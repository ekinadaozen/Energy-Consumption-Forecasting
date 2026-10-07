"""
============================================================
 API SERVİS MODÜLÜ (FastAPI Application)
============================================================
 Bu modül, eğitilmiş makine öğrenmesi modelini bir REST API
 servisi olarak dışarıya açar.

 Endpoint'ler:
   GET  /           -> API durum kontrolü (health check)
   GET  /info       -> Model ve özellik bilgileri
   POST /predict    -> Enerji tüketim tahmini

 Kullanım:
   uvicorn src.api:app --reload

 Örnek İstek (curl):
   curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"temperature": 25.0, "humidity": 60.0, \
          "wind_speed": 15.0, "cloud_cover": 40.0, \
          "day_of_week": 2, "month": 7, "is_weekend": 0}'
============================================================
"""

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import FEATURE_COLUMNS, MODEL_PATH
from src.model import load_model


# ---------------------------------------------------------
# FastAPI Uygulamasını Oluştur
# ---------------------------------------------------------
# title ve description parametreleri otomatik oluşturulan
# API dokümantasyonunda (Swagger UI) görünür.
app = FastAPI(
    title="Enerji Tüketim Tahmin API'si",
    description=(
        "Hava durumu verilerini ve zamansal özellikleri kullanarak "
        "günlük elektrik tüketimini tahmin eden API servisi.\n\n"
        "Swagger UI: http://localhost:8000/docs"
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# Modeli Yükle (Uygulama Başlangıcında)
# ---------------------------------------------------------
# Modeli global değişkende tutuyoruz çünkü her istek için
# modeli diskten tekrar yüklemek yavaş olurdu.
# Uygulama başladığında bir kez yüklenir.
model = None


@app.on_event("startup")
async def startup_event():
    """
    Uygulama başladığında çalışır.
    Eğitilmiş modeli diskten yükler.
    """
    global model
    try:
        model = load_model()
        print("\n  [OK] API başlatıldı, model yüklendi.")
    except FileNotFoundError as e:
        print(f"\n  [UYARI] {e}")
        print("  API başlatıldı ancak model yüklenmedi.")
        print("  Önce modeli eğitin: python -m scripts.train_model")


# ---------------------------------------------------------
# İstek/Yanıt Veri Modelleri (Pydantic)
# ---------------------------------------------------------
# Pydantic modelleri, gelen JSON verisinin otomatik olarak
# doğrulanmasını (validation) sağlar.

class PredictionRequest(BaseModel):
    """
    Tahmin isteği için beklenen JSON yapısı.

    Her alan için:
      - Tip kontrolü otomatik yapılır
      - Field() ile açıklama ve örnek değer verilir
      - ge/le ile min/max sınırları belirlenir
    """
    temperature: float = Field(
        ...,
        description="Ortalama sıcaklık (°C)",
        ge=-30, le=50,
        examples=[25.0]
    )
    humidity: float = Field(
        ...,
        description="Nem oranı (%)",
        ge=0, le=100,
        examples=[60.0]
    )
    wind_speed: float = Field(
        ...,
        description="Rüzgar hızı (km/s)",
        ge=0, le=200,
        examples=[15.0]
    )
    cloud_cover: float = Field(
        ...,
        description="Bulutluluk oranı (%)",
        ge=0, le=100,
        examples=[40.0]
    )
    day_of_week: int = Field(
        ...,
        description="Haftanın günü (0=Pazartesi, 6=Pazar)",
        ge=0, le=6,
        examples=[2]
    )
    month: int = Field(
        ...,
        description="Ay (1=Ocak, 12=Aralık)",
        ge=1, le=12,
        examples=[7]
    )
    is_weekend: int = Field(
        ...,
        description="Hafta sonu mu? (0=Hayır, 1=Evet)",
        ge=0, le=1,
        examples=[0]
    )


class PredictionResponse(BaseModel):
    """
    Tahmin yanıtı için JSON yapısı.
    """
    predicted_energy_kwh: float = Field(
        ..., description="Tahmini günlük enerji tüketimi (kWh)"
    )
    unit: str = Field(default="kWh", description="Ölçü birimi")
    model_path: str = Field(..., description="Kullanılan model dosyası")
    input_features: dict = Field(..., description="Girdi olarak alınan özellikler")


# ---------------------------------------------------------
# Endpoint: Ana Sayfa (Health Check)
# ---------------------------------------------------------
@app.get("/", tags=["Genel"])
async def root():
    """
    API'nin çalışıp çalışmadığını kontrol eden endpoint.
    Bu tür endpoint'lere 'health check' denir.
    """
    return {
        "status": "active",
        "message": "Enerji Tüketim Tahmin API'si çalışıyor!",
        "docs_url": "/docs",
        "model_loaded": model is not None,
    }


# ---------------------------------------------------------
# Endpoint: Model Bilgisi
# ---------------------------------------------------------
@app.get("/info", tags=["Genel"])
async def model_info():
    """
    Model ve özellik bilgilerini döndürür.
    Hangi özelliklerin beklendiğini gösterir.
    """
    return {
        "model_type": "GradientBoostingRegressor",
        "feature_columns": FEATURE_COLUMNS,
        "target": "energy_kwh (Günlük enerji tüketimi)",
        "model_path": MODEL_PATH,
        "model_loaded": model is not None,
    }


# ---------------------------------------------------------
# Endpoint: Tahmin (Prediction)
# ---------------------------------------------------------
@app.post("/predict", response_model=PredictionResponse, tags=["Tahmin"])
async def predict(request: PredictionRequest):
    """
    Hava durumu parametrelerini alır ve enerji tüketim
    tahmini döndürür.

    İşleyiş:
      1. JSON isteği Pydantic ile doğrulanır
      2. Girdi değerleri numpy array'e dönüştürülür
      3. Model tahmin yapar
      4. Sonuç JSON olarak döndürülür
    """
    # Model yüklü mü kontrol et
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model henüz yüklenmedi. "
                "Önce modeli eğitin: python -m scripts.train_model"
            ),
        )

    # Girdi değerlerini sözlükten al ve sıralı şekilde diziye çevir
    # Modelin beklediği sıra, FEATURE_COLUMNS'daki sıradır
    input_dict = request.model_dump()
    input_array = np.array([
        [input_dict[col] for col in FEATURE_COLUMNS]
    ])

    # Model ile tahmin yap
    prediction = model.predict(input_array)[0]

    # Negatif tahmin mantıksızdır (enerji >= 0 olmalı)
    prediction = max(0, prediction)

    # Yanıt oluştur ve döndür
    return PredictionResponse(
        predicted_energy_kwh=round(prediction, 2),
        unit="kWh",
        model_path=MODEL_PATH,
        input_features=input_dict,
    )
