from email.header import decode_header
import imaplib
import email
from bs4 import BeautifulSoup
import ollama
import os
from dotenv import load_dotenv

load_dotenv()

# Email credentials
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"  

# Define marketing keywords
MARKETING_KEYWORDS = [
    "sale", "discount", "offer", "promo", "deal", "save", "subscribe", "limited time",
    "exclusive", "special offer", "coupon", "clearance", "newsletter", "free shipping"
    "unsubscribe",
]

# Determine if an email is marketing based on subject and sender.
def is_marketing_email(subject, sender, content):
    combined_text = f"{subject.lower()} {sender.lower()} {content.lower()}"
    return any(keyword in combined_text for keyword in MARKETING_KEYWORDS)\

def decode_subject(subject):
    if subject is None:
        return "(No Subject)"
    
    decoded_parts = decode_header(subject)
    
    # Process each part (some emails have multiple encoded parts)
    decoded_subject = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):  # If encoded, decode it
            decoded_subject.append(part.decode(encoding or "utf-8"))
        else:
            decoded_subject.append(part)  # If already a string, keep it

    return "".join(decoded_subject)

def fetch_marketing_emails():
    # Connect to email server
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    # Search for marketing emails (customize this filter)
    result, data = mail.search(None, 'ALL')  # Change to 'UNSEEN' for new emails only
    email_ids = data[0].split()[::-1]

    summaries = []
    
    for email_id in email_ids[:10]:  # Limit to 10 for performance
        result, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_subject(msg["subject"])
                sender = msg["from"]
                
                # Extract email content
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            html_content = part.get_payload(decode=True).decode("utf-8")
                            text_content = BeautifulSoup(html_content, "html.parser").get_text()
                            break
                else:
                    text_content = msg.get_payload(decode=True).decode("utf-8")
                
                # Check if it's a marketing email
                if not is_marketing_email(subject, sender, text_content):
                    continue  # Skip non-marketing emails

                # Summarize with Ollama
                response = ollama.chat(model="mistral", messages=[{"role": "user", "content": f"Create a brief summary of the email contents:\n{text_content}"}])
                summary = response["message"]["content"]

                summaries.append(f"📩 **{subject}** from {sender}\n{summary}\n")

    mail.logout()
    return "\n".join(summaries)

# Run the script
if __name__ == "__main__":
    print(fetch_marketing_emails())


