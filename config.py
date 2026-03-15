"""
Konfigurasi untuk ChatGPT Auto Signup Bot
"""

# ═══════════════════════════════════════════
# URL & Endpoints
# ═══════════════════════════════════════════
SIGNUP_URL = "https://chatgpt.com/"
AUTH_URL = "https://auth0.openai.com/"

# ═══════════════════════════════════════════
# Browser Settings
# ═══════════════════════════════════════════
HEADLESS = False                # Default: tampilkan browser (lebih stealth)
SLOW_MO = 50              # Delay antar aksi (ms), human delays ditambah di code
BROWSER_TIMEOUT = 60000   # Timeout per aksi (ms)
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800

# ═══════════════════════════════════════════
# Proxy Settings
# ═══════════════════════════════════════════
USE_PROXY = False               # Set True untuk aktifkan proxy
PROXY_FILE = "proxies.txt"      # Path ke file daftar proxy
PROXY_VALIDATE = True           # Test proxy sebelum dipakai
PROXY_TIMEOUT = 10              # Timeout validasi proxy (detik)

# ═══════════════════════════════════════════
# 2Captcha Settings
# ═══════════════════════════════════════════
CAPTCHA_API_KEY = "7434dca5501025b89e3675c7fc0bd3bc"
CAPTCHA_ENABLED = True                # Auto-solve CAPTCHA via 2Captcha
CAPTCHA_POLL_INTERVAL = 5             # Cek hasil setiap X detik
CAPTCHA_MAX_WAIT = 120                # Timeout tunggu solusi (detik)

# ═══════════════════════════════════════════
# Temp Email Settings
# ═══════════════════════════════════════════
MAX_EMAIL_RETRIES = 3           # Max retry signup jika email domain diblock
BLOCKED_EMAIL_DOMAINS = []      # Domain yang diketahui diblock (auto-updated)
EMAIL_POLL_INTERVAL = 5         # Cek inbox setiap X detik
EMAIL_POLL_TIMEOUT = 120        # Timeout tunggu email (detik)

# ═══════════════════════════════════════════
# Account Generation
# ═══════════════════════════════════════════
PASSWORD_LENGTH = 16            # Panjang password yang di-generate
MIN_AGE = 20                    # Umur minimum untuk DOB
MAX_AGE = 40                    # Umur maksimum untuk DOB

# ═══════════════════════════════════════════
# Retry & Delay
# ═══════════════════════════════════════════
MAX_RETRIES = 3                 # Maksimum retry per step
"""
Konfigurasi untuk ChatGPT Auto Signup Bot
"""

# ═══════════════════════════════════════════
# URL & Endpoints
# ═══════════════════════════════════════════
SIGNUP_URL = "https://chatgpt.com/"
AUTH_URL = "https://auth0.openai.com/"

# ═══════════════════════════════════════════
# Browser Settings
# ═══════════════════════════════════════════
HEADLESS = False                # Default: tampilkan browser (lebih stealth)
SLOW_MO = 50              # Delay antar aksi (ms), human delays ditambah di code
BROWSER_TIMEOUT = 60000   # Timeout per aksi (ms)
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800

# ═══════════════════════════════════════════
# Proxy Settings
# ═══════════════════════════════════════════
USE_PROXY = False               # Set True untuk aktifkan proxy
PROXY_FILE = "proxies.txt"      # Path ke file daftar proxy
PROXY_VALIDATE = True           # Test proxy sebelum dipakai
PROXY_TIMEOUT = 10              # Timeout validasi proxy (detik)

# ═══════════════════════════════════════════
# 2Captcha Settings
# ═══════════════════════════════════════════
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_KEY"
CAPTCHA_ENABLED = True                # Auto-solve CAPTCHA via 2Captcha
CAPTCHA_POLL_INTERVAL = 5             # Cek hasil setiap X detik
CAPTCHA_MAX_WAIT = 120                # Timeout tunggu solusi (detik)

# ═══════════════════════════════════════════
# Temp Email Settings
# ═══════════════════════════════════════════
MAX_EMAIL_RETRIES = 3           # Max retry signup jika email domain diblock
BLOCKED_EMAIL_DOMAINS = []      # Domain yang diketahui diblock (auto-updated)
EMAIL_POLL_INTERVAL = 5         # Cek inbox setiap X detik
EMAIL_POLL_TIMEOUT = 120        # Timeout tunggu email (detik)

# ═══════════════════════════════════════════
# Account Generation
# ═══════════════════════════════════════════
PASSWORD_LENGTH = 16            # Panjang password yang di-generate
MIN_AGE = 20                    # Umur minimum untuk DOB
MAX_AGE = 40                    # Umur maksimum untuk DOB

# ═══════════════════════════════════════════
# Retry & Delay
# ═══════════════════════════════════════════
MAX_RETRIES = 3                 # Maksimum retry per step
RETRY_DELAY = 2                 # Delay antar retry (detik)
ACTION_DELAY = 1                # Delay antar aksi utama (detik)

# ═══════════════════════════════════════════
# Output
# ═══════════════════════════════════════════
LOG_FILE = "results.txt"        # File untuk simpan hasil
SAVE_CREDENTIALS = True         # Simpan email:password ke file
GMAIL_APP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"