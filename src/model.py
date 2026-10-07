"""
============================================================
 MODEL MODÜLÜ (Machine Learning Model Module)
============================================================
 Bu modül, makine öğrenmesi modelinin eğitiminden
 değerlendirmesine, kaydedilmesinden yüklenmesine kadar
 tüm işlemleri yönetir.

 Kullanılan Algoritma: Gradient Boosting Regressor
   - Neden? Tabular (tablo) verilerde en iyi performans
     gösteren algoritmalardan biridir.
   - Karar ağaçlarını sıralı olarak eğitir; her yeni ağaç
     önceki ağacın hatalarını düzeltmeye çalışır.

 Metrikler:
   - MAE  (Mean Absolute Error)  : Ortalama mutlak hata
   - RMSE (Root Mean Squared Error): Kök ortalama kare hata
   - R²   (R-Squared)            : Belirlilik katsayısı
============================================================
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config import MODEL_PATH, RANDOM_STATE


# ---------------------------------------------------------
# Model Eğitimi
# ---------------------------------------------------------
def train_model(X_train, y_train):
    """
    Gradient Boosting Regressor modelini eğitir.

    Hiperparametreler:
      - n_estimators  : Kaç tane karar ağacı kullanılacak
      - max_depth     : Her ağacın maksimum derinliği
      - learning_rate : Öğrenme hızı (küçük = daha yavaş ama daha iyi)
      - subsample     : Her ağaç için kullanılacak veri yüzdesi

    Args:
        X_train: Eğitim özellikleri
        y_train: Eğitim hedef değerleri

    Returns:
        model: Eğitilmiş model nesnesi
    """
    print("\n" + "=" * 50)
    print("  MODEL EĞİTİMİ")
    print("=" * 50)

    # Gradient Boosting Regressor modelini oluştur
    model = GradientBoostingRegressor(
        n_estimators=200,     # 200 adet karar ağacı
        max_depth=5,          # Her ağaç maksimum 5 seviye derin
        learning_rate=0.1,    # Öğrenme hızı
        subsample=0.8,        # Her ağaç verinin %80'ini kullanır
        random_state=RANDOM_STATE,
    )

    # Modeli eğit (fit)
    # Model, X_train ve y_train arasındaki ilişkiyi öğrenir
    print("  Model eğitiliyor...")
    model.fit(X_train, y_train)
    print("  [OK] Model eğitimi tamamlandı!")

    return model


# ---------------------------------------------------------
# Model Değerlendirme
# ---------------------------------------------------------
def evaluate_model(model, X_test, y_test):
    """
    Eğitilmiş modeli test verisi üzerinde değerlendirir
    ve 3 temel metriği hesaplar.

    Metrik Açıklamaları:
    -------------------
    MAE (Mean Absolute Error):
      Tahmin ile gerçek değer arasındaki ortalama mutlak fark.
      Örneğin MAE=50 ise, model ortalama 50 kWh sapıyor demektir.
      Düşük = daha iyi.

    RMSE (Root Mean Squared Error):
      MAE'ye benzer ama büyük hataları daha çok cezalandırır.
      Düşük = daha iyi.

    R² (R-Squared / Belirlilik Katsayısı):
      Modelin verideki değişkenliğin ne kadarını açıkladığını gösterir.
      0.0 = Model hiçbir şey açıklamıyor
      1.0 = Model mükemmel tahmin yapıyor
      0.85+ genelde iyi kabul edilir.

    Args:
        model: Eğitilmiş model
        X_test: Test özellikleri
        y_test: Test hedef değerleri

    Returns:
        dict: Metrik adı -> değer sözlüğü
    """
    # Test verisi üzerinde tahmin yap
    y_pred = model.predict(X_test)

    # Metrikleri hesapla
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Sonuçları ekrana yazdır
    print("\n" + "=" * 50)
    print("  MODEL DEĞERLENDİRME SONUÇLARI")
    print("=" * 50)
    print(f"  MAE  (Ortalama Mutlak Hata)     : {mae:.2f} kWh")
    print(f"  RMSE (Kök Ort. Kare Hata)       : {rmse:.2f} kWh")
    print(f"  R²   (Belirlilik Katsayısı)      : {r2:.4f}")
    print("-" * 50)

    # R² skoruna göre yorum yap
    if r2 >= 0.90:
        print("  YORUM: Mükemmel! Model verideki değişkenliğin")
        print(f"         %{r2*100:.1f}'ini açıklıyor.")
    elif r2 >= 0.75:
        print("  YORUM: İyi performans. Model güvenilir tahminler")
        print("         üretiyor, ancak iyileştirme alanı var.")
    elif r2 >= 0.50:
        print("  YORUM: Orta düzey performans. Daha fazla özellik")
        print("         veya farklı algoritma denenebilir.")
    else:
        print("  YORUM: Düşük performans. Veri kalitesi ve özellik")
        print("         mühendisliği gözden geçirilmeli.")

    print("=" * 50)

    # Metrikleri sözlük olarak döndür
    metrics = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
    }
    return metrics


# ---------------------------------------------------------
# Özellik Önem Sıralaması
# ---------------------------------------------------------
def print_feature_importance(model, feature_names):
    """
    Modelin hangi özelliklere ne kadar önem verdiğini gösterir.

    Bu bilgi, hangi değişkenlerin enerji tüketimini en çok
    etkilediğini anlamamıza yardımcı olur.

    Args:
        model: Eğitilmiş model
        feature_names: Özellik adları listesi
    """
    importances = model.feature_importances_

    # Önem sırasına göre sırala (en önemli en üstte)
    sorted_idx = np.argsort(importances)[::-1]

    print("\n" + "=" * 50)
    print("  ÖZELLİK ÖNEM SIRALAMASI")
    print("=" * 50)

    for rank, idx in enumerate(sorted_idx, 1):
        bar = "█" * int(importances[idx] * 40)
        print(f"  {rank}. {feature_names[idx]:15s} : {importances[idx]:.4f} {bar}")

    print("=" * 50)


# ---------------------------------------------------------
# Modeli Kaydet
# ---------------------------------------------------------
def save_model(model):
    """
    Eğitilmiş modeli diske kaydeder (serialize).

    joblib, scikit-learn modellerini kaydetmek için
    önerilen kütüphanedir. pickle'dan daha hızlıdır
    ve numpy array'leri daha verimli saklar.

    Args:
        model: Kaydedilecek model nesnesi
    """
    # Klasör yoksa oluştur
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    # Modeli kaydet
    joblib.dump(model, MODEL_PATH)
    print(f"\n  [OK] Model kaydedildi: {MODEL_PATH}")


# ---------------------------------------------------------
# Modeli Yükle
# ---------------------------------------------------------
def load_model():
    """
    Daha önce kaydedilmiş modeli diskten yükler.

    Bu fonksiyon API servisinde kullanılır; sunucu
    başlatıldığında model bir kez yüklenir ve her
    tahmin isteğinde tekrar kullanılır.

    Returns:
        model: Yüklenmiş model nesnesi

    Raises:
        FileNotFoundError: Model dosyası bulunamazsa
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model dosyası bulunamadı: {MODEL_PATH}\n"
            "  Önce modeli eğitin: python -m scripts.train_model"
        )

    model = joblib.load(MODEL_PATH)
    print(f"  [OK] Model yüklendi: {MODEL_PATH}")
    return model
