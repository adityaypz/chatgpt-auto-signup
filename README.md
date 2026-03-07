# ChatGPT Auto Signup Bot 🤖

> **Learning Project** — Untuk belajar browser automation tingkat tinggi dengan Python + `nodriver` (undetected Chrome).
>
> **© 2026 [adityaypz](https://github.com/adityaypz)** — Licensed under [MIT](LICENSE)

## ⚠️ Disclaimer

Project ini dibuat **hanya untuk tujuan edukasi dan testing**.
Jangan digunakan untuk aktivitas yang melanggar *Terms of Service*.

---

## 🛠️ Requirements

- Python 3.10+
- OS Chrome Browser yang terinstal di sistem operasi Anda (Windows / macOS / Linux)

## 📦 Setup

```bash
# 1. Masuk ke folder project
cd chatgpt-auto-signup

# 2. Install dependencies
pip install -r requirements.txt
```

## 🚀 Cara Pakai

```bash
# Basic (Akan ditanya secara interaktif berapa akun)
python main.py

# Headless mode (Berjalan senyap tanpa GUI browser)
python main.py --headless

# Menggunakan daftar proxy
python main.py --proxy

# (Advanced) Jalankan langsung tanpa pertanyaan interaktif
python main.py --count 5 --proxy --delay 10
```

### CLI Options

| Argument | Default | Keterangan |
|---|---|---|
| `--count`, `-c` | 1 | Jumlah akun yang dibuat (Bisa disetel interaktif) |
| `--headless` | `False` | Jalankan di background (sembunyi). Hati-hati, lebih mudah dideteksi Cloudflare! |
| `--proxy` | `False` | Aktifkan proxy dari file `proxies.txt` |
| `--delay`, `-d` | 5 | Jeda delay antar signup akun (detik) |

## 🌐 Proxy Setup (`nodriver` Rules)

1. Edit file `proxies.txt`
2. Tambahkan proxy (1 per baris):

```text
123.456.789.0:8080
```

> **🚨 CATATAN PENTING PROXY:** 
> Automasi _Anti-Detect_ ini menggunakan **nodriver**, yang memanfaatkan Chrome murni. Chromium native **TIDAK MENDUKUNG** injeksi Username dan Password proxy melalui _command line argument_. 
> Jika Anda membeli *Residential Proxy* / *Premium Proxy*, Anda **WAJIB menggunakan otentikasi IP Whitelist**. Daftarkan IP Publik VPS/Komputer Anda di dashboard penyedia Proxy agar Anda cukup memasukkan `ip:port` saja di file `proxies.txt` tanpa di-prompt untuk login.

3. Jalankan dengan flag `--proxy`:
```bash
python main.py --proxy
```

## 📁 Struktur Project

```text
chatgpt-auto-signup/
├── main.py              # Entry point + CLI Interaktif
├── config.py            # Tempat setup utama (headless, delay, dll)
├── temp_email.py        # Pengacak email (Mail.tm, dll)
├── proxy_manager.py     # Proxy rotation
├── signup_bot.py        # Core automation (nodriver) & JS Injections
├── proxies.txt          # Daftar IP proxy
├── requirements.txt     # Dependencies
├── results.txt          # Tempat akun tersimpan (auto-generated)
└── README.md            # (file ini)
```

## ⚡ Troubleshoots & Catatan Penting

- 📱 **Phone Verification ("Log in or sign up")**  
  Jika di akhir pendaftaran ChatGPT tiba-tiba menyuruh Anda memasukkan nomor HP, itu berarti skor reputasi **IP Anda dianggap buruk oleh sistem OpenAI**, meskipun kita sudah berhasil melewati Cloudflare Turnstile.
  **Solusi:** Gunakan IP Mobile, restart router Anda untuk mendapat IP dinamik baru, atau beli *Residential Proxy* berkualitas tinggi.
  
- 🤖 **Bypass React Form Lock**  
  Script ini menggunakan injeksi JavaScript intensif berbasis `KeyboardEvent` untuk mengecoh sistem validasi Frontend (React) OpenAI pada form *Birthday*, *Name*, dan *Submit buttons*.

- 🛡️ **Headless vs Headed**  
  Mode `headed` (browser terlihat) memiliki skor kepercayaan sistem robot jauh lebih baik dibandingkan `--headless`. Saat *headless*, Cloudflare sangat rewel.

## 🧠 Apa yang Dipelajari

- Bypass Deteksi Bot Tingkat Dewa (Cloudflare Turnstile) menggunakan **nodriver**.
- *JavaScript DOM Manipulation* & React Form Bypassing via Automation.
- Async/await HTTP requests di Python.
- CLI argument parsing interaktif.
