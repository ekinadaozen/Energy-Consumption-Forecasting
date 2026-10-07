"""
============================================================
 GERÇEK VERİ YÜKLEME VE ENTEGRASYON SCRİPTİ
 (Real Data Ingestion & Integration Script)
============================================================
 Bu script:
   1. EPİAŞ'tan indirilen gerçek elektrik tüketim dosyasını
      (.csv veya .xlsx) okur ve günlük toplamlara dönüştürür.
   2. Open-Meteo Historical Archive API'sini kullanarak
      aynı tarih aralığındaki GERÇEK hava durumu verilerini
      (sıcaklık, nem, rüzgar hızı, bulutluluk) çeker.
   3. İki veri setini tarihe göre birleştirir ve özellikleri üretir.
   4. PostgreSQL veritabanına aktarır.
   5. Modeli bu gerçek verilerle baştan eğitir.

 Kullanım:
   python -m scripts.load_real_data
   python -m scripts.load_real_data --file "data/GercekZamanliTuketim.csv"
============================================================
"""

import os
import sys
import glob
import argparse
import urllib.request
import json
from datetime import datetime
import pandas as pd
import numpy as np

from src.database import get_connection, insert_dataframe
from src.config import RANDOM_STATE
from sqlalchemy import text


# ---------------------------------------------------------
# Türkiye Koordinatları (Varsayılan: İstanbul)
# ---------------------------------------------------------
DEFAULT_LAT = 41.0082
DEFAULT_LON = 28.9784
DEFAULT_CITY = "İstanbul"


