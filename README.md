# 📡 RADAR COPET v3.0 - Trading Dashboard

**Dashboard Trading Real-Time berbasis MetaTrader 5**  
*Developed by DELAWA Inc.*

---

## 📋 Daftar Isi
- [Fitur Utama](#fitur-utama)
- [Persyaratan Sistem](#persyaratan-sistem)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Cara Membaca Indikator](#cara-membaca-indikator)
- [Penjelasan Sinyal](#penjelasan-sinyal)
- [Troubleshooting](#troubleshooting)

---

##  Fitur Utama

✅ **Multi-Timeframe Analysis** (M1, M5, M15, H1, D1, W1)  
✅ **Dual Bollinger Bands** (BB Cepat 20 & BB Trend 150)  
✅ **Power Strength Matrix** untuk deteksi kekuatan tren  
✅ **Real-time Signal** untuk scalping (M1) dan trend monitoring (M5)  
✅ **Candle Timer** untuk menghitung sisa waktu candle  
✅ **Daily Pivot Tracking** (jarak dari Open harian dalam pips)  
✅ **Sound Alert** saat ada sinyal BUY/SELL  
✅ **Responsive Design** - bisa diakses via PC atau HP  

---

## 💻 Persyaratan Sistem

### **Wajib:**
- **Operating System:** Windows 10/11 (MetaTrader 5 Python API hanya support Windows)
- **Python:** Versi 3.8 - 3.11 (64-bit)
- **MetaTrader 5:** Terminal terinstal dan berjalan
- **Akun Trading:** Aktif (contoh: Akun Cent HFM)

### **Koneksi:**
- PC dan HP harus dalam **satu jaringan WiFi/LAN** (untuk akses via HP)

---

## 📦 Instalasi

### **1. Clone atau Download Project**
```bash
mkdir radar-copet
cd radar-copet
```

Pastikan struktur folder seperti ini:
```
radar-copet/
├── main.py
└── templates/
    └── index.html
```

### **2. Buat Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Untuk Windows
# source venv/bin/activate  # Untuk Linux/Mac
```

### **3. Install Dependencies**
```bash
pip install Flask MetaTrader5 pandas numpy
```

Atau buat file `requirements.txt`:
```
Flask==3.0.0
MetaTrader5==5.0.45
pandas==2.1.0
numpy==1.24.0
```

Lalu install:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Konfigurasi

### **Edit Simbol Trading**
Buka file `main.py`, sesuaikan simbol dengan broker Anda:

```python
SYMBOL_LIST = ["XAUUSDc", "EURUSDc", "GBPUSDc", "USDJPYc", "AUDUSDc"]
```

**Catatan:** 
- Untuk akun **standard**: `XAUUSD`, `EURUSD`
- Untuk akun **cent**: `XAUUSDc`, `EURUSDc` (ada huruf 'c' di belakang)

### **Port Server**
Default port: **5050**  
Ubah di baris terakhir `main.py` jika perlu:
```python
app.run(debug=True, host='0.0.0.0', port=5050)
```

---

## 🚀 Cara Menjalankan

### **1. Pastikan MetaTrader 5:**
- ✅ Sudah terinstal
- ✅ Sudah login ke akun trading
- ✅ Terminal dalam keadaan **terbuka dan online**

### **2. Jalankan Aplikasi**
```bash
# Aktifkan virtual environment
venv\Scripts\activate

# Jalankan server
python main.py
```

### **3. Akses Dashboard**

**Dari PC yang sama:**
```
http://localhost:5050
```

**Dari HP/PC lain (satu jaringan):**
1. Cari IP Address PC server:
   - Windows: Buka CMD → ketik `ipconfig` → lihat **IPv4 Address**
   - Contoh: `192.168.1.100`

2. Akses dari browser HP:
   ```
   http://192.168.1.100:5050
   ```

---

## 📊 Cara Membaca Indikator

### **1. TIMEFRAME M1 (Scalping Entry)**

Digunakan untuk **entry point** scalping dengan sinyal cepat.

**Komponen:**
- **M1 SIGNAL**: Sinyal utama (BUY/SELL/WAIT)
- **BB1 Cepat (20)**: Bollinger Bands periode 20 (deviasi 1.3)
  - **U** = Upper Band
  - **M** = Middle Band (MA 20)
  - **L** = Lower Band
- **BB2 Trend (150)**: Bollinger Bands periode 150 untuk trend utama
- **MA Fast / Slow**: Moving Average 10 dan 20
- **RSI (14)**: Relative Strength Index
- **ATR**: Average True Range (volatilitas)
- **Sisa Candle**: Waktu tersisa sebelum candle M1 close

### **2. TIMEFRAME M5 (Trend Monitor)**

Digunakan untuk **konfirmasi trend** yang lebih stabil.

Komponen sama dengan M1, namun lebih reliable untuk melihat arah trend jangka pendek.

### **3. Power Strength Matrix**

Menunjukkan kekuatan tren BUY/SELL dalam persentase di semua timeframe:

| Timeframe | Buy Power | Sell Power | Interpretasi |
|-----------|-----------|------------|--------------|
| **M1** | 80% | 20% | Strong Buy (scalping) |
| **M5** | 70% | 30% | Buy (trend pendek) |
| **M15** | 60% | 40% | Moderate Buy |
| **H1** | 50% | 50% | Neutral |
| **D1** | 30% | 70% | Sell (trend harian) |
| **W1** | 40% | 60% | Slight Sell (mingguan) |

**Cara Hitung:**
- Close > MA10 → +30 poin Buy
- Close > MA20 → +30 poin Buy  
- RSI > 55 → +40 poin Buy
- RSI < 45 → +40 poin Sell
- RSI 45-55 → +20 poin masing-masing

---

## 🎯 Penjelasan Sinyal

### **SINYAL BUY**

**Kondisi Pemicu:**
1. **Mid Crossover (BB1 > BB2 Mid)**  
   - BB1 Middle band crossover di atas BB2 Middle band
   - **Kekuatan**: ⭐⭐⭐ (Sedang)

2. **Reversal (BB1 Mid > BB2 Low)**  
   - BB1 Middle band menembus atas BB2 Lower band
   - **Kekuatan**: ⭐⭐⭐⭐ (Strong)

3. **Upper Break (BB1 Up > BB2 Mid)**  
   - BB1 Upper band menembus BB2 Middle band
   - **Kekuatan**: ⭐⭐⭐⭐⭐ (Very Strong)

4. **Breakout: Close > BB1 Upper**  
   - Harga close di atas BB1 Upper band
   - **Kekuatan**: ⭐⭐⭐⭐ (Strong - momentum)

### **SINYAL SELL**

**Kondisi Pemicu:**
1. **Mid Crossover (BB1 < BB2 Mid)**  
   - BB1 Middle band crossover di bawah BB2 Middle band
   - **Kekuatan**: ⭐⭐⭐ (Sedang)

2. **Reversal (BB1 Mid < BB2 Low)**  
   - BB1 Middle band menembus bawah BB2 Lower band
   - **Kekuatan**: ⭐⭐⭐⭐ (Strong)

3. **Lower Break (BB1 Low < BB2 Mid)**  
   - BB1 Lower band menembus BB2 Middle band
   - **Kekuatan**: ⭐⭐⭐⭐⭐ (Very Strong)

4. **Breakout: Close < BB1 Lower**  
   - Harga close di bawah BB1 Lower band
   - **Kekuatan**: ⭐⭐⭐⭐ (Strong - momentum)

### **SINYAL WAIT**

- Tidak ada kondisi crossover atau breakout yang terpenuhi
- Market dalam kondisi sideways/konsolidasi
- **Saran**: Jangan entry, tunggu sinyal yang lebih jelas

---

## 📈 Strategi Trading

### **Untuk Scalping (M1):**

**Entry BUY ketika:**
1. M1 Signal = **BUY**
2. M5 Signal = **BUY** atau **WAIT** (bukan SELL)
3. Buy Power M1 > 60%
4. Spread < 30 points (untuk Gold)

**Entry SELL ketika:**
1. M1 Signal = **SELL**
2. M5 Signal = **SELL** atau **WAIT** (bukan BUY)
3. Sell Power M1 > 60%
4. Spread < 30 points (untuk Gold)

**Exit/Take Profit:**
- Target: 10-20 pips (Gold), 5-10 pips (Forex)
- Stop Loss: 5-10 pips di bawah BB1 Lower (untuk BUY) atau di atas BB1 Upper (untuk SELL)
- Atau exit ketika M1 Signal berubah menjadi WAIT atau berlawanan

### **Untuk Trend Following (M5/H1):**

**Konfirmasi Trend Kuat:**
- Jika **Buy Power M5 + H1 > 120%** → Trend BUY kuat
- Jika **Sell Power M5 + H1 > 120%** → Trend SELL kuat
- Entry di M1 searah dengan trend M5/H1

---

## 🔧 Troubleshooting

### **Error: "Gagal koneksi ke MT5"**
**Solusi:**
1. Pastikan terminal MetaTrader 5 **terbuka**
2. Pastikan sudah **login** ke akun trading
3. Restart MT5 dan jalankan ulang `python main.py`

### **Error: "Simbol Tidak Ditemukan"**
**Solusi:**
1. Cek nama simbol di MT5 (Market Watch)
2. Sesuaikan `SYMBOL_LIST` di `main.py`
3. Untuk akun cent, biasanya ada akhiran 'c' (XAUUSD**c**)

### **Error: "Gagal memproses indikator"**
**Solusi:**
1. Market mungkin baru buka (data historis belum cukup)
2. Tunggu beberapa menit hingga data 155+ candle terkumpul
3. Pastikan koneksi internet stabil

### **Dashboard tidak bisa diakses dari HP**
**Solusi:**
1. Pastikan PC dan HP dalam **satu WiFi**
2. Cek **Windows Firewall** → izinkan Python/port 5050
3. Pastikan IP Address PC benar (cek dengan `ipconfig`)

### **Sinyal tidak update/ stuck**
**Solusi:**
1. Refresh browser (F5)
2. Cek apakah MT5 masih online
3. Restart aplikasi Flask (Ctrl+C → jalankan ulang)

---

## ⚠️ Disclaimer

**PERINGATAN PENTING:**

1. Aplikasi ini adalah **alat bantu analisis**, bukan jaminan profit
2. Trading forex dan gold memiliki **risiko tinggi**
3. Selalu gunakan **money management** yang baik
4. Jangan investasikan uang yang Anda tidak sanggup kehilangan
5. Backtest strategi sebelum digunakan dengan uang asli
6. Developer **tidak bertanggung jawab** atas kerugian trading

---

## 📞 Support

Untuk pertanyaan atau bug report:
- Email: support@delawainc.com (contoh)
- GitHub Issues: [link repo]

---

## 📄 License

© 2024 DELAWA Inc.  
All rights reserved.

---

**Happy Trading! 📊💰**  
*Gunakan dengan bijak dan selalu disiplin!*
