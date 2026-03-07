"""
Signup Bot — Core automation untuk signup ChatGPT
Menggunakan nodriver (undetected Chrome) untuk bypass Cloudflare
"""

import asyncio
import time
import string
import random
from datetime import datetime, timedelta
import nodriver as uc
from colorama import Fore, Style
from faker import Faker
import config
from temp_email import TempEmail
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver


class AuthErrorException(Exception):
    """Raised ketika ChatGPT redirect ke auth/error"""
    pass


fake = Faker()


class SignupBot:
    """Automate ChatGPT signup process dengan nodriver (undetected)"""

    def __init__(self, headless: bool = None, use_proxy: bool = None):
        self.headless = headless if headless is not None else config.HEADLESS
        self.use_proxy = use_proxy if use_proxy is not None else config.USE_PROXY
        self.browser = None
        self.page = None
        self.temp_email = TempEmail()
        self.proxy_manager = ProxyManager() if self.use_proxy else None
        self.captcha_solver = CaptchaSolver() if config.CAPTCHA_ENABLED else None
        self.results = []

    # ═══════════════════════════════════════════
    # Human-like Behavior
    # ═══════════════════════════════════════════
    async def _random_delay(self, min_s: float = 0.5, max_s: float = 2.0):
        """Delay random"""
        await asyncio.sleep(random.uniform(min_s, max_s))

    def _generate_password(self) -> str:
        """Generate password kuat (min 12 chars)"""
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = (
            random.choice(string.ascii_uppercase)
            + random.choice(string.ascii_lowercase)
            + random.choice(string.digits)
            + random.choice("!@#$%")
            + "".join(random.choice(chars) for _ in range(config.PASSWORD_LENGTH - 4))
        )
        return "".join(random.sample(password, len(password)))

    def _generate_birthday(self) -> dict:
        """Generate tanggal lahir random"""
        today = datetime.now()
        min_date = today - timedelta(days=config.MAX_AGE * 365)
        max_date = today - timedelta(days=config.MIN_AGE * 365)
        random_date = min_date + timedelta(
            days=random.randint(0, (max_date - min_date).days)
        )
        return {
            "year": str(random_date.year),
            "month": str(random_date.month).zfill(2),
            "day": str(random_date.day).zfill(2),
        }

    # ═══════════════════════════════════════════
    # Browser Setup
    # ═══════════════════════════════════════════
    async def _setup_browser(self):
        """Launch browser dengan nodriver (undetected Chrome)"""
        self._print_step("Launching browser (nodriver/undetected)...")

        browser_args = []
        if self.use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                # nodriver menerima args Chrome standar
                server = proxy['server'].replace('http://', '').replace('https://', '')
                browser_args.append(f"--proxy-server={server}")
                self._print_success(f"Menggunakan proxy: {server}")
                
                # CATATAN: Chrome headless/nodriver native tidak mendukung username:password
                # proxy credentials di command line secara aman. Jika proxy premium butuh auth,
                # direkomendasikan whitelist IP VPS di dashboard provider proxy (IP Auth).
                if proxy.get('username'):
                    self._print_warning("Proxy memerlukan username/password.")
                    self._print_warning("Pastikan Anda menggunakan 'IP Whitelist' di provider proxy Anda untuk nodriver.")

        self.browser = await uc.start(
            headless=self.headless,
            lang="en-US",
            browser_args=browser_args
        )

        self._print_success("Browser launched (nodriver/undetected)!")

    # ═══════════════════════════════════════════
    # Navigation
    # ═══════════════════════════════════════════
    async def _navigate_to_signup(self):
        """Buka halaman signup ChatGPT"""
        self._print_step("Navigating to ChatGPT signup...")

        self.page = await self.browser.get(config.SIGNUP_URL)

        # Tunggu halaman load penuh
        self._print_step("Menunggu halaman load...")
        await self.page.sleep(4)

        # Handle Cloudflare jika ada
        try:
            self._print_step("Checking Cloudflare challenge...")
            await self.page.cf_verify()
            self._print_success("Cloudflare OK!")
            await self.page.sleep(2)
        except Exception:
            self._print_step("Tidak ada Cloudflare challenge, lanjut...")

        # Klik tombol Sign Up
        signup_clicked = False
        signup_texts = ["Sign up", "Get started", "Create account"]

        for text in signup_texts:
            try:
                element = await self.page.find(text, best_match=True, timeout=5)
                if element:
                    await element.click()
                    signup_clicked = True
                    self._print_success(f"Klik '{text}' berhasil!")
                    break
            except Exception:
                continue

        if not signup_clicked:
            # Coba via href
            try:
                element = await self.page.select("a[href*='signup']", timeout=5)
                if element:
                    await element.click()
                    signup_clicked = True
                    self._print_success("Klik link signup berhasil!")
            except Exception:
                pass

        if not signup_clicked:
            self._print_warning("Tombol Sign Up tidak ditemukan, mungkin sudah di halaman signup")

        await self.page.sleep(3)

        # Handle Cloudflare lagi setelah klik signup
        try:
            await self.page.cf_verify()
            await self.page.sleep(2)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    # Email Entry
    # ═══════════════════════════════════════════
    async def _enter_email(self, email: str):
        """Input email address"""
        self._print_step(f"Memasukkan email: {email}")
        await self._random_delay(1.0, 2.0)

        # Cari input email via CSS selector
        email_element = None
        selectors = [
            "input[name='email']",
            "input[type='email']",
            "input[id='email']",
            "input[name='username']",
            "input[autocomplete='email']",
        ]

        for selector in selectors:
            try:
                email_element = await self.page.select(selector, timeout=5)
                if email_element:
                    self._print_step(f"Email input ditemukan via: {selector}")
                    break
            except Exception:
                continue

        if not email_element:
            # Debug: print halaman saat ini
            self._print_error(f"Email input tidak ditemukan! URL: {self.page.url}")
            try:
                await self.page.save_screenshot("debug_no_email_input.png")
                self._print_warning("Screenshot debug: debug_no_email_input.png")
            except Exception:
                pass
            raise Exception("Email input not found")

        # Klik dan ketik email
        await email_element.click()
        await self._random_delay(0.3, 0.8)
        await email_element.send_keys(email)
        self._print_success("Email dimasukkan!")

        await self._random_delay(0.5, 1.5)

        # Simpan URL sebelum klik continue
        url_before = self.page.url

        # Klik Continue
        await self._click_continue()

        # Tunggu halaman berubah
        self._print_step("Menunggu halaman password...")
        await self.page.sleep(5)

        # Cek auth error
        if await self._check_auth_error():
            domain = email.split('@')[1] if '@' in email else 'unknown'
            raise AuthErrorException(
                f"Email domain '{domain}' diblock oleh OpenAI"
            )

    # ═══════════════════════════════════════════
    # Password Entry
    # ═══════════════════════════════════════════
    async def _enter_password(self, password: str):
        """Input password"""
        self._print_step("Memasukkan password...")
        await self._random_delay(1.5, 3.0)

        selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[id='password']",
            "input[autocomplete='new-password']",
        ]

        for attempt in range(config.MAX_RETRIES):
            for selector in selectors:
                try:
                    element = await self.page.select(selector, timeout=5)
                    if element:
                        await element.click()
                        await self._random_delay(0.3, 0.8)
                        await element.send_keys(password)
                        self._print_success("Password dimasukkan!")

                        await self._random_delay(0.5, 1.5)
                        await self._click_continue()

                        self._print_step("Menunggu halaman berikutnya...")
                        await self.page.sleep(4)
                        return
                except Exception:
                    continue

            if attempt < config.MAX_RETRIES - 1:
                self._print_warning(f"Password field belum muncul, retry {attempt + 2}/{config.MAX_RETRIES}...")
                await self.page.sleep(config.RETRY_DELAY)

        self._print_error(f"Password input tidak ditemukan! URL: {self.page.url}")
        try:
            await self.page.save_screenshot("debug_no_password.png")
        except Exception:
            pass
        raise Exception("Password input not found")

    # ═══════════════════════════════════════════
    # Verification Code
    # ═══════════════════════════════════════════
    async def _enter_verification_code(self, code: str):
        """Input 6-digit verification code"""
        self._print_step(f"Memasukkan verification code: {code}")
        await self._random_delay(1, 2)

        code_selectors = [
            "input[name='code']",
            "input[type='text'][maxlength='6']",
            "input[autocomplete='one-time-code']",
            "input[inputmode='numeric']",
            "input#code",
        ]

        for selector in code_selectors:
            try:
                element = await self.page.select(selector, timeout=5)
                if element:
                    await element.click()
                    await self._random_delay(0.3, 0.5)
                    await element.send_keys(code)
                    self._print_success("Verification code dimasukkan!")
                    await self.page.sleep(1)
                    await self._click_continue()
                    return
            except Exception:
                continue

        self._print_error("Input verification code tidak ditemukan!")

    # ═══════════════════════════════════════════
    # Personal Info
    # ═══════════════════════════════════════════
    async def _fill_personal_info(self):
        """Isi nama dan tanggal lahir di halaman 'Let's confirm your age'"""
        self._print_step("Mengisi informasi personal...")
        await self._random_delay(1, 2)

        full_name = f"{fake.first_name()} {fake.last_name()}"
        birthday = self._generate_birthday()
        
        # PENTING: Format YYYY-MM-DD sering dibutuhkan untuk hidden date inputs
        dob_value = f"{birthday['year']}-{birthday['month']}-{birthday['day']}"

        self._print_step(f"Nama: {full_name}, DOB: {birthday['month']}/{birthday['day']}/{birthday['year']}")

        # === 1. JS INJECTION (PALING RELIABLE) ===
        js_code = f"""
        (() => {{
            const fullName = "{full_name}";
            const month = "{birthday['month']}";
            const day = "{birthday['day']}";
            const year = "{birthday['year']}";
            const dobValue = "{dob_value}";
            let results = {{name: false, dob: false}};

            let nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;

            // Helper: Simulasi ketikan manusia (Bypass React validation)
            const simulateTyping = (el, text) => {{
                el.focus();
                
                // Set value secara nativer
                try {{ nativeSetter.call(el, text); }} catch(e) {{ el.value = text; }}
                
                // Tembakkan serangkaian event untuk menipu React
                el.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', charCode: 13, keyCode: 13, bubbles: true }}));
                el.dispatchEvent(new KeyboardEvent('keypress', {{ key: 'Enter', code: 'Enter', charCode: 13, keyCode: 13, bubbles: true }}));
                el.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', charCode: 13, keyCode: 13, bubbles: true }}));
                
                el.blur();
            }};

            // === NAMA ===
            let nameInput = document.querySelector("input[name='name']")
                || document.querySelector("input[name='fullName']")
                || document.querySelector("input[name='full_name']")
                || document.querySelector("input[name='firstName']");

            if (nameInput) {{
                simulateTyping(nameInput, fullName);
                results.name = true;
            }}

            // === BIRTHDAY ===
            
            // Method 1: Cari hidden/standard date input dan force value-nya
            let bdayInputs = document.querySelectorAll("input[name='birthday'], input[type='date'], input[name='date_of_birth']");
            bdayInputs.forEach(input => {{
                try {{
                    simulateTyping(input, dobValue);
                    results.dob = true;
                }} catch(e) {{}}
            }});

            // Method 2: Cari React spinbuttons (month, day, year)
            let monthEls = document.querySelectorAll("[aria-label*='month' i], input[placeholder*='mm' i], input[placeholder*='month' i]");
            let dayEls = document.querySelectorAll("[aria-label*='day' i], input[placeholder*='dd' i], input[placeholder*='day' i]");
            let yearEls = document.querySelectorAll("[aria-label*='year' i], input[placeholder*='yyyy' i], input[placeholder*='year' i]");

            if (monthEls.length > 0 && dayEls.length > 0 && yearEls.length > 0) {{
                let mEl = monthEls[0];
                let dEl = dayEls[0];
                let yEl = yearEls[0];
                
                if (mEl.tagName.toLowerCase() === 'input') {{
                   simulateTyping(mEl, month);
                   simulateTyping(dEl, day);
                   simulateTyping(yEl, year);
                }} else {{
                   mEl.textContent = month;
                   dEl.textContent = day;
                   yEl.textContent = year;
                   
                   [mEl, dEl, yEl].forEach(el => {{
                       el.dispatchEvent(new Event('input', {{bubbles: true}}));
                       el.dispatchEvent(new Event('change', {{bubbles: true}}));
                       el.dispatchEvent(new Event('blur', {{bubbles: true}}));
                   }});
                }}
                results.dob = true;
            }}

            return JSON.stringify(results);
        }})();
        """

        try:
            result_str = await self.page.evaluate(js_code)
            self._print_success(f"JS injection result: {result_str}")
        except Exception as e:
            self._print_warning(f"JS injection error: {e}")

            # === 2. FALLBACK KEYBOARD ===
            self._print_step("Fallback: keyboard approach...")
            try:
                name_selectors = ["input[name='name']", "input[name='fullName']", "input[name='firstName']"]
                for sel in name_selectors:
                    try:
                        name_el = await self.page.select(sel, timeout=3)
                        if name_el:
                            await name_el.click()
                            await self._random_delay(0.2, 0.4)
                            await name_el.apply("function(e) { e.value = ''; }")
                            await name_el.send_keys(full_name)
                            break
                    except Exception:
                        continue
                
                # Birthday fields fallback
                month_el = await self.page.select("[aria-label*='month' i], input[placeholder*='mm' i]", timeout=3)
                if month_el:
                    await month_el.click()
                    await month_el.send_keys(birthday['month'])
                
                day_el = await self.page.select("[aria-label*='day' i], input[placeholder*='dd' i]", timeout=3)
                if day_el:
                    await day_el.click()
                    await day_el.send_keys(birthday['day'])
                
                year_el = await self.page.select("[aria-label*='year' i], input[placeholder*='yyyy' i]", timeout=3)
                if year_el:
                    await year_el.click()
                    await year_el.send_keys(birthday['year'])
                        
            except Exception as e2:
                self._print_warning(f"Keyboard fallback juga gagal: {e2}")

        self._print_success(f"Info: {full_name}, DOB: {birthday['month']}/{birthday['day']}/{birthday['year']}")
        await self._random_delay(1.0, 2.0)

        self._print_step("Mencoba klik tombol submit/finish...")
        js_click = """
        (() => {
            let btns = Array.from(document.querySelectorAll('button'));
            // Cari tombol yang teksnya mengandung kata kunci submit/finish
            let submitBtn = btns.find(b => {
                let text = b.textContent.toLowerCase();
                return text.includes('finish') || text.includes('agree') || text.includes('continue') || text.includes('submit');
            });
            if (submitBtn) {
                // Hapus atribut disabled jika form react masih melocknya
                submitBtn.removeAttribute('disabled');
                submitBtn.disabled = false;
                submitBtn.click();
                return submitBtn.textContent.trim();
            }
            return null;
        })();
        """
        try:
            btn_text = await self.page.evaluate(js_click)
            if btn_text:
                self._print_success(f"Klik '{btn_text}' via JS berhasil!")
                await self._random_delay(2.0, 4.0)
                return
        except Exception as e:
            self._print_warning(f"JS submit click error: {e}")

        # Fallback nodriver click
        finish_texts = ["Agree", "Finish creating account", "Continue", "Submit", "Next"]
        for text in finish_texts:
            try:
                element = await self.page.find(text, best_match=True, timeout=3)
                if element:
                    await element.click()
                    self._print_success(f"Klik '{text}' via nodriver berhasil!")
                    return
            except Exception:
                continue

        await self._click_continue()

    # ═══════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════
    async def _click_continue(self):
        """Cari dan klik tombol Continue/Submit secara paksa via JS"""
        await self.page.sleep(0.5)

        js_click = """
        (() => {
            let btns = Array.from(document.querySelectorAll('button'));
            
            // Cari tombol utama, hindari tombol SSO (Google/Apple/Microsoft)
            let submitBtn = btns.find(b => {
                let text = b.textContent.toLowerCase();
                let isSSO = text.includes('google') || text.includes('apple') || text.includes('microsoft');
                let isSubmit = text.includes('continue') || text.includes('next') || text.includes('submit') || text.includes('verify');
                return isSubmit && !isSSO;
            });
            
            if (submitBtn) {
                // Hapus atribut disabled jika form react masih melocknya
                submitBtn.removeAttribute('disabled');
                submitBtn.disabled = false;
                submitBtn.click();
                return submitBtn.textContent.trim();
            }
            
            // Fallback button type submit
            let formBtn = document.querySelector("button[type='submit']");
            if (formBtn) {
                formBtn.removeAttribute('disabled');
                formBtn.disabled = false;
                formBtn.click();
                return formBtn.textContent.trim();
            }
            
            return null;
        })();
        """

        try:
            btn_text = await self.page.evaluate(js_click)
            if btn_text:
                self._print_success(f"Klik '{btn_text}' via JS berhasil!")
                await self._random_delay(0.5, 1.5)
                return
        except Exception as e:
            self._print_warning(f"JS submit click error di _click_continue: {e}")

        # Fallback nodriver
        button_texts = ["Continue", "Next", "Submit", "Verify"]
        for text in button_texts:
            try:
                element = await self.page.find(text, best_match=True, timeout=3)
                if element:
                    await element.click()
                    await self._random_delay(0.5, 1.5)
                    return
            except Exception:
                continue

        # Fallback 2: button[type='submit']
        try:
            element = await self.page.select("button[type='submit']", timeout=3)
            if element:
                await element.click()
                await self._random_delay(0.5, 1.5)
        except Exception:
            pass

    async def _check_auth_error(self) -> bool:
        """Cek apakah halaman redirect ke auth error"""
        current_url = str(self.page.url or "")
        if "/api/auth/error" in current_url or "/auth/error" in current_url:
            self._print_warning(f"⚠️ Auth error detected: {current_url}")
            return True
        return False

    async def _handle_phone_verification(self) -> bool:
        """Deteksi halaman phone verification"""
        try:
            element = await self.page.select("input[type='tel']", timeout=3)
            if element:
                self._print_warning("📱 Phone verification terdeteksi!")
                self._print_warning("👉 Masukkan nomor HP secara manual di browser")
                input(f"\n{Fore.YELLOW}[INPUT]{Style.RESET_ALL} Tekan ENTER setelah selesai verifikasi HP...")
                return True
        except Exception:
            pass
        return False

    async def _dismiss_dialogs(self):
        """Tutup dialog/popup"""
        for text in ["Next", "Done", "OK", "Skip", "Got it"]:
            try:
                element = await self.page.find(text, best_match=True, timeout=2)
                if element:
                    await element.click()
                    await self.page.sleep(0.5)
            except Exception:
                continue

    # ═══════════════════════════════════════════
    # Main Signup Flow
    # ═══════════════════════════════════════════
    async def signup(self) -> dict:
        """Jalankan full signup flow"""
        result = {
            "email": None,
            "password": None,
            "status": "failed",
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 1. Setup browser
            await self._setup_browser()

            # Retry loop
            max_email_retries = config.MAX_EMAIL_RETRIES
            email_addr = None
            password = None

            for email_attempt in range(max_email_retries):
                try:
                    if email_attempt > 0:
                        self._print_warning(
                            f"🔄 Retry #{email_attempt + 1}/{max_email_retries} dengan email baru..."
                        )

                    # 2. Generate credentials
                    email_addr = self.temp_email.create_email()
                    password = self._generate_password()
                    result["email"] = email_addr
                    result["password"] = password

                    # 3. Navigate ke signup
                    await self._navigate_to_signup()

                    # 4. Enter email
                    await self._enter_email(email_addr)
                    await self._random_delay(1, 2)

                    # Cek auth error
                    if await self._check_auth_error():
                        domain = email_addr.split('@')[1] if '@' in email_addr else 'unknown'
                        raise AuthErrorException(f"Domain '{domain}' diblock")

                    break  # Berhasil lewat email step

                except AuthErrorException as e:
                    domain = email_addr.split('@')[1] if '@' in email_addr else 'unknown'
                    self._print_warning(f"⚠️ Domain '{domain}' diblock! ({email_attempt + 1}/{max_email_retries})")
                    if domain not in config.BLOCKED_EMAIL_DOMAINS:
                        config.BLOCKED_EMAIL_DOMAINS.append(domain)
                    if email_attempt >= max_email_retries - 1:
                        raise Exception(f"Semua email domain diblock: {config.BLOCKED_EMAIL_DOMAINS}")
                    continue

            # 5. Enter password
            await self._enter_password(password)
            await self._random_delay(1, 2)

            # 6. Wait for verification code
            self._print_step("Menunggu email verifikasi...")
            code = self.temp_email.wait_for_verification_code()

            if code:
                await self._enter_verification_code(code)
                await self._random_delay(1, 2)

                phone_required = await self._handle_phone_verification()

                try:
                    await self._fill_personal_info()
                except Exception:
                    pass

                await self.page.sleep(2)
                await self._dismiss_dialogs()

                result["status"] = "success"
                result["phone_required"] = phone_required
                self._print_success(f"🎉 SIGNUP BERHASIL!")
                self._print_success(f"   Email: {email_addr}")
                self._print_success(f"   Password: {password}")
            else:
                result["error"] = "Verification code not received"
                self._print_error("Gagal: verification code tidak diterima")

        except Exception as e:
            result["error"] = str(e)
            self._print_error(f"Error: {e}")

        self.results.append(result)
        return result

    async def close(self):
        """Tutup browser"""
        try:
            if self.browser:
                self.browser.stop()
        except Exception:
            pass
        self._print_step("Browser ditutup")

    # ═══════════════════════════════════════════
    # Print Helpers
    # ═══════════════════════════════════════════
    def _print_step(self, msg: str):
        print(f"{Fore.CYAN}[BOT]{Style.RESET_ALL} {msg}")

    def _print_success(self, msg: str):
        print(f"{Fore.GREEN}[BOT]{Style.RESET_ALL} {msg}")

    def _print_warning(self, msg: str):
        print(f"{Fore.YELLOW}[BOT]{Style.RESET_ALL} {msg}")

    def _print_error(self, msg: str):
        print(f"{Fore.RED}[BOT]{Style.RESET_ALL} {msg}")
