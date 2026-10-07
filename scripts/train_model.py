"""
============================================================
 MODEL EĞİTİM PIPELINE'I (Training Pipeline Script)
============================================================
 Bu script, veri çekme -> temizleme -> özellik hazırlama ->
 model eğitimi -> değerlendirme -> kaydetme adımlarını
 sıralı olarak çalıştıran ana pipeline'dır.

 Bir pipeline, veri biliminde birbirine bağlı adımların
 belirli bir sırayla çalıştırılması anlamına gelir.

 Kullanım:
   python -m scripts.train_model
============================================================
"""

import sys
from src.database import fetch_all_data, test_connection
from src.features import clean_data, prepare_features, split_data
from src.model import train_model, evaluate_model, print_feature_importance, save_model
from src.config import FEATURE_COLUMNS


def run_training_pipeline():
    """
    Tam eğitim pipeline'ını çalıştırır.

    Adımlar:
      1. Veritabanı bağlantı kontrolü
      2. Veritabanından veri çekme
      3. Veri temizleme
      4. Özellik ve hedef ayırma
      5. Eğitim/test bölme
      6. Model eğitimi
      7. Model değerlendirme
      8. Özellik önem sıralaması
      9. Modeli kaydetme
    """
    print("\n" + "#" * 60)
    print("#  ENERJİ TÜKETİM TAHMİN MODELİ - EĞİTİM PIPELINE'I")
    print("#" * 60)

    # ----- ADIM 1: Veritabanı Bağlantı Kontrolü -----
    print("\n>> Adım 1/7: Veritabanı bağlantısı kontrol ediliyor...")
    if not test_connection():
        print("  [HATA] Veritabanına bağlanılamadı. İşlem durduruluyor.")
        sys.exit(1)

    # ----- ADIM 2: Veri Çekme -----
    print("\n>> Adım 2/7: Veritabanından veriler çekiliyor...")
    df = fetch_all_data()

    if len(df) == 0:
        print("  [HATA] Veritabanında veri bulunamadı!")
        print("  Önce veri ekleyin: python -m scripts.seed_database")
        sys.exit(1)

    # ----- ADIM 3: Veri Temizleme -----
    print("\n>> Adım 3/7: Veriler temizleniyor...")
    df = clean_data(df)

    # ----- ADIM 4: Özellik Hazırlama -----
    print("\n>> Adım 4/7: Özellikler hazırlanıyor...")
    X, y = prepare_features(df)

    # ----- ADIM 5: Eğitim/Test Bölme -----
    print("\n>> Adım 5/7: Veri bölünüyor...")
    X_train, X_test, y_train, y_test = split_data(X, y)

    # ----- ADIM 6: Model Eğitimi -----
    print("\n>> Adım 6/7: Model eğitiliyor...")
    model = train_model(X_train, y_train)

    # ----- ADIM 7: Değerlendirme & Kaydetme -----
    print("\n>> Adım 7/7: Model değerlendiriliyor ve kaydediliyor...")
    metrics = evaluate_model(model, X_test, y_test)
    print_feature_importance(model, FEATURE_COLUMNS)
    save_model(model)

    # ----- ÖZET -----
    print("\n" + "#" * 60)
    print("#  EĞİTİM TAMAMLANDI!")
    print("#" * 60)
    print(f"#  MAE  : {metrics['mae']} kWh")
    print(f"#  RMSE : {metrics['rmse']} kWh")
    print(f"#  R²   : {metrics['r2']}")
    print("#")
    print("#  Sonraki adım: API'yi başlatın")
    print("#    uvicorn src.api:app --reload")
    print("#" * 60)

    return metrics


if __name__ == "__main__":
    run_training_pipeline()
