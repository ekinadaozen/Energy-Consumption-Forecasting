"""
============================================================
 YAPILANDIRMA MODÜLÜ (Configuration Module)
============================================================
 Bu modül, projenin tüm yapılandırma ayarlarını merkezi
 bir noktada toplar. Veritabanı bağlantı bilgileri, model
 parametreleri ve dosya yolları burada tanımlanır.

 .env dosyasındaki ortam değişkenleri otomatik olarak
 yüklenir ve kullanılır.
============================================================
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------
# .env dosyasından ortam değişkenlerini yükle
# ---------------------------------------------------------
load_dotenv()


# ---------------------------------------------------------
# Veritabanı Yapılandırması
# ---------------------------------------------------------
# PostgreSQL bağlantı bilgilerini ortam değişkenlerinden al.
# Eğer ortam değişkeni tanımlı değilse, varsayılan değerleri kullan.
DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "energy_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "energy_pass_123"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "energy_forecasting_db"),
}

# SQLAlchemy bağlantı dizesi (connection string)
# Format: postgresql://kullanıcı:şifre@host:port/veritabanı
DATABASE_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)


# ---------------------------------------------------------
# Model Yapılandırması
# ---------------------------------------------------------
# Eğitilen modelin kaydedileceği dosya yolu
MODEL_PATH = os.getenv("MODEL_PATH", "models/energy_model.joblib")

# Modelin kullanacağı özellik (feature) sütunları
# Bu liste, veritabanındaki hangi sütunların model girdisi
# olarak kullanılacağını belirler.
FEATURE_COLUMNS = [
    "temperature",    # Sıcaklık (°C)
    "humidity",       # Nem oranı (%)
    "wind_speed",     # Rüzgar hızı (km/s)
    "cloud_cover",    # Bulutluluk (%)
    "day_of_week",    # Haftanın günü (0-6)
    "month",          # Ay (1-12)
    "is_weekend",     # Hafta sonu mu? (0/1)
]

# Hedef (target) değişken: Tahmin etmek istediğimiz değer
TARGET_COLUMN = "energy_kwh"

# Eğitim-test bölme oranı
# 0.2 = Verinin %20'si test, %80'i eğitim için kullanılır
TEST_SIZE = 0.2

# Rastgelelik tohumu (reproducibility için)
# Aynı sonuçları tekrar elde edebilmemizi sağlar
RANDOM_STATE = 42


# ---------------------------------------------------------
# API Yapılandırması
# ---------------------------------------------------------
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
