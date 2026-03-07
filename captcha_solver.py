"""
Captcha Solver — menggunakan 2Captcha API
Solve Cloudflare Turnstile CAPTCHA secara otomatis
"""

import time
import requests
from colorama import Fore, Style
import config


class CaptchaSolver:
    """Solve CAPTCHA via 2Captcha API"""

    API_URL = "https://2captcha.com"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.CAPTCHA_API_KEY
        self.session = requests.Session()

    def get_balance(self) -> float:
        """Cek saldo 2Captcha"""
        try:
            response = self.session.get(
                f"{self.API_URL}/res.php",
                params={
                    "key": self.api_key,
                    "action": "getbalance",
                    "json": 1,
                },
                timeout=10,
            )
            data = response.json()
            if data.get("status") == 1:
                balance = float(data.get("request", 0))
                print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Saldo 2Captcha: ${balance:.4f}")
                return balance
            else:
                print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} {data.get('request')}")
                return 0
        except Exception as e:
            print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} Gagal cek saldo: {e}")
            return 0

    def solve_turnstile(self, site_key: str, page_url: str) -> str | None:
        """
        Solve Cloudflare Turnstile CAPTCHA.
        Return token atau None jika gagal.
        """
        print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Mengirim Turnstile ke 2Captcha...")
        print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Site key: {site_key[:20]}...")

        try:
            # Step 1: Submit CAPTCHA
            response = self.session.post(
                f"{self.API_URL}/in.php",
                data={
                    "key": self.api_key,
                    "method": "turnstile",
                    "sitekey": site_key,
                    "pageurl": page_url,
                    "json": 1,
                },
                timeout=15,
            )
            data = response.json()

            if data.get("status") != 1:
                print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} Submit gagal: {data.get('request')}")
                return None

            captcha_id = data.get("request")
            print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Captcha ID: {captcha_id}")
            print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Menunggu solusi... (biasanya 10-30 detik)")

            # Step 2: Poll for result
            for attempt in range(config.CAPTCHA_MAX_WAIT // config.CAPTCHA_POLL_INTERVAL):
                time.sleep(config.CAPTCHA_POLL_INTERVAL)

                result = self.session.get(
                    f"{self.API_URL}/res.php",
                    params={
                        "key": self.api_key,
                        "action": "get",
                        "id": captcha_id,
                        "json": 1,
                    },
                    timeout=10,
                )
                result_data = result.json()

                if result_data.get("status") == 1:
                    token = result_data.get("request")
                    print(f"{Fore.GREEN}[CAPTCHA]{Style.RESET_ALL} ✓ Solved! Token: {token[:50]}...")
                    return token

                if result_data.get("request") == "CAPCHA_NOT_READY":
                    elapsed = (attempt + 1) * config.CAPTCHA_POLL_INTERVAL
                    print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Masih solving... ({elapsed}s)")
                    continue

                # Error
                print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} {result_data.get('request')}")
                return None

            print(f"{Fore.RED}[CAPTCHA]{Style.RESET_ALL} Timeout! CAPTCHA tidak terselesaikan dalam {config.CAPTCHA_MAX_WAIT}s")
            return None

        except Exception as e:
            print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} Error: {e}")
            return None

    def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str | None:
        """
        Solve reCAPTCHA v2 (backup, kalau ChatGPT switch dari Turnstile).
        """
        print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Mengirim reCAPTCHA v2 ke 2Captcha...")

        try:
            response = self.session.post(
                f"{self.API_URL}/in.php",
                data={
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1,
                },
                timeout=15,
            )
            data = response.json()

            if data.get("status") != 1:
                print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} Submit gagal: {data.get('request')}")
                return None

            captcha_id = data.get("request")
            print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Captcha ID: {captcha_id}")
            print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Menunggu solusi reCAPTCHA... (bisa 30-60 detik)")

            for attempt in range(config.CAPTCHA_MAX_WAIT // config.CAPTCHA_POLL_INTERVAL):
                time.sleep(config.CAPTCHA_POLL_INTERVAL)

                result = self.session.get(
                    f"{self.API_URL}/res.php",
                    params={
                        "key": self.api_key,
                        "action": "get",
                        "id": captcha_id,
                        "json": 1,
                    },
                    timeout=10,
                )
                result_data = result.json()

                if result_data.get("status") == 1:
                    token = result_data.get("request")
                    print(f"{Fore.GREEN}[CAPTCHA]{Style.RESET_ALL} ✓ reCAPTCHA solved!")
                    return token

                if result_data.get("request") == "CAPCHA_NOT_READY":
                    elapsed = (attempt + 1) * config.CAPTCHA_POLL_INTERVAL
                    print(f"{Fore.CYAN}[CAPTCHA]{Style.RESET_ALL} Masih solving... ({elapsed}s)")
                    continue

                print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} {result_data.get('request')}")
                return None

            return None

        except Exception as e:
            print(f"{Fore.RED}[CAPTCHA ERROR]{Style.RESET_ALL} Error: {e}")
            return None


if __name__ == "__main__":
    from colorama import init
    init()

    solver = CaptchaSolver()
    balance = solver.get_balance()
    print(f"Saldo: ${balance:.4f}")
