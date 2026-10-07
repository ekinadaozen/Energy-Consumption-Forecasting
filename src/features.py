"""
============================================================
 ÖZELLİK MÜHENDİSLİĞİ MODÜLÜ (Feature Engineering Module)
============================================================
 Bu modül, ham verileri makine öğrenmesi modeline beslemeden
 önce hazırlama ve dönüştürme işlemlerini yapar.

 İçerik:
   - Veri temizleme (eksik değer kontrolü)
   - Özellik seçimi
   - Eğitim/test seti bölme
   - Veri ön-işleme (scaling, encoding vb.)
============================================================
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from src.config import FEATURE_COLUMNS, TARGET_COLUMN, TEST_SIZE, RANDOM_STATE


# ---------------------------------------------------------
# Veri Temizleme ve Ön-Kontrol
# ---------------------------------------------------------
def clean_data(df):
    """
    Veriyi temizler ve kalite kontrolü yapar.

    Adımlar:
      1. Eksik değer (NaN) kontrolü
      2. Sayısal olmayan değerlerin tespiti
      3. is_weekend sütununu integer'a çevirme

    Args:
        df (pd.DataFrame): Ham veri

    Returns:
        pd.DataFrame: Temizlenmiş veri
    """
    print("\n" + "=" * 50)
    print("  VERİ TEMİZLEME RAPORU")
    print("=" * 50)

    # Kaç satır ve sütun var?
    print(f"  Toplam satır sayısı : {len(df)}")
    print(f"  Toplam sütun sayısı: {len(df.columns)}")

    # Eksik değerleri kontrol et
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\n  [UYARI] Eksik değerler bulundu:")
        print(missing[missing > 0])
        # Eksik değerleri sütun ortalaması ile doldur
        # Bu, basit ama etkili bir stratejidir
        df = df.fillna(df.mean(numeric_only=True))
        print("  -> Eksik değerler ortalama ile dolduruldu.")
    else:
        print("  [OK] Eksik değer bulunamadı.")

    # is_weekend sütununu boolean'dan integer'a çevir
    # Makine öğrenmesi modelleri sayısal değerlerle çalışır
    if "is_weekend" in df.columns:
        df["is_weekend"] = df["is_weekend"].astype(int)

    print("=" * 50)
    return df


# ---------------------------------------------------------
# Özellik ve Hedef Değişken Ayırma
# ---------------------------------------------------------
def prepare_features(df):
    """
    DataFrame'den özellik matrisini (X) ve hedef vektörünü (y)
    ayırır.

    Makine öğrenmesinde:
      X = Girdi özellikleri (bağımsız değişkenler)
      y = Tahmin edilecek hedef (bağımlı değişken)

    Args:
        df (pd.DataFrame): Temizlenmiş veri

    Returns:
        tuple: (X, y) -> (pd.DataFrame, pd.Series)
    """
    # Sadece config'de tanımlı özellik sütunlarını al
    X = df[FEATURE_COLUMNS].copy()

    # Hedef değişkeni ayır
    y = df[TARGET_COLUMN].copy()

    print(f"\n  Özellik matrisi (X) boyutu: {X.shape}")
    print(f"  Hedef vektör (y) boyutu   : {y.shape}")
    print(f"  Kullanılan özellikler     : {FEATURE_COLUMNS}")

    return X, y


# ---------------------------------------------------------
# Eğitim / Test Bölme
# ---------------------------------------------------------
def split_data(X, y):
    """
    Veriyi eğitim ve test setlerine böler.

    Neden bölüyoruz?
      Modelin daha önce görmediği veriler üzerindeki
      performansını ölçmek için. Bu, modelin gerçek
      dünyada ne kadar iyi çalışacağının göstergesidir.

    Args:
        X (pd.DataFrame): Özellik matrisi
        y (pd.Series): Hedef değişken

    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,       # %20 test, %80 eğitim
        random_state=RANDOM_STATE  # Tekrarlanabilirlik için
    )

    print(f"\n  Eğitim seti boyutu: {X_train.shape[0]} satır")
    print(f"  Test seti boyutu  : {X_test.shape[0]} satır")
    print(f"  Bölme oranı       : %{int(TEST_SIZE*100)} test")

    return X_train, X_test, y_train, y_test
