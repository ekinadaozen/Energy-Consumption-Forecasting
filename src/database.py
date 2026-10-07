"""
============================================================
 VERİTABANI MODÜLÜ (Database Module)
============================================================
 Bu modül, PostgreSQL veritabanı ile tüm etkileşimleri
 yönetir:
   - Veritabanı bağlantısı kurma
   - Veri ekleme (INSERT)
   - Veri çekme (SELECT) -> Pandas DataFrame olarak
   - Bağlantı testi

 SQLAlchemy engine ve Pandas pd.read_sql kullanılır.
============================================================
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from src.config import DATABASE_URL


# ---------------------------------------------------------
# Veritabanı Engine Oluştur
# ---------------------------------------------------------
# SQLAlchemy engine, veritabanı bağlantı havuzunu (connection
# pool) yönetir. Her sorgu için yeni bağlantı açıp kapatmak
# yerine, havuzdan bağlantı alıp geri verir.
def get_engine():
    """
    SQLAlchemy veritabanı engine'i oluşturur ve döndürür.

    Returns:
        Engine: SQLAlchemy veritabanı bağlantı motoru
    """
    engine = create_engine(DATABASE_URL, echo=False)
    return engine


# ---------------------------------------------------------
# Bağlantı Testi
# ---------------------------------------------------------
def test_connection():
    """
    Veritabanı bağlantısını test eder.
    Başarılıysa True, başarısızsa False döndürür.

    Returns:
        bool: Bağlantı başarılı mı?
    """
    try:
        engine = get_engine()
        # Basit bir sorgu ile bağlantıyı test et
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Veritabanı bağlantısı başarılı!")
        return True
    except OperationalError as e:
        print(f"[HATA] Veritabanına bağlanılamadı: {e}")
        print("  -> Docker container'ın çalıştığından emin olun:")
        print("     docker-compose up -d")
        return False


# ---------------------------------------------------------
# Veri Çekme (Tüm Veriler)
# ---------------------------------------------------------
def fetch_all_data():
    """
    energy_consumption tablosundaki tüm verileri çeker
    ve Pandas DataFrame olarak döndürür.

    Bu fonksiyon pd.read_sql() kullanır; bu sayede SQL
    sorgu sonucu doğrudan DataFrame'e dönüştürülür.

    Returns:
        pd.DataFrame: Tüm enerji tüketim verileri
    """
    engine = get_engine()

    # SQL sorgusu: Tüm kayıtları tarihe göre sıralı getir
    query = """
        SELECT
            date,
            temperature,
            humidity,
            wind_speed,
            cloud_cover,
            day_of_week,
            month,
            is_weekend,
            energy_kwh
        FROM energy_consumption
        ORDER BY date ASC;
    """

    # pd.read_sql ile veritabanından DataFrame'e aktar
    # Bu, veri biliminde çok sık kullanılan bir kalıptır
    df = pd.read_sql(query, engine)

    print(f"[OK] Veritabanından {len(df)} satır veri çekildi.")
    return df


# ---------------------------------------------------------
# Veri Ekleme (DataFrame -> Veritabanı)
# ---------------------------------------------------------
def insert_dataframe(df, table_name="energy_consumption"):
    """
    Bir Pandas DataFrame'i veritabanına toplu olarak ekler.

    Pandas'ın to_sql() metodu, DataFrame'deki her satırı
    otomatik olarak SQL INSERT ifadesine dönüştürür.

    Args:
        df (pd.DataFrame): Eklenecek veri
        table_name (str): Hedef tablo adı
    """
    engine = get_engine()

    # if_exists='append' -> Tabloya ekleme yapar (üzerine yazmaz)
    # index=False -> DataFrame indeksini sütun olarak eklemez
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        method="multi",  # Toplu ekleme (daha hızlı)
    )

    print(f"[OK] {len(df)} satır '{table_name}' tablosuna eklendi.")


# ---------------------------------------------------------
# Kayıt Sayısını Kontrol Et
# ---------------------------------------------------------
def get_record_count(table_name="energy_consumption"):
    """
    Belirtilen tablodaki toplam kayıt sayısını döndürür.

    Args:
        table_name (str): Tablo adı

    Returns:
        int: Kayıt sayısı
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
    return count
