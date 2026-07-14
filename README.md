# 📧 Bulk Email Mailer - Send 10,000+ Emails

A production-ready Python bulk email mailer with rate limiting, retry logic, parallel processing, and comprehensive error handling.

## ✨ Features

- ✅ Send up to **10,000+ emails** efficiently
- ✅ **Rate limiting** to avoid being blocked
- ✅ **Automatic retries** with exponential backoff
- ✅ **Parallel processing** with ThreadPoolExecutor
- ✅ Support for **plain text and HTML emails**
- ✅ **CC/BCC support**
- ✅ **CSV import** for bulk recipient lists
- ✅ **Detailed logging** with progress tracking
- ✅ **Error handling & reporting**
- ✅ **Statistics & success metrics**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Email Credentials

#### Gmail Setup (Recommended)

1. Enable 2-factor authentication: https://myaccount.google.com/security
2. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

3. Update `send_emails.py` with your credentials:
```python
sender_email="your-email@gmail.com"
sender_password="your-16-char-app-password"
```

#### Other Email Providers

| Provider | SMTP Server | Port |
|----------|-------------|------|
| Gmail | smtp.gmail.com | 465 |
| Outlook | smtp-mail.outlook.com | 587 |
| SendGrid | smtp.sendgrid.net | 587 |
| Mailgun | smtp.mailgun.org | 587 |

### 3. Prepare Your Email List

Create or edit `emails.csv`:

```csv
to,subject,body,html_body,cc,bcc
user1@example.com,Hello,Welcome!,<h1>Welcome</h1>,,
user2@example.com,Hello,Welcome!,<h1>Welcome</h1>,,
```

**CSV Columns:**
- `to` (required) - Recipient email
- `subject` (required) - Email subject
- `body` (required) - Plain text body
- `html_body` (optional) - HTML version
- `cc` (optional) - Comma-separated CC emails
- `bcc` (optional) - Comma-separated BCC emails

## 📝 Usage Examples

### Test Mode (Send 10 Test Emails)

```bash
python send_emails.py --mode test --count 10
```

### Send from CSV

```bash
python send_emails.py --mode csv --csv emails.csv
```

### Bulk Send (10,000+ Emails)

```bash
python send_emails.py --mode bulk --csv emails_10k.csv
```

## 🔧 Configuration

Edit `send_emails.py` to adjust settings:

```python
config = MailerConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=465,
    sender_email="your-email@gmail.com",
    sender_password="your-app-password",
    max_workers=20,              # Concurrent threads (10-30 recommended)
    timeout=30,                  # Connection timeout in seconds
    retry_attempts=3,            # Number of retry attempts
    retry_delay=5,               # Initial retry delay in seconds
    rate_limit_per_second=50     # Emails per second (adjust based on provider)
)
```

### Rate Limiting Guidelines

| Provider | Recommended Rate | Notes |
|----------|------------------|-------|
| Gmail | 20-50/sec | May throttle if too fast |
| SendGrid | 100+/sec | Higher limits |
| Mailgun | 100+/sec | Higher limits |
| Standard SMTP | 10-20/sec | Conservative approach |

## 📊 Monitoring

### Real-time Logging

```bash
tail -f mailer.log
```

### Sample Output

```
2026-07-14 14:00:01 - INFO - Starting to send 10000 emails...
2026-07-14 14:00:05 - INFO - ✓ Email sent to user1@example.com
2026-07-14 14:00:10 - INFO - Progress: 1000/10000 emails processed
2026-07-14 14:05:30 - INFO - ============================================================
2026-07-14 14:05:30 - INFO - SENDING SUMMARY
2026-07-14 14:05:30 - INFO - Total emails: 10000
2026-07-14 14:05:30 - INFO - Sent: 9850
2026-07-14 14:05:30 - INFO - Failed: 150
2026-07-14 14:05:30 - INFO - Success rate: 98.50%
2026-07-14 14:05:30 - INFO - Duration: 0:05:29
```

## 📂 Project Structure

```
zukoks/
├── mailer.py              # Core mailer class
├── send_emails.py         # Command-line interface
├── emails.csv             # Sample recipient list
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── mailer.log            # Log file (created after first run)
```

## 🔐 Security Tips

⚠️ **Never commit your credentials!**

1. Use environment variables:
```python
import os
sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')
```

2. Create a `.env` file (add to `.gitignore`):
```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

3. Load with python-dotenv:
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

## 🐛 Troubleshooting

### "Authentication failed"
- Verify email and password are correct
- For Gmail: Use App Password, not regular password
- Ensure 2FA is enabled on Gmail

### "Connection timeout"
- Check internet connection
- SMTP server might be down
- Try increasing `timeout` value

### "Emails not being sent"
- Check `mailer.log` for errors
- Verify CSV format is correct
- Test with `--mode test` first

### "Too many failures"
- Reduce `max_workers` value
- Reduce `rate_limit_per_second`
- Increase `retry_delay`
- Check email provider limits

## 📈 Performance Tips

For maximum performance with 10,000 emails:

1. **Increase workers** (but not too much):
   ```python
   max_workers=25  # Good balance
   ```

2. **Optimize rate limit** based on provider:
   ```python
   rate_limit_per_second=100  # For premium providers
   ```

3. **Use batching**:
   ```python
   mailer.send_bulk(emails, batch_size=1000)
   ```

4. **Run on a server** with good internet connection

5. **Monitor CPU and memory** usage

## 📜 Examples

### Generate 10,000 test emails programmatically

```python
from mailer import Email, BulkMailer, MailerConfig

# Create 10,000 emails
emails = [
    Email(
        to=f"user{i}@example.com",
        subject=f"Welcome {i}",
        body=f"Hello user {i}!",
        html_body=f"<h1>Welcome {i}</h1>"
    )
    for i in range(10000)
]

config = MailerConfig(...)
mailer = BulkMailer(config)
stats = mailer.send_bulk(emails)
```

### Send with CC and BCC

```python
email = Email(
    to="user@example.com",
    subject="Meeting",
    body="See you tomorrow",
    cc=["manager@example.com"],
    bcc=["archive@example.com"]
)
```

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Found a bug or want to improve? Create an issue or pull request!

## 📞 Support

For issues or questions, check the logs first with:
```bash
tail -f mailer.log
```

---

**Happy emailing! 🚀**
