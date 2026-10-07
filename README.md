# ⚡ Enerji Tüketim Tahmini (Energy Consumption Forecasting)

> Geçmiş hava durumu verilerini ve zamansal özellikleri kullanarak günlük elektrik tüketimini tahmin eden uçtan uca (end-to-end) makine öğrenmesi projesi.

---

## 📋 Proje Özeti

Bu proje, bir **junior yazılımcının** veri bilimi ve makine öğrenmesi servis geliştirmeyi öğrenmesi için tasarlanmış profesyonel standartlarda bir iskelet projedir.

### Projenin 3 Katmanı

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| 🗄️ **SQL Entegrasyonu** | PostgreSQL + Docker | Veriler CSV'den değil, veritabanından `pd.read_sql` ile çekilir |
| 📊 **Model Değerlendirme** | Scikit-Learn Metrics | MAE, RMSE, R² skorları hesaplanır ve yorumlanır |
| 🌐 **API Servisi** | FastAPI | `/predict` endpoint'i ile anlık tahmin yapılır |

---

## 🗂️ Proje Yapısı

```
Energy Consumption Forecasting/
│
├── docker-compose.yml        # PostgreSQL container tanımı
├── .env                      # Ortam değişkenleri (DB şifreleri vb.)
├── .gitignore                # Git'e dahil edilmeyecek dosyalar
├── requirements.txt          # Python bağımlılıkları
├── main.py                   # Ana giriş noktası (tek komutla çalıştır)
│
├── init_db/
│   └── init.sql              # Veritabanı tablo oluşturma scripti
│
├── src/                      # Ana kaynak kod paketi
│   ├── __init__.py
│   ├── config.py             # Merkezi yapılandırma ayarları
│   ├── database.py           # Veritabanı işlemleri (bağlantı, CRUD)
│   ├── features.py           # Özellik mühendisliği (temizleme, bölme)
│   ├── model.py              # Model eğitimi, değerlendirme, kaydetme
│   └── api.py                # FastAPI uygulaması (/predict endpoint)
│
├── scripts/                  # Yardımcı scriptler
│   ├── __init__.py
│   ├── seed_database.py      # Sentetik veri üretimi ve DB'ye ekleme
│   └── train_model.py        # Eğitim pipeline'ı
│
└── models/                   # Eğitilmiş model dosyaları (.joblib)
    └── .gitkeep
```

---

## 🚀 Hızlı Başlangıç

### Ön Gereksinimler

- **Python 3.10+**
- **Docker Desktop** (PostgreSQL için)
- **pip** (Python paket yöneticisi)

### Adım Adım Kurulum

```bash
# 1. Proje dizinine gir
cd "Energy Consumption Forecasting"

# 2. Sanal ortam oluştur (önerilir)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# 3. Bağımlılıkları kur
pip install -r requirements.txt

# 4. PostgreSQL'i Docker ile başlat
docker-compose up -d

# 5. Veritabanına sentetik veri ekle
python -m scripts.seed_database

# 6. Modeli eğit ve değerlendir
python -m scripts.train_model

# 7. API'yi başlat
uvicorn src.api:app --reload
```

> 💡 **Tek komutla hepsini çalıştır:** `python main.py`

---

## 📊 Model Değerlendirme Çıktısı (Örnek)

```
==================================================
  MODEL DEĞERLENDİRME SONUÇLARI
==================================================
  MAE  (Ortalama Mutlak Hata)     : 25.43 kWh
  RMSE (Kök Ort. Kare Hata)       : 32.18 kWh
  R²   (Belirlilik Katsayısı)      : 0.9512
--------------------------------------------------
  YORUM: Mükemmel! Model verideki değişkenliğin
         %95.1'ini açıklıyor.
==================================================
```

---

## 🌐 API Kullanımı

### Swagger UI (Otomatik Dokümantasyon)

API başlatıldıktan sonra: **http://localhost:8000/docs**

### Örnek İstek (curl)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 25.0,
    "humidity": 60.0,
    "wind_speed": 15.0,
    "cloud_cover": 40.0,
    "day_of_week": 2,
    "month": 7,
    "is_weekend": 0
  }'
```

### Örnek Yanıt

```json
{
  "predicted_energy_kwh": 687.45,
  "unit": "kWh",
  "model_path": "models/energy_model.joblib",
  "input_features": {
    "temperature": 25.0,
    "humidity": 60.0,
    "wind_speed": 15.0,
    "cloud_cover": 40.0,
    "day_of_week": 2,
    "month": 7,
    "is_weekend": 0
  }
}
```

### PowerShell ile İstek

```powershell
$body = @{
    temperature  = 25.0
    humidity     = 60.0
    wind_speed   = 15.0
    cloud_cover  = 40.0
    day_of_week  = 2
    month        = 7
    is_weekend   = 0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method Post -Body $body -ContentType "application/json"
```

---

## 🛠️ Kullanılan Teknolojiler

| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| Python | 3.10+ | Ana programlama dili |
| Pandas | 2.0+ | Veri manipülasyonu, `pd.read_sql` |
| Scikit-Learn | 1.3+ | GradientBoostingRegressor modeli |
| PostgreSQL | 16 | Veri depolama (Docker ile) |
| SQLAlchemy | 2.0+ | ORM / Veritabanı bağlantı yönetimi |
| FastAPI | 0.100+ | REST API servisi |
| Pydantic | 2.0+ | Veri doğrulama (request/response) |
| Docker | - | PostgreSQL container yönetimi |
| joblib | 1.3+ | Model serileştirme (kaydetme/yükleme) |

---

## 📖 Öğrenme Notları

### Pipeline Akışı

```
PostgreSQL (Docker)
      │
      ▼
  pd.read_sql()    ← Veri Çekme
      │
      ▼
  clean_data()     ← Veri Temizleme
      │
      ▼
  prepare_features() ← X (girdi) ve y (hedef) ayırma
      │
      ▼
  split_data()     ← %80 eğitim, %20 test
      │
      ▼
  train_model()    ← GradientBoostingRegressor
      │
      ▼
  evaluate_model() ← MAE, RMSE, R² hesapla
      │
      ▼
  save_model()     ← .joblib olarak kaydet
      │
      ▼
  FastAPI /predict ← API ile tahmin sun
```

---

## 📝 Lisans

Bu proje eğitim amaçlıdır. Serbestçe kullanabilir ve değiştirebilirsiniz.
