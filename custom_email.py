import random
import string
import time
import re
from imapclient import IMAPClient
import mailparser
from colorama import Fore, Style
import config

class CustomDomainEmail:
    """
    Manage email using Custom Domain Catch-all (Cloudflare Routing) + Gmail IMAP.
    This replaces public temp mail providers for higher quality accounts.
    """

    def __init__(self):
        # Configuration - You will need to set these in your config.py or .env
        self.domain = "moonarket.shop"
        self.imap_host = "imap.gmail.com"
        
        # NOTE: GMAIL REQUIRES AN "APP PASSWORD", NOT YOUR REGULAR PASSWORD.
        # Go to Google Account -> Security -> 2-Step Verification -> App Passwords
        self.gmail_user = "hyungsikkim1@gmail.com" 
        self.gmail_app_password = getattr(config, "GMAIL_APP_PASSWORD", "SET_THIS_IN_CONFIG") 
        
        self.email_address = None
        self.provider = "custom_domain_catchall"

    def create_email(self) -> str:
        """Generate a random professional-looking email address on the custom domain."""
        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Generating custom domain email...")
        
        # Generate format like: user.12345@moonarket.shop or admin.xyz@moonarket.shop
        prefixes = ["user", "admin", "info", "contact", "support", "hello", "gpt", "account"]
        prefix = random.choice(prefixes)
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        
        self.email_address = f"{prefix}.{random_str}@{self.domain}"
        
        print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Email created: {Fore.YELLOW}{self.email_address}{Style.RESET_ALL}")
        return self.email_address

    def wait_for_verification_code(self) -> str | None:
        """Poll Gmail inbox via IMAP to find the OpenAI verification code sent to the generated email."""
        if self.gmail_app_password == "SET_THIS_IN_CONFIG":
            print(f"{Fore.RED}[EMAIL ERROR]{Style.RESET_ALL} You must set GMAIL_APP_PASSWORD in config.py!")
            print("Create an App Password at: https://myaccount.google.com/apppasswords")
            return None

        print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Polling '{self.gmail_user}' inbox for verification code...")
        start_time = time.time()

        try:
            with IMAPClient(self.imap_host, ssl=True) as server:
                server.login(self.gmail_user, self.gmail_app_password)
                
                while time.time() - start_time < config.EMAIL_POLL_TIMEOUT:
                    server.select_folder('INBOX')
                    
                    # Cuma cari yang UNSEEN. Gak usah filter SUBJECT dari IMAP karena sering ngaco pas forwarding/catch-all
                    messages = server.search(['UNSEEN'])
                    
                    if messages:
                        # Ambil maksimal 10 email terbaru biar gak berat (karena inbox user ada ribuan unread)
                        recent_messages = messages[-10:]
                        for msgid, data in server.fetch(recent_messages, 'RFC822').items():
                            email_message = mailparser.parse_from_bytes(data[b'RFC822'])
                        
                        subject = email_message.subject.lower() if email_message.subject else ""
                        sender = str(email_message.from_).lower() if email_message.from_ else ""
                        
                        # Cek apakah ini beneran dari OpenAI
                        if "openai" in subject or "openai" in sender or "verify" in subject or "code" in subject:
                            body = email_message.text_plain[0] if email_message.text_plain else (email_message.text_html[0] if email_message.text_html else "")
                            
                            code = self._extract_code(body)
                            if code:
                                print(f"{Fore.GREEN}[EMAIL]{Style.RESET_ALL} Verification code found: {Fore.YELLOW}{code}{Style.RESET_ALL}")
                                # Mark as read so we don't process it again
                                server.add_flags(msgid, b'\\Seen')
                                return code

                    # Wait before checking again
                    elapsed = int(time.time() - start_time)
                    remaining = config.EMAIL_POLL_TIMEOUT - elapsed
                    print(f"{Fore.CYAN}[EMAIL]{Style.RESET_ALL} Waiting for email... (remaining {remaining}s)")
                    time.sleep(10) # Polish interval every 10 seconds

        except Exception as e:
             print(f"{Fore.RED}[EMAIL ERROR]{Style.RESET_ALL} IMAP checking failed: {e}")

        print(f"{Fore.RED}[EMAIL]{Style.RESET_ALL} Timeout! Verification email not received.")
        return None

    def _extract_code(self, body: str) -> str | None:
        """Extract 6-digit verification code from email body"""
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
                return match.group(1)

        return None

    def get_email_address(self) -> str:
        return self.email_address

if __name__ == "__main__":
    # Simple test execution
    email_manager = CustomDomainEmail()
    addr = email_manager.create_email()
    print(f"Testing IMAP inbox fetch for {addr}. Send an email with 'OpenAI' in the subject and a 6-digit code in the body to test.")
    code = email_manager.wait_for_verification_code()
    print(f"Processed Code: {code}")
