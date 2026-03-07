"""
Temp Email Module — Multi-provider support
Provider 1: TempMail.lol (gratis, tanpa API key, domain sering diupdate)
Provider 2: Guerrilla Mail (established, gratis)
Provider 3: Mail.tm (backup, domain kadang diblock)
"""

import requests
import time
import re
import random
import string
import base64
from colorama import Fore, Style
import config


class TempEmail:
    """Manage temporary email dengan multiple provider fallback"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            "Accept": "application/json",
        })
        self.provider = None
        self.email_address = None
        self.password = None
        self.token = None  # Untuk mail.tm / tempmail.lol auth
        self.account_id = None
        self.guerrilla_sid = None  # Guerrilla Mail session ID

    def create_email(self) -> str:
        """Buat email temporary — coba tempmail.lol dulu, fallback"""
        # Try tempmail.lol first (paling reliable)
        email = self._create_tempmail_lol()
        if email:
            self.provider = "tempmail.lol"
            return email

        # Fallback: Guerrilla Mail
        email = self._create_guerrillamail()
        if email:
            self.provider = "guerrillamail"
            return email

        # Fallback: Mail.tm
        email = self._create_mailtm()
        if email:
            self.provider = "mail.tm"
            return email

        raise Exception("Gagal buat temp email dari semua provider!")

    # ═══════════════════════════════════════════
    # TempMail.lol Provider (Primary)
    # ═══════════════════════════════════════════
    def _create_tempmail_lol(self) -> str | None:
        """Buat email via TempMail.lol API — gratis, tanpa API key"""
        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Mencoba TempMail.lol...")

        try:
            resp = self.session.get(
                "https://api.tempmail.lol/v2/inbox/create",
                timeout=15,
            )

            if resp.status_code not in [200, 201]:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} TempMail.lol gagal: {resp.status_code}")
                return None

            data = resp.json()
            email = data.get("address")
            self.token = data.get("token")  # Token untuk check inbox

            if not email or not self.token:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} TempMail.lol response tidak valid")
                return None

            # Check domain blacklist
            domain = email.split("@")[1] if "@" in email else ""
            if domain in config.BLOCKED_EMAIL_DOMAINS:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} TempMail.lol domain '{domain}' diblokir, skip")
                return None

            self.email_address = email
            print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dibuat (TempMail.lol): {Fore.YELLOW}{email}{Style.RESET_ALL}")
            domain = email.split("@")[1] if "@" in email else "unknown"
            print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Domain: {Fore.YELLOW}{domain}{Style.RESET_ALL}")
            return email

        except Exception as e:
            print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} TempMail.lol error: {e}")
            return None

    def _check_tempmail_lol(self) -> str | None:
        """Cek inbox TempMail.lol untuk verification code"""
        try:
            resp = self.session.get(
                f"https://api.tempmail.lol/v2/inbox?token={self.token}",
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            emails = data.get("emails", [])

            for msg in emails:
                subject = msg.get("subject", "").lower()
                sender = msg.get("from", "").lower()

                if "openai" in sender or "openai" in subject or "verify" in subject or "code" in subject:
                    print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dari OpenAI ditemukan!")

                    # Body bisa di-base64 encode
                    body = msg.get("body", "")
                    html = msg.get("html", "")

                    # Coba decode base64 jika perlu
                    for content in [body, html]:
                        if content:
                            try:
                                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                                code = self._extract_code(decoded)
                                if code:
                                    return code
                            except Exception:
                                pass
                            # Coba langsung jika bukan base64
                            code = self._extract_code(content)
                            if code:
                                return code

            return None
        except Exception as e:
            print(f"{Fore.RED}[EMAIL ERROR]{Style.RESET_ALL} TempMail.lol check error: {e}")
            return None

    # ═══════════════════════════════════════════
    # Guerrilla Mail Provider (Secondary)
    # ═══════════════════════════════════════════
    def _create_guerrillamail(self) -> str | None:
        """Buat email via Guerrilla Mail API"""
        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Mencoba Guerrilla Mail...")

        try:
            resp = self.session.get(
                "https://api.guerrillamail.com/ajax.php",
                params={"f": "get_email_address", "lang": "en"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            email = data.get("email_addr")
            self.guerrilla_sid = data.get("sid_token")

            if not email:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Guerrilla Mail: tidak ada email")
                return None

            # Check domain blacklist
            domain = email.split("@")[1] if "@" in email else ""
            if domain in config.BLOCKED_EMAIL_DOMAINS:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Guerrilla Mail domain '{domain}' diblokir, skip")
                return None

            self.email_address = email

            print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dibuat (Guerrilla Mail): {Fore.YELLOW}{email}{Style.RESET_ALL}")
            domain = email.split("@")[1] if "@" in email else "unknown"
            print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Domain: {Fore.YELLOW}{domain}{Style.RESET_ALL}")
            return email

        except Exception as e:
            print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Guerrilla Mail error: {e}")
            return None

    def _check_guerrillamail(self) -> str | None:
        """Cek inbox Guerrilla Mail"""
        try:
            resp = self.session.get(
                "https://api.guerrillamail.com/ajax.php",
                params={
                    "f": "get_email_list",
                    "offset": "0",
                    "sid_token": self.guerrilla_sid,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            messages = data.get("list", [])

            for msg in messages:
                sender = msg.get("mail_from", "").lower()
                subject = msg.get("mail_subject", "").lower()
                mail_id = msg.get("mail_id")

                if "openai" in sender or "openai" in subject or "verify" in subject or "code" in subject:
                    print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dari OpenAI ditemukan!")

                    # Fetch full message
                    msg_resp = self.session.get(
                        "https://api.guerrillamail.com/ajax.php",
                        params={
                            "f": "fetch_email",
                            "email_id": mail_id,
                            "sid_token": self.guerrilla_sid,
                        },
                        timeout=15,
                    )
                    msg_data = msg_resp.json()
                    body = msg_data.get("mail_body", "")
                    code = self._extract_code(body)
                    if code:
                        return code

            return None
        except Exception as e:
            print(f"{Fore.RED}[EMAIL ERROR]{Style.RESET_ALL} Guerrilla Mail check error: {e}")
            return None

    # ═══════════════════════════════════════════
    # Mail.tm Provider (Backup)
    # ═══════════════════════════════════════════
    def _create_mailtm(self) -> str | None:
        """Buat email via Mail.tm API"""
        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Mencoba Mail.tm...")

        try:
            # 1. Get available domains
            resp = self.session.get("https://api.mail.tm/domains", timeout=10)
            resp.raise_for_status()
            domains = resp.json()

            domain_list = domains.get("hydra:member", domains) if isinstance(domains, dict) else domains
            if not domain_list:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Mail.tm: tidak ada domain tersedia")
                return None

            # Filter domain yang diblokir oleh OpenAI
            available_domains = [
                d["domain"] for d in domain_list
                if d["domain"] not in config.BLOCKED_EMAIL_DOMAINS
            ]

            if not available_domains:
                blocked = config.BLOCKED_EMAIL_DOMAINS
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Mail.tm: semua domain diblokir: {blocked}")
                return None

            domain = available_domains[0]

            # 2. Generate random username
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            email = f"{username}@{domain}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

            # 3. Create account
            resp = self.session.post("https://api.mail.tm/accounts", json={
                "address": email,
                "password": password,
            }, timeout=10)

            if resp.status_code not in [200, 201]:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Mail.tm create gagal: {resp.status_code}")
                return None

            data = resp.json()
            self.account_id = data.get("id")

            # 4. Get auth token
            resp = self.session.post("https://api.mail.tm/token", json={
                "address": email,
                "password": password,
            }, timeout=10)

            if resp.status_code == 200:
                self.token = resp.json().get("token")
            else:
                print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Mail.tm token gagal: {resp.status_code}")
                return None

            self.email_address = email
            self.password = password

            print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dibuat (Mail.tm): {Fore.YELLOW}{email}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Domain: {Fore.YELLOW}{domain}{Style.RESET_ALL}")
            return email

        except Exception as e:
            print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Mail.tm error: {e}")
            return None

    def _check_mailtm(self) -> str | None:
        """Cek inbox Mail.tm untuk verification code"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = self.session.get(
                "https://api.mail.tm/messages",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            messages = data.get("hydra:member", data) if isinstance(data, dict) else data

            for msg in messages:
                subject = msg.get("subject", "").lower()
                sender = str(msg.get("from", {}).get("address", "")).lower()

                if "openai" in sender or "openai" in subject or "verify" in subject or "code" in subject:
                    print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email dari OpenAI ditemukan!")
                    # Fetch full message
                    msg_id = msg.get("id")
                    msg_resp = self.session.get(
                        f"https://api.mail.tm/messages/{msg_id}",
                        headers=headers,
                        timeout=10,
                    )
                    msg_data = msg_resp.json()

                    # Extract code from text or html body
                    body = msg_data.get("text", "") or msg_data.get("html", [""])[0] if isinstance(msg_data.get("html"), list) else msg_data.get("text", "")
                    code = self._extract_code(body)
                    if code:
                        return code

            return None
        except Exception as e:
            print(f"{Fore.RED}[EMAIL ERROR]{Style.RESET_ALL} Mail.tm check error: {e}")
            return None

    # ═══════════════════════════════════════════
    # Common Methods
    # ═══════════════════════════════════════════
    def wait_for_verification_code(self) -> str | None:
        """Polling inbox untuk cari verification code dari OpenAI"""
        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Menunggu email verifikasi dari OpenAI... (provider: {self.provider})")
        start_time = time.time()

        while time.time() - start_time < config.EMAIL_POLL_TIMEOUT:
            # Check berdasarkan provider
            code = None
            if self.provider == "tempmail.lol":
                code = self._check_tempmail_lol()
            elif self.provider == "guerrillamail":
                code = self._check_guerrillamail()
            elif self.provider == "mail.tm":
                code = self._check_mailtm()

            if code:
                return code

            elapsed = int(time.time() - start_time)
            remaining = config.EMAIL_POLL_TIMEOUT - elapsed
            print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Belum ada email... (sisa {remaining}s)")
            time.sleep(config.EMAIL_POLL_INTERVAL)

        print(f"{Fore.RED}[EMAIL]{Style.RESET_ALL} Timeout! Tidak ada email verifikasi dalam {config.EMAIL_POLL_TIMEOUT}s")
        return None

    def _extract_code(self, body: str) -> str | None:
        """Extract 6-digit verification code dari email body"""
        if not body:
            return None

        patterns = [
            r'\b(\d{6})\b',
            r'code[:\s]+(\d{6})',
            r'verification[:\s]+(\d{6})',
            r'verify[:\s]+(\d{6})',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                code = match.group(1)
                print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Verification code: {Fore.YELLOW}{code}{Style.RESET_ALL}")
                return code

        print(f"{Fore.YELLOW}[EMAIL]{Style.RESET_ALL} Email ditemukan tapi code tidak bisa di-parse")
        return None

    def get_email_address(self) -> str:
        return self.email_address


if __name__ == "__main__":
    from colorama import init
    init()

    email = TempEmail()
    addr = email.create_email()
    print(f"\nEmail: {addr}")
    print(f"Provider: {email.provider}")
    print("\nMenunggu email masuk... (Ctrl+C untuk stop)")

    try:
        code = email.wait_for_verification_code()
        print(f"Code: {code}" if code else "Tidak ada code")
    except KeyboardInterrupt:
        print("\nDibatalkan.")