def find_data_file(custom_path=None):
    """
    Kullanıcının sağladığı dosyayı veya data/ klasöründeki
    CSV/Excel dosyalarını otomatik bulur.
    """
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # data/ klasöründe ve ana dizinde ara
    patterns = [
        "data/*.csv",
        "data/*.xlsx",
        "data/*.xls",
        "*.csv",
        "*.xlsx",
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        for f in files:
            # Sistem veya bağımlılık dosyalarını atla
            basename = os.path.basename(f).lower()
            if basename not in ["requirements.txt", ".gitignore"]:
                return f

    return None


def parse_epias_file(file_path):
    """
    EPİAŞ'tan indirilen CSV veya Excel dosyasını ayrıştırır.
    Saatlik verileri günlük toplamlara dönüştürür.
    """
    print(f"\n[1/4] EPİAŞ dosyası okunuyor: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        # CSV ayraç kontrolü (; veya ,)
        try:
            df = pd.read_csv(file_path, sep=";")
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",")
        except Exception:
            df = pd.read_csv(file_path, sep=",")

    print(f"  Bulunan sütunlar: {list(df.columns)}")

    # Sütun isimlerini normalize et
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        if "tarih" in c_clean or "date" in c_clean:
            col_map[col] = "date"
        elif "tüketim" in c_clean or "tuketim" in c_clean or "consumption" in c_clean:
            col_map[col] = "consumption"

    if "date" not in col_map.values() or "consumption" not in col_map.values():
        raise ValueError(
            "EPİAŞ dosyasında 'Tarih' ve 'Tüketim' sütunları bulunamadı!\n"
            f"Mevcut sütunlar: {list(df.columns)}"
        )

    df = df.rename(columns=col_map)
    df = df[["date", "consumption"]].dropna()

    # Sayı formatı temizleme (Türkçe format: 35.123,45 -> 35123.45)
    def clean_number(val):
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        # Eğer hem nokta hem virgül varsa
        if "." in s and "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)

    df["consumption"] = df["consumption"].apply(clean_number)

    # Tarih formatını parse et
    df["date"] = pd.to_datetime(df["date"], dayfirst=True).dt.date

    # Günlük toplama dönüştür (Saatlik verileri topla)
    daily_df = df.groupby("date")["consumption"].sum().reset_index()
    daily_df.rename(columns={"consumption": "energy_kwh"}, inplace=True)

    print(f"  Toplam {len(daily_df)} günlük tüketim verisi işlendi.")
    print(f"  Tarih aralığı: {daily_df['date'].min()} -> {daily_df['date'].max()}")
    print(f"  Ortalama günlük tüketim: {daily_df['energy_kwh'].mean():,.1f} MWh/kWh")

    return daily_df


def fetch_real_weather(start_date, end_date, lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """
    Open-Meteo Historical Archive API ile belirtilen tarih aralığı
    için gerçek hava durumu verilerini çeker.
    """
    print(f"\n[2/4] Open-Meteo'dan gerçek hava durumu çekiliyor ({DEFAULT_CITY})...")
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={start_str}&end_date={end_str}&"
        f"daily=temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_max,cloud_cover_mean&"
        f"timezone=auto"
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "EnergyForecastingProject/1.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    daily = data.get("daily", {})
    weather_df = pd.DataFrame({
        "date": pd.to_datetime(daily["time"]).dt.date,
        "temperature": daily["temperature_2m_mean"],
        "humidity": daily["relative_humidity_2m_mean"],
        "wind_speed": daily["wind_speed_10m_max"],
        "cloud_cover": daily["cloud_cover_mean"],
    })

    print(f"  {len(weather_df)} günlük gerçek hava durumu verisi başarıyla çekildi!")
    return weather_df


def merge_and_enrich(consumption_df, weather_df):
    """
    Tüketim ve hava durumu verilerini birleştirir,
    takvim ve mevsimsel özellikleri üretir.
    """
    print("\n[3/4] Veriler birleştiriliyor ve özellik mühendisliği uygulanıyor...")
    merged = pd.merge(consumption_df, weather_df, on="date", how="inner")

    # Eksik değerleri temizle
    merged = merged.dropna().copy()

    # Zamansal özellikler
    dates = pd.to_datetime(merged["date"])
    merged["day_of_week"] = dates.dt.weekday
    merged["month"] = dates.dt.month
    merged["is_weekend"] = merged["day_of_week"] >= 5

    # Yuvarlamalar
    merged["temperature"] = merged["temperature"].round(1)
    merged["humidity"] = merged["humidity"].round(1)
    merged["wind_speed"] = merged["wind_speed"].round(1)
    merged["cloud_cover"] = merged["cloud_cover"].round(1)
    merged["energy_kwh"] = merged["energy_kwh"].round(2)

    # Sıralama
    merged = merged.sort_values("date").reset_index(drop=True)

    print(f"  Eğitime hazır birleştirilmiş veri sayısı: {len(merged)} gün")
    return merged


def save_to_database(df):
    """
    Veritabanındaki eski verileri temizler ve yeni gerçek verileri yazar.
    """
    print("\n[4/4] PostgreSQL veritabanı güncelleniyor...")
    engine = get_connection()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE energy_consumption RESTART IDENTITY;"))

    insert_dataframe(df)
    print("  [OK] Gerçek veriler PostgreSQL'e başarıyla kaydedildi!")


def main():
    parser = argparse.ArgumentParser(description="Gerçek Veri Yükleme Aracı")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="EPİAŞ CSV veya Excel dosya yolu",
    )
    args = parser.parse_args()

    file_path = find_data_file(args.file)

    if not file_path:
        print("\n" + "=" * 60)
        print("  [BİLGİ] EPİAŞ Veri Dosyası Bulunamadı!")
        print("=" * 60)
        print("  Lütfen EPİAŞ Şeffaflık Platformu'ndan indirdiğiniz CSV")
        print("  veya Excel dosyasını projenin 'data/' klasörüne koyun.")
        print("  Örnek: data/GercekZamanliTuketim.csv")
        print("=" * 60)
        sys.exit(1)

    # 1. EPİAŞ Dosyasını Oku
    consumption_df = parse_epias_file(file_path)

    # 2. Gerçek Hava Durumu Çek
    start_date = consumption_df["date"].min()
    end_date = consumption_df["date"].max()
    weather_df = fetch_real_weather(start_date, end_date)

    # 3. Birleştir ve Zenginleştir
    final_df = merge_and_enrich(consumption_df, weather_df)

    # 4. Veritabanına Yaz
    save_to_database(final_df)

    # 5. Modeli Eğit
    print("\n" + "=" * 60)
    print("  YENİ MODEL EĞİTİMİ (Gerçek Veriler ile)")
    print("=" * 60)
    from scripts.train_model import run_training_pipeline
    run_training_pipeline()

    print("\n" + "=" * 60)
    print("  [TEBRİKLER] Gerçek verilerle eğitim tamamlandı!")
    print("  FastAPI servisi artık gerçek verilere göre tahmin üretiyor.")
    print("=" * 60)


if __name__ == "__main__":
    main()
