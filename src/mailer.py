import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import Config

def send_email_digest(html_content, text_content, subject="Daily AI News Digest", dry_run=False):
    """
    Sends the HTML & plain text email using Gmail SMTP and an App Password.
    If dry_run is True or credentials are not configured, it writes to a local preview file.
    """
    # Check for credentials
    has_credentials = bool(Config.GMAIL_ADDRESS and Config.GMAIL_APP_PASSWORD and Config.DIGEST_RECIPIENT)
    
    if dry_run or not has_credentials:
        preview_filename = "latest_digest_preview.html"
        try:
            with open(preview_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info("[Preview Saved] Email was not sent because dry_run=True or credentials are missing.")
            logging.info("You can view the styled HTML output by opening the file:")
            logging.info("  file:///%s", os.path.abspath(preview_filename).replace(os.sep, '/'))
            # Also print to console for immediate visibility
            print("\n[Preview Saved] Email was not sent because dry_run=True or credentials are missing.")
            print("You can view the styled HTML output by opening the file:")
            print(f"  file:///{os.path.abspath(preview_filename).replace(os.sep, '/')}")
            return True
        except Exception as e:
            logging.error("Failed to write local preview file: %s", e)
            return False

    print(f"Connecting to Gmail SMTP server for {Config.GMAIL_ADDRESS}...")
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = Config.GMAIL_ADDRESS
        msg['To'] = Config.DIGEST_RECIPIENT

        # Attach text and html parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Establish SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()  # Upgrade connection to secure TLS
        server.ehlo()
        
        # Login and send
        server.login(Config.GMAIL_ADDRESS, Config.GMAIL_APP_PASSWORD)
        server.sendmail(Config.GMAIL_ADDRESS, Config.DIGEST_RECIPIENT, msg.as_string())
        server.quit()
        
        logging.info("Successfully sent AI News Digest email to %s", Config.DIGEST_RECIPIENT)
        return True
        
    except Exception as e:
        logging.error("SMTP Error: Failed to send email digest: %s", e)
        # Fall back to writing local file so the run output isn't lost
        preview_filename = "latest_digest_preview_fallback.html"
        try:
            with open(preview_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[Fallback Saved] Wrote email body to {preview_filename} for review.")
        except Exception:
            pass
        return False

if __name__ == "__main__":
    print("Testing mailer module...")
    test_html = "<h1>Test Email</h1><p>If you see this, the template pipeline works!</p>"
    test_text = "Test Email: If you see this, the template pipeline works!"
    
    # Run test in dry_run mode by default
    send_email_digest(test_html, test_text, subject="Test AI News Digest", dry_run=True)
