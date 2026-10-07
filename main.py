"""
============================================================
 ANA GİRİŞ NOKTASI (Main Entry Point)
============================================================
 Bu dosya, projenin ana giriş noktasıdır ve tüm pipeline'ı
 tek komutla çalıştırmanızı sağlar.

 Kullanım:
   python main.py             -> Tam pipeline (seed + train + api)
   python main.py --seed      -> Sadece veri tohumlama
   python main.py --train     -> Sadece model eğitimi
   python main.py --api       -> Sadece API başlatma
============================================================
"""

import sys
import argparse


def main():
    """
    Komut satırı argümanlarını ayrıştırır ve ilgili
    işlemi çalıştırır.
    """
    # ---------------------------------------------------------
    # Argüman Ayrıştırıcı Oluştur
    # ---------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Enerji Tüketim Tahmin Sistemi",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Veritabanına sentetik veri ekle",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Modeli eğit ve değerlendir",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="FastAPI servisini başlat",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="EPİAŞ ve Open-Meteo gerçek verilerini yükle ve modeli eğit",
    )

    args = parser.parse_args()

    # Gerçek veri akışı istendiyse
    if args.real:
        from scripts.load_real_data import run_real_data_pipeline
        run_real_data_pipeline()
        return

    # Hiçbir argüman verilmediyse hepsini çalıştır
    run_all = not (args.seed or args.train or args.api)

    # ---------------------------------------------------------
    # Veri Tohumlama
    # ---------------------------------------------------------
    if args.seed or run_all:
        print("\n" + "=" * 60)
        print("  ADIM 1: Veritabanı Tohumlama")
        print("=" * 60)
        from scripts.seed_database import generate_synthetic_data
        from src.database import (
            test_connection,
            get_record_count,
            insert_dataframe,
        )

        if test_connection():
            count = get_record_count()
            if count == 0:
                df = generate_synthetic_data()
                insert_dataframe(df)
                print("  [OK] Tohumlama tamamlandı!")
            else:
                print(f"  [BİLGİ] Veritabanında zaten {count} kayıt var.")
        else:
            print("  [HATA] Veritabanına bağlanılamadı!")
            if run_all:
                sys.exit(1)

    # ---------------------------------------------------------
    # Model Eğitimi
    # ---------------------------------------------------------
    if args.train or run_all:
        print("\n" + "=" * 60)
        print("  ADIM 2: Model Eğitimi")
        print("=" * 60)
        from scripts.train_model import run_training_pipeline

        run_training_pipeline()

    # ---------------------------------------------------------
    # API Başlatma
    # ---------------------------------------------------------
    if args.api or run_all:
        print("\n" + "=" * 60)
        print("  ADIM 3: API Servisi Başlatılıyor")
        print("=" * 60)
        import uvicorn
        from src.config import API_HOST, API_PORT

        print(f"  API Adresi: http://localhost:{API_PORT}")
        print(f"  Swagger UI: http://localhost:{API_PORT}/docs")
        print("  Durdurmak için: Ctrl+C")
        uvicorn.run("src.api:app", host=API_HOST, port=API_PORT, reload=True)


if __name__ == "__main__":
    main()
