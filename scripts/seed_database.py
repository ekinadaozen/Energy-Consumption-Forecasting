"""
============================================================
 VERİTABANI TOHUMLAMA SCRİPTİ (Database Seeding Script)
============================================================
 Bu script, PostgreSQL veritabanına gerçekçi sentetik
 (yapay) enerji tüketim verileri ekler.

 Neden sentetik veri?
   Gerçek dünya verileri her zaman hazır olmayabilir.
   Sentetik veri ile modelin çalışma mantığını test
   edebilir ve proje iskeleti oluşturabiliriz.

 Veri Mantığı:
   - Sıcaklık mevsimsel olarak değişir (kış soğuk, yaz sıcak)
   - Enerji tüketimi sıcaklıkla ters orantılı (ısıtma ihtiyacı)
   - Hafta sonları tüketim biraz farklıdır
   - Rüzgar, nem ve bulutluluk rastgele gürültü ekler

 Kullanım:
   python -m scripts.seed_database
============================================================
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

from src.database import insert_dataframe, test_connection, get_record_count
from src.config import RANDOM_STATE


# ---------------------------------------------------------
# Sentetik Veri Üretici
# ---------------------------------------------------------
def generate_synthetic_data(start_date="2022-01-01", num_days=730):
    """
    Gerçekçi sentetik enerji tüketim verileri üretir.

    2 yıllık (730 gün) günlük veri üretir.
    Her gün için sıcaklık, nem, rüzgar hızı, bulutluluk,
    ve bunlara bağlı enerji tüketimi hesaplanır.

    Args:
        start_date (str): Başlangıç tarihi (YYYY-MM-DD)
        num_days (int): Kaç günlük veri üretilecek

    Returns:
        pd.DataFrame: Üretilen veri seti
    """
    np.random.seed(RANDOM_STATE)

    print("\n" + "=" * 50)
    print("  SENTETİK VERİ ÜRETİMİ")
    print("=" * 50)
    print(f"  Başlangıç tarihi: {start_date}")
    print(f"  Gün sayısı      : {num_days}")

    # Tarih dizisi oluştur
    start = pd.to_datetime(start_date)
    dates = [start + timedelta(days=i) for i in range(num_days)]

    records = []
    for d in dates:
        # --- Zamansal Özellikler ---
        day_of_week = d.weekday()       # 0=Pzt, 6=Paz
        month = d.month                 # 1-12
        is_weekend = day_of_week >= 5   # Cumartesi veya Pazar

        # --- Mevsimsel Sıcaklık Hesaplama ---
        # Sinüs fonksiyonu ile mevsimsel değişim simüle edilir
        # Ocak'ta (gün ~0) en soğuk, Temmuz'da (gün ~180) en sıcak
        day_of_year = d.timetuple().tm_yday
        seasonal_factor = np.sin(2 * np.pi * (day_of_year - 80) / 365)
        # Türkiye iklimi: Ortalama 15°C, yaz 35°C, kış -5°C
        temperature = 15 + 15 * seasonal_factor + np.random.normal(0, 3)

        # --- Hava Durumu Özellikleri ---
        humidity = np.clip(60 + 20 * np.random.randn(), 10, 100)
        wind_speed = np.clip(np.random.exponential(12), 0, 80)
        cloud_cover = np.clip(50 + 25 * np.random.randn(), 0, 100)

        # --- Enerji Tüketimi Hesaplama ---
        # Gerçekçi bir formül: Sıcaklıktan sapma enerji tüketimini artırır
        # (hem çok soğuk hem çok sıcak = yüksek tüketim)
        comfort_temp = 20  # Konfor sıcaklığı
        temp_deviation = abs(temperature - comfort_temp)

        # Temel tüketim + sıcaklık etkisi + gürültü
        base_consumption = 500          # Baz tüketim (kWh)
        temp_effect = 12 * temp_deviation  # Sıcaklık sapmasının etkisi
        wind_effect = 1.5 * wind_speed     # Rüzgar etkisi
        humidity_effect = 0.8 * humidity   # Nem etkisi
        cloud_effect = 0.5 * cloud_cover   # Bulutluluk etkisi

        # Hafta sonu etkisi (daha az tüketim)
        weekend_effect = -50 if is_weekend else 0

        # Mevsimsel ek (kışın ısıtma, yazın soğutma)
        seasonal_extra = 80 * abs(seasonal_factor)

        # Toplam tüketim
        energy = (
            base_consumption
            + temp_effect
            + wind_effect
            + humidity_effect
            + cloud_effect
            + weekend_effect
            + seasonal_extra
            + np.random.normal(0, 30)  # Rastgele gürültü
        )

        # Negatif tüketim olamaz
        energy = max(energy, 100)

        records.append({
            "date": d.date(),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "wind_speed": round(wind_speed, 1),
            "cloud_cover": round(cloud_cover, 1),
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,
            "energy_kwh": round(energy, 1),
        })

    df = pd.DataFrame(records)

    print(f"\n  [OK] {len(df)} günlük sentetik veri üretildi.")
    print(f"  Enerji tüketim aralığı: {df['energy_kwh'].min():.0f} - {df['energy_kwh'].max():.0f} kWh")
    print(f"  Ortalama tüketim      : {df['energy_kwh'].mean():.0f} kWh")
    print(f"  Sıcaklık aralığı      : {df['temperature'].min():.1f}°C - {df['temperature'].max():.1f}°C")

    return df


# ---------------------------------------------------------
# Ana Çalıştırma Bloğu
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  VERİTABANI TOHUMLAMA İŞLEMİ")
    print("#" * 60)

    # 1. Veritabanı bağlantısını test et
    if not test_connection():
        print("\n  [HATA] İşlem iptal edildi.")
        exit(1)

    # 2. Mevcut kayıt sayısını kontrol et
    count = get_record_count()
    if count > 0:
        print(f"\n  [BİLGİ] Veritabanında zaten {count} kayıt var.")
        print("  Yeni veri eklenmeyecek. Temiz başlangıç için:")
        print("    docker-compose down -v && docker-compose up -d")
        exit(0)

    # 3. Sentetik veri üret
    df = generate_synthetic_data()

    # 4. Veriyi veritabanına ekle
    insert_dataframe(df)

    # 5. Doğrulama
    final_count = get_record_count()
    print(f"\n  [OK] Veritabanındaki toplam kayıt: {final_count}")
    print("  Tohumlama işlemi başarıyla tamamlandı!")
    print("#" * 60)
