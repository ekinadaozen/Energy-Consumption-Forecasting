-- ============================================================
-- Veritabanı Başlangıç Scripti (Initialization SQL)
-- ============================================================
-- Bu script, Docker container ilk oluşturulduğunda otomatik
-- olarak çalışır ve gerekli tabloları oluşturur.
--
-- Tablo: energy_consumption
--   Günlük enerji tüketim verilerini ve ilgili hava durumu
--   bilgilerini saklar.
-- ============================================================

-- ---------------------------------------------------------
-- Ana Tablo: energy_consumption
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_consumption (
    id              SERIAL PRIMARY KEY,           -- Otomatik artan birincil anahtar
    date            DATE NOT NULL UNIQUE,         -- Tarih (her gün için tek kayıt)
    temperature     FLOAT NOT NULL,               -- Ortalama sıcaklık (°C)
    humidity        FLOAT NOT NULL,               -- Nem oranı (%)
    wind_speed      FLOAT NOT NULL,               -- Rüzgar hızı (km/s)
    cloud_cover     FLOAT NOT NULL,               -- Bulutluluk oranı (%)
    day_of_week     INTEGER NOT NULL,             -- Haftanın günü (0=Pzt, 6=Paz)
    month           INTEGER NOT NULL,             -- Ay (1-12)
    is_weekend      BOOLEAN NOT NULL DEFAULT FALSE, -- Hafta sonu mu?
    energy_kwh      FLOAT NOT NULL,               -- Günlük enerji tüketimi (kWh)
    created_at      TIMESTAMP DEFAULT NOW()       -- Kayıt oluşturulma zamanı
);

-- ---------------------------------------------------------
-- Performans için indeks oluştur
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_energy_date ON energy_consumption(date);
CREATE INDEX IF NOT EXISTS idx_energy_month ON energy_consumption(month);

-- Bilgi mesajı
DO $$
BEGIN
    RAISE NOTICE 'energy_consumption tablosu başarıyla oluşturuldu!';
END $$;
