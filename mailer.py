import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mailer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Email:
    """Represents a single email to be sent"""
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


@dataclass
class MailerConfig:
    """Configuration for the mailer"""
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    max_workers: int = 5
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    rate_limit_per_second: int = 10


class RateLimiter:
    """Simple rate limiter to control email sending rate"""
    
    def __init__(self, rate_per_second: int):
        self.rate_per_second = rate_per_second
        self.min_interval = 1.0 / rate_per_second
        self.last_call = 0
    
    def wait(self):
        """Wait if necessary to maintain rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class BulkMailer:
    """Send bulk emails with rate limiting and error handling"""
    
    def __init__(self, config: MailerConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_per_second)
        self.stats = {
            'total': 0,
            'sent': 0,
            'failed': 0,
            'retried': 0,
            'start_time': None,
            'end_time': None,
            'failed_emails': []
        }
    
    def _send_single_email(self, email: Email) -> Tuple[bool, str]:
        """
        Send a single email with retry logic
        Returns: (success: bool, message: str)
        """
        for attempt in range(self.config.retry_attempts):
            try:
                # Rate limit
                self.rate_limiter.wait()
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = email.subject
                msg['From'] = self.config.sender_email
                msg['To'] = email.to
                
                if email.cc:
                    msg['Cc'] = ', '.join(email.cc)
                
                # Attach body
                part1 = MIMEText(email.body, 'plain')
                msg.attach(part1)
                
                # Attach HTML body if provided
                if email.html_body:
                    part2 = MIMEText(email.html_body, 'html')
                    msg.attach(part2)
                
                # Send email
                with smtplib.SMTP_SSL(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=self.config.timeout
                ) as server:
                    server.login(self.config.sender_email, self.config.sender_password)
                    
                    recipients = [email.to]
                    if email.cc:
                        recipients.extend(email.cc)
                    if email.bcc:
                        recipients.extend(email.bcc)
                    
                    server.sendmail(
                        self.config.sender_email,
                        recipients,
                        msg.as_string()
                    )
                
                logger.info(f"✓ Email sent to {email.to}")
                return True, "Success"
            
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                return False, f"Authentication error: {e}"
            
            except smtplib.SMTPException as e:
                if attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"SMTP error for {email.to} (attempt {attempt + 1}/"
                        f"{self.config.retry_attempts}). Retrying in {wait_time}s: {e}"
                    )
                    self.stats['retried'] += 1
                    time.sleep(wait_time)
                else:
                    logger.error(f"✗ Failed to send to {email.to} after {self.config.retry_attempts} attempts: {e}")
                    return False, f"SMTP error: {e}"
            
            except Exception as e:
                logger.error(f"✗ Unexpected error sending to {email.to}: {e}")
                return False, f"Unexpected error: {e}"
        
        return False, "Max retries exceeded"
    
    def send_bulk(self, emails: List[Email], batch_size: int = 1000) -> Dict:
        """
        Send emails in batches with parallel processing
        
        Args:
            emails: List of Email objects to send
            batch_size: Number of emails to process before logging progress
        
        Returns:
            Dictionary with sending statistics
        """
        self.stats['total'] = len(emails)
        self.stats['start_time'] = datetime.now()
        
        logger.info(f"Starting to send {len(emails)} emails...")
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._send_single_email, email): email 
                for email in emails
            }
            
            completed = 0
            for future in as_completed(futures):
                email = futures[future]
                try:
                    success, message = future.result()
                    if success:
                        self.stats['sent'] += 1
                    else:
                        self.stats['failed'] += 1
                        self.stats['failed_emails'].append({
                            'to': email.to,
                            'subject': email.subject,
                            'error': message
                        })
                except Exception as e:
                    logger.error(f"Future exception for {email.to}: {e}")
                    self.stats['failed'] += 1
                    self.stats['failed_emails'].append({
                        'to': email.to,
                        'subject': email.subject,
                        'error': str(e)
                    })
                
                completed += 1
                if completed % batch_size == 0:
                    logger.info(f"Progress: {completed}/{len(emails)} emails processed")
        
        self.stats['end_time'] = datetime.now()
        self._log_summary()
        
        return self.stats
    
    def _log_summary(self):
        """Log summary statistics"""
        duration = self.stats['end_time'] - self.stats['start_time']
        success_rate = (self.stats['sent'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("SENDING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total emails: {self.stats['total']}")
        logger.info(f"Sent: {self.stats['sent']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Retried: {self.stats['retried']}")
        logger.info(f"Success rate: {success_rate:.2f}%")
        logger.info(f"Duration: {duration}")
        logger.info(f"Avg time per email: {duration.total_seconds() / max(self.stats['total'], 1):.2f}s")
        logger.info("=" * 60)
        
        if self.stats['failed_emails']:
            logger.warning(f"\nFailed to send {len(self.stats['failed_emails'])} emails:")
            for failed in self.stats['failed_emails'][:10]:  # Show first 10
                logger.warning(f"  - {failed['to']}: {failed['error']}")
            if len(self.stats['failed_emails']) > 10:
                logger.warning(f"  ... and {len(self.stats['failed_emails']) - 10} more")


def load_emails_from_csv(filepath: str) -> List[Email]:
    """Load emails from CSV file"""
    import csv
    
    emails = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = Email(
                    to=row['to'],
                    subject=row['subject'],
                    body=row['body'],
                    html_body=row.get('html_body'),
                    cc=row.get('cc', '').split(',') if row.get('cc') else None,
                    bcc=row.get('bcc', '').split(',') if row.get('bcc') else None
                )
                emails.append(email)
        logger.info(f"Loaded {len(emails)} emails from {filepath}")
        return emails
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []


# Example usage
if __name__ == "__main__":
    # Configuration
    config = MailerConfig(
        smtp_server="smtp.gmail.com",  # or your SMTP server
        smtp_port=465,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password",
        max_workers=10,
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        rate_limit_per_second=20
    )
    
    # Create mailer
    mailer = BulkMailer(config)
    
    # Example: Load emails from CSV
    # emails = load_emails_from_csv('emails.csv')
    
    # Example: Create emails programmatically
    emails = [
        Email(
            to=f"user{i}@example.com",
            subject=f"Test Email {i}",
            body=f"This is test email number {i}",
            html_body=f"<h1>Test Email {i}</h1><p>This is an HTML email.</p>"
        )
        for i in range(100)  # Change to 10000 for large batch
    ]
    
    # Send emails
    stats = mailer.send_bulk(emails, batch_size=500)
    
    # Print final statistics
    print(json.dumps(stats, indent=2, default=str))
