from mailer import BulkMailer, MailerConfig, load_emails_from_csv, Email
import sys

def send_from_csv(csv_file: str):
    """Send emails from a CSV file"""
    
    # Configure your SMTP
    config = MailerConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password",
        max_workers=20,
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        rate_limit_per_second=50
    )
    
    # Create mailer instance
    mailer = BulkMailer(config)
    
    # Load emails from CSV
    emails = load_emails_from_csv(csv_file)
    
    if not emails:
        print("No emails to send!")
        return
    
    # Send all emails
    print(f"\n{'='*60}")
    print(f"Starting to send {len(emails)} emails...")
    print(f"{'='*60}\n")
    
    stats = mailer.send_bulk(emails, batch_size=500)
    
    # Print results
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total: {stats['total']}")
    print(f"Sent: {stats['sent']}")
    print(f"Failed: {stats['failed']}")
    print(f"Retried: {stats['retried']}")
    if stats['total'] > 0:
        success_rate = (stats['sent'] / stats['total'] * 100)
        print(f"Success Rate: {success_rate:.2f}%")
    print(f"Duration: {stats['end_time'] - stats['start_time']}")
    print(f"{'='*60}\n")
    
    if stats['failed_emails']:
        print("Failed emails (first 20):")
        for failed in stats['failed_emails'][:20]:
            print(f"  - {failed['to']}: {failed['error']}")
        if len(stats['failed_emails']) > 20:
            print(f"  ... and {len(stats['failed_emails']) - 20} more")


def send_test_emails(num_emails: int = 10):
    """Send test emails to verify setup"""
    
    config = MailerConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password",
        max_workers=5,
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        rate_limit_per_second=10
    )
    
    mailer = BulkMailer(config)
    
    # Create test emails
    emails = [
        Email(
            to=f"test{i}@example.com",
            subject=f"Test Email {i}",
            body=f"This is test email number {i}\n\nIf you received this, the mailer is working!",
            html_body=f"""
            <html>
                <body>
                    <h1>Test Email {i}</h1>
                    <p>This is an HTML test email.</p>
                    <p>If you received this, the mailer is working!</p>
                </body>
            </html>
            """
        )
        for i in range(num_emails)
    ]
    
    print(f"\n{'='*60}")
    print(f"Sending {num_emails} test emails...")
    print(f"{'='*60}\n")
    
    stats = mailer.send_bulk(emails, batch_size=100)
    
    print(f"\n{'='*60}")
    print("TEST RESULTS")
    print(f"{'='*60}")
    print(f"Sent: {stats['sent']}/{stats['total']}")
    print(f"Failed: {stats['failed']}")
    if stats['total'] > 0:
        success_rate = (stats['sent'] / stats['total'] * 100)
        print(f"Success Rate: {success_rate:.2f}%")
    print(f"{'='*60}\n")


def send_bulk_10k(csv_file: str):
    """Send 10,000 emails optimized for bulk sending"""
    
    config = MailerConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password",
        max_workers=25,
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        rate_limit_per_second=50
    )
    
    mailer = BulkMailer(config)
    emails = load_emails_from_csv(csv_file)
    
    if not emails:
        print("No emails to send!")
        return
    
    print(f"\n{'='*60}")
    print(f"Starting BULK SEND of {len(emails)} emails...")
    print(f"This may take a while. Check mailer.log for progress.")
    print(f"{'='*60}\n")
    
    stats = mailer.send_bulk(emails, batch_size=1000)
    
    print(f"\n{'='*60}")
    print("BULK SEND COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {stats['total']}")
    print(f"Sent: {stats['sent']}")
    print(f"Failed: {stats['failed']}")
    print(f"Retried: {stats['retried']}")
    if stats['total'] > 0:
        success_rate = (stats['sent'] / stats['total'] * 100)
        print(f"Success Rate: {success_rate:.2f}%")
    print(f"Duration: {stats['end_time'] - stats['start_time']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send emails using the bulk mailer")
    parser.add_argument(
        "--mode",
        choices=["test", "csv", "bulk"],
        default="test",
        help="Mode: test (send 10 test emails), csv (send from CSV), bulk (send 10k from CSV)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file containing emails"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of test emails to send (only for test mode)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "test":
        send_test_emails(args.count)
    elif args.mode == "csv":
        if not args.csv:
            print("Error: --csv argument required for csv mode")
            sys.exit(1)
        send_from_csv(args.csv)
    elif args.mode == "bulk":
        if not args.csv:
            print("Error: --csv argument required for bulk mode")
            sys.exit(1)
        send_bulk_10k(args.csv)
