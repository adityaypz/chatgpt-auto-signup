from imapclient import IMAPClient
import mailparser
from colorama import Fore, Style
import config

if __name__ == "__main__":
    from colorama import init
    init()

    gmail_user = "hyungsikkim1@gmail.com"
    gmail_app_password = config.GMAIL_APP_PASSWORD

    print(f"Connecting to IMAP as {gmail_user}...")
    try:
        with IMAPClient("imap.gmail.com", ssl=True) as server:
            server.login(gmail_user, gmail_app_password)
            print(f"{Fore.GREEN}Login successful!{Style.RESET_ALL}")
            
            server.select_folder('INBOX')
            
            # Fetch the ALL unread emails to see what we missed
            messages = server.search(['UNSEEN'])
            print(f"Found {len(messages)} UNREAD messages.")
            
            for msgid, data in server.fetch(messages, 'RFC822').items():
                email_message = mailparser.parse_from_bytes(data[b'RFC822'])
                subject = email_message.subject
                sender = email_message.from_
                print(f"\n---")
                print(f"From: {sender}")
                print(f"Subject: {subject}")
                
                body = email_message.text_plain[0] if email_message.text_plain else "No plain text body"
                print(f"Body snippet: {body[:100]}...")

    except Exception as e:
         print(f"{Fore.RED}IMAP checking failed: {e}{Style.RESET_ALL}")
