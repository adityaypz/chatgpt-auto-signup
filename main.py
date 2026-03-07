"""
╔══════════════════════════════════════════════════╗
║   ChatGPT Auto Signup Bot — Learning Project     ║
║   Untuk testing kemampuan browser automation     ║
╚══════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import sys
import os
import warnings
from datetime import datetime
from colorama import init, Fore, Style

# Suppress asyncio pipe warnings on Windows (cosmetic, doesn't affect functionality)
warnings.filterwarnings("ignore", category=ResourceWarning)

import nodriver as uc
import config
from signup_bot import SignupBot

# Init colorama untuk Windows
init()


def print_banner():
    """Tampilkan banner"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║                                                  ║
║   {Fore.WHITE}ChatGPT Auto Signup Bot{Fore.CYAN}                       ║
║   {Fore.YELLOW}Learning Project — Browser Automation{Fore.CYAN}         ║
║   {Fore.GREEN}Engine: nodriver (undetected Chrome){Fore.CYAN}          ║
║                                                  ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def save_result(result: dict):
    """Simpan hasil signup ke file"""
    if not config.SAVE_CREDENTIALS:
        return

    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        line = (
            f"[{result['timestamp']}] "
            f"Status: {result['status']} | "
            f"Email: {result.get('email', 'N/A')} | "
            f"Password: {result.get('password', 'N/A')}"
        )
        if result.get("error"):
            line += f" | Error: {result['error']}"
        f.write(line + "\n")

    print(f"{Fore.CYAN}[SAVE]{Style.RESET_ALL} Hasil disimpan ke {config.LOG_FILE}")


def print_summary(results: list):
    """Tampilkan ringkasan di akhir"""
    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success

    print(f"\n{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}  📊 RINGKASAN{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}")
    print(f"  Total    : {len(results)}")
    print(f"  {Fore.GREEN}Berhasil : {success}{Style.RESET_ALL}")
    print(f"  {Fore.RED}Gagal    : {failed}{Style.RESET_ALL}")

    if success > 0:
        print(f"\n  {Fore.GREEN}✓ Akun berhasil:{Style.RESET_ALL}")
        for r in results:
            if r["status"] == "success":
                print(f"    {r['email']} : {r['password']}")

    print(f"{Fore.CYAN}{'═' * 50}{Style.RESET_ALL}\n")


async def run_signup(count: int, headless: bool, use_proxy: bool, delay: int):
    """Jalankan signup sebanyak count kali"""
    results = []

    for i in range(count):
        print(f"\n{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  🚀 Signup #{i + 1}/{count}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}\n")

        bot = SignupBot(headless=headless, use_proxy=use_proxy)

        try:
            result = await bot.signup()
            results.append(result)
            save_result(result)
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Signup #{i + 1} gagal total: {e}")
            results.append({
                "email": None,
                "password": None,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
        finally:
            await bot.close()

        # Delay antar signup
        if i < count - 1 and delay > 0:
            print(f"\n{Fore.CYAN}[DELAY]{Style.RESET_ALL} Menunggu {delay} detik sebelum signup berikutnya...")
            await asyncio.sleep(delay)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="ChatGPT Auto Signup Bot — Learning Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py                    # 1 akun, headed mode
  python main.py --count 3          # 3 akun
  python main.py --headless         # Background mode
  python main.py --proxy            # Gunakan proxy
  python main.py --count 2 --proxy --delay 10
        """
    )

    parser.add_argument(
        "--count", "-c",
        type=int,
        default=1,
        help="Jumlah akun yang akan dibuat (default: 1)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Jalankan tanpa tampilan browser (default: headed/visible)"
    )
    parser.add_argument(
        "--proxy",
        action="store_true",
        help="Aktifkan proxy (baca dari proxies.txt)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=5,
        help="Delay antar signup dalam detik (default: 5)"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # 1. Tanya user berapa akun yang mau dibuat (Timpa argument --count)
    print(f"{Fore.CYAN}╭────────────────────────────────────────────────╮{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│ {Fore.WHITE}Berapa banyak akun yang ingin dibuat?    {Fore.CYAN}      │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╰────────────────────────────────────────────────╯{Style.RESET_ALL}")
    try:
        user_input = input(f"   {Fore.YELLOW}Jumlah (default {args.count}): {Style.RESET_ALL}")
        count = int(user_input) if user_input.strip() else args.count
        if count <= 0:
            count = 1
    except ValueError:
        print(f"{Fore.RED}   Input invalid, menggunakan default ({args.count}){Style.RESET_ALL}")
        count = args.count
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}   Dibatalkan.{Style.RESET_ALL}")
        sys.exit(0)

    # Print config
    headless = args.headless
    print(f"\n{Fore.WHITE}  ⚙️  Konfigurasi:{Style.RESET_ALL}")
    print(f"     Jumlah akun : {count}")
    print(f"     Mode        : {'Headless' if headless else 'Headed (visible)'}")
    print(f"     Proxy       : {'Aktif' if args.proxy else 'Tidak aktif'}")
    print(f"     Delay       : {args.delay}s antar signup")
    print()

    # Konfirmasi
    try:
        input(f"{Fore.YELLOW}  Tekan ENTER untuk mulai pembuatan {count} akun (Ctrl+C untuk batal)...{Style.RESET_ALL}\n")
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}  Dibatalkan.{Style.RESET_ALL}")
        sys.exit(0)

    # Run — nodriver perlu pakai uc.loop() bukan asyncio.run()
    uc.loop().run_until_complete(run_signup(
        count=count,
        headless=headless,
        use_proxy=args.proxy,
        delay=args.delay,
    ))


if __name__ == "__main__":
    main()
