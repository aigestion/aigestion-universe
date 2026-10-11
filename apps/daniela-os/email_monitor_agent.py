"""
Email Monitor Agent - aigestion-universe
Monitors Gmail inbox via IMAP, classifies emails, and provides summaries.
"""

import imaplib
import email
import json
import os
import time
import re
from email.header import decode_header
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    uid: str
    from_addr: str
    from_name: str
    subject: str
    date: str
    body_preview: str
    is_unread: bool
    classification: str = "normal"
    priority: int = 5
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


class EmailMonitorAgent:
    """Monitors Gmail inbox via IMAP and classifies incoming emails."""
    
    def __init__(self):
        self.imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        self.email_user = os.getenv("GMAIL_USER", "admin@aigestion.net")
        self.email_pass = os.getenv("GMAIL_PASS", "epts dela rkis gtmv")
        self.last_uid = 0
        self.mail = None
        
        # Classification rules
        self.urgent_keywords = [
            "urgent", "emergency", "critical", "security", "breach",
            "stolen", "fraud", "hack", "phishing", "compromise",
            "denuncia", "policia", "guardia civil", "juzgado",
            "deadlines", "expired", "suspended", "blocked"
        ]
        
        self.important_senders = [
            "guardiacivil.org", "policia.es", "juzgado",
            "tether.to", "circle.com", "opensea.io", "safepal",
            "binance.com", "coinbase.com", "kraken.com",
            "github.com", "gitlab.com",
            "google.com", "microsoft.com", "apple.com"
        ]
        
        self.newsletter_keywords = [
            "newsletter", "unsubscribe", "weekly digest", "monthly update",
            "promotional", "sale", "discount", "offer", "deal"
        ]
        
        logger.info(f"EmailMonitorAgent initialized for {self.email_user}")
    
    def connect(self) -> bool:
        """Establish IMAP connection."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            self.mail.login(self.email_user, self.email_pass)
            self.mail.select('INBOX')
            logger.info("Connected to IMAP server")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection."""
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None
    
    def classify_email(self, from_addr: str, subject: str, body: str) -> Tuple[str, int, List[str]]:
        """Classify email based on sender, subject, and body."""
        from_lower = from_addr.lower()
        subject_lower = subject.lower()
        body_lower = body.lower() if body else ""
        combined = f"{subject_lower} {body_lower}"
        
        labels = []
        priority = 5
        classification = "normal"
        
        # Check for urgent keywords
        if any(kw in combined for kw in self.urgent_keywords):
            classification = "urgent"
            priority = 9
            labels.append("urgent")
        
        # Check for important senders
        for sender in self.important_senders:
            if sender in from_lower:
                classification = "important"
                priority = max(priority, 8)
                labels.append(f"from:{sender}")
                break
        
        # Check for newsletters
        if any(kw in combined for kw in self.newsletter_keywords):
            classification = "newsletter"
            priority = 2
            labels.append("newsletter")
        
        # Check for security-related
        if any(kw in combined for kw in ["2fa", "password", "login", "verify", "confirm"]):
            if "security" not in labels:
                labels.append("security")
            priority = max(priority, 7)
        
        # Check for crypto-related
        if any(kw in combined for kw in ["wallet", "crypto", "ethereum", "bitcoin", "usdt", "usdc", "nft"]):
            labels.append("crypto")
            priority = max(priority, 6)
        
        return classification, priority, labels
    
    def fetch_emails(self, limit: int = 20, unread_only: bool = False) -> List[EmailMessage]:
        """Fetch emails from inbox."""
        if not self.connect():
            return []
        
        emails = []
        try:
            # Search
            if unread_only:
                status, data = self.mail.search(None, '(UNSEEN)')
            else:
                status, data = self.mail.search(None, 'ALL')
            
            if not data or not data[0]:
                return []
            
            ids = data[0].split()
            
            # Get last N emails
            fetch_ids = ids[-limit:] if len(ids) > limit else ids
            
            for num in fetch_ids:
                try:
                    status, msg_data = self.mail.fetch(num, '(BODY.PEEK[])')
                    if not msg_data or not msg_data[0]:
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Decode subject
                    subject_raw = decode_header(msg['Subject'])[0][0]
                    if isinstance(subject_raw, bytes):
                        subject = subject_raw.decode('utf-8', errors='ignore')
                    else:
                        subject = subject_raw or ""
                    
                    # Decode from
                    from_raw = decode_header(msg['From'])[0][0]
                    if isinstance(from_raw, bytes):
                        from_name = from_raw.decode('utf-8', errors='ignore')
                    else:
                        from_name = from_raw or ""
                    
                    # Extract email address
                    from_match = re.search(r'<([^>]+)>', from_name)
                    from_addr = from_match.group(1) if from_match else from_name
                    from_name_clean = from_name.split('<')[0].strip().strip('"')
                    
                    # Get body preview
                    body_preview = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body_preview = part.get_payload(decode=True).decode('utf-8', errors='ignore')[:500]
                                except Exception:
                                    pass
                                break
                    else:
                        try:
                            body_preview = msg.get_payload(decode=True).decode('utf-8', errors='ignore')[:500]
                        except Exception:
                            pass
                    
                    # Classify
                    classification, priority, labels = self.classify_email(
                        from_addr, subject, body_preview
                    )
                    
                    email_msg = EmailMessage(
                        uid=num.decode(),
                        from_addr=from_addr,
                        from_name=from_name_clean,
                        subject=subject,
                        date=msg['Date'] or "",
                        body_preview=body_preview,
                        is_unread=False,  # Would need FLAGS to determine
                        classification=classification,
                        priority=priority,
                        labels=labels
                    )
                    
                    emails.append(email_msg)
                    
                except Exception as e:
                    logger.warning(f"Error parsing email {num}: {e}")
                    continue
            
            # Sort by priority (highest first)
            emails.sort(key=lambda x: x.priority, reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        finally:
            self.disconnect()
        
        return emails
    
    def get_unread_summary(self, limit: int = 10) -> Dict:
        """Get summary of unread emails."""
        emails = self.fetch_emails(limit=limit, unread_only=True)
        
        urgent = [e for e in emails if e.classification == "urgent"]
        important = [e for e in emails if e.classification == "important"]
        normal = [e for e in emails if e.classification == "normal"]
        newsletters = [e for e in emails if e.classification == "newsletter"]
        
        return {
            "total_unread": len(emails),
            "urgent_count": len(urgent),
            "important_count": len(important),
            "normal_count": len(normal),
            "newsletter_count": len(newsletters),
            "urgent_emails": [asdict(e) for e in urgent[:5]],
            "important_emails": [asdict(e) for e in important[:5]],
            "recent_emails": [asdict(e) for e in emails[:10]]
        }
    
    def get_inbox_summary(self, limit: int = 20) -> Dict:
        """Get summary of recent inbox emails."""
        emails = self.fetch_emails(limit=limit)
        
        return {
            "total_fetched": len(emails),
            "emails": [asdict(e) for e in emails]
        }
    
    def monitor_loop(self, interval_seconds: int = 60):
        """Continuous monitoring loop."""
        logger.info(f"Starting email monitor loop (interval: {interval_seconds}s)")
        
        while True:
            try:
                summary = self.get_unread_summary(limit=10)
                
                if summary["urgent_count"] > 0:
                    logger.warning(f"URGENT: {summary['urgent_count']} urgent unread emails!")
                    for e in summary["urgent_emails"]:
                        logger.warning(f"  - {e['from_addr']}: {e['subject']}")
                
                logger.info(f"Inbox: {summary['total_unread']} unread "
                          f"({summary['urgent_count']} urgent, "
                          f"{summary['important_count']} important)")
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(interval_seconds)


def main():
    """CLI interface for email monitoring."""
    import sys
    
    agent = EmailMonitorAgent()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unread":
            summary = agent.get_unread_summary(limit=10)
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        
        elif command == "inbox":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            summary = agent.get_inbox_summary(limit=limit)
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        
        elif command == "monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            agent.monitor_loop(interval)
        
        else:
            print("Commands: unread, inbox [limit], monitor [interval]")
    
    else:
        # Default: show unread summary
        summary = agent.get_unread_summary(limit=10)
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
