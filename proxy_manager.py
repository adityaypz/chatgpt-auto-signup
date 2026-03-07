"""
Proxy Manager — load, validasi, dan rotasi proxy
"""

import requests
import re
from urllib.parse import urlparse
from colorama import Fore, Style
import config


class ProxyManager:
    """Manage proxy list dengan rotasi round-robin"""

    def __init__(self, proxy_file: str = None):
        self.proxy_file = proxy_file or config.PROXY_FILE
        self.proxies: list[dict] = []
        self.current_index = 0
        self._load_proxies()

    def _load_proxies(self):
        """Load proxy dari file"""
        try:
            with open(self.proxy_file, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                # Skip komentar dan baris kosong
                if not line or line.startswith("#"):
                    continue

                proxy = self._parse_proxy(line)
                if proxy:
                    self.proxies.append(proxy)

            print(f"{Fore.CYAN}[PROXY]{Style.RESET_ALL} Loaded {Fore.YELLOW}{len(self.proxies)}{Style.RESET_ALL} proxy dari {self.proxy_file}")

        except FileNotFoundError:
            print(f"{Fore.RED}[PROXY ERROR]{Style.RESET_ALL} File {self.proxy_file} tidak ditemukan!")
        except Exception as e:
            print(f"{Fore.RED}[PROXY ERROR]{Style.RESET_ALL} Gagal load proxy: {e}")

    def _parse_proxy(self, line: str) -> dict | None:
        """
        Parse berbagai format proxy:
        - http://ip:port
        - http://user:pass@ip:port
        - socks5://ip:port
        - ip:port (default http)
        - ip:port:user:pass (default http)
        """
        try:
            # Jika sudah ada protocol://
            if "://" in line:
                parsed = urlparse(line)
                server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                result = {"server": server}
                if parsed.username:
                    result["username"] = parsed.username
                    result["password"] = parsed.password or ""
                return result

            # Format ip:port
            parts = line.split(":")
            if len(parts) == 2:
                return {"server": f"http://{parts[0]}:{parts[1]}"}

            # Format ip:port:user:pass
            if len(parts) == 4:
                return {
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "username": parts[2],
                    "password": parts[3],
                }

            print(f"{Fore.YELLOW}[PROXY]{Style.RESET_ALL} Format tidak dikenali: {line}")
            return None

        except Exception:
            print(f"{Fore.YELLOW}[PROXY]{Style.RESET_ALL} Gagal parse: {line}")
            return None

    def validate_proxy(self, proxy: dict) -> bool:
        """Test apakah proxy aktif"""
        try:
            server = proxy["server"]
            proxies_dict = {
                "http": server,
                "https": server,
            }
            if proxy.get("username"):
                parsed = urlparse(server)
                auth_server = f"{parsed.scheme}://{proxy['username']}:{proxy['password']}@{parsed.hostname}:{parsed.port}"
                proxies_dict = {"http": auth_server, "https": auth_server}

            response = requests.get(
                "https://httpbin.org/ip",
                proxies=proxies_dict,
                timeout=config.PROXY_TIMEOUT,
            )
            if response.status_code == 200:
                ip = response.json().get("origin", "unknown")
                print(f"{Fore.GREEN}[PROXY]{Style.RESET_ALL} ✓ {server} aktif (IP: {ip})")
                return True
        except Exception:
            print(f"{Fore.RED}[PROXY]{Style.RESET_ALL} ✗ {proxy['server']} — mati/timeout")
        return False

    def get_next_proxy(self, validate: bool = None) -> dict | None:
        """
        Ambil proxy berikutnya (round-robin).
        Jika validate=True, skip proxy yang mati.
        """
        if not self.proxies:
            print(f"{Fore.RED}[PROXY]{Style.RESET_ALL} Tidak ada proxy tersedia!")
            return None

        should_validate = validate if validate is not None else config.PROXY_VALIDATE
        attempts = 0

        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            attempts += 1

            if should_validate:
                if self.validate_proxy(proxy):
                    return proxy
                else:
                    continue
            else:
                return proxy

        print(f"{Fore.RED}[PROXY]{Style.RESET_ALL} Semua proxy mati!")
        return None

    def get_playwright_proxy(self, proxy: dict = None) -> dict | None:
        """
        Convert proxy dict ke format yang dibutuhkan Playwright.
        Return dict: {"server": "...", "username": "...", "password": "..."}
        """
        if proxy is None:
            proxy = self.get_next_proxy()

        if proxy is None:
            return None

        pw_proxy = {"server": proxy["server"]}
        if proxy.get("username"):
            pw_proxy["username"] = proxy["username"]
            pw_proxy["password"] = proxy.get("password", "")

        return pw_proxy

    def total_proxies(self) -> int:
        return len(self.proxies)


if __name__ == "__main__":
    from colorama import init
    init()

    pm = ProxyManager()
    print(f"\nTotal proxy: {pm.total_proxies()}")

    if pm.total_proxies() > 0:
        print("\nValidasi semua proxy:")
        for i, p in enumerate(pm.proxies):
            pm.validate_proxy(p)
