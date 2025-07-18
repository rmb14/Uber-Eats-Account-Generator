"""
OTP (One-Time Password) Extraction for Email Verification

"""

import imaplib
import email
import re
import asyncio
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from email.message import Message
import logging
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailParsingError(Exception):
    """Custom exception for email parsing errors. TODO"""
    pass


class IMAPClient:
    """Handles IMAP email server connections"""
    
    DEFAULT_PORTS = {
        'imap.gmail.com': 993,
        'imap.zmailservice.com': 993,
        'outlook.office365.com': 993
    }
    
    def __init__(self, username: str, password: str, server: str = None):
        self.username = username
        self.password = password
        self.server = self._determine_server(username, server)
        self.port = self.DEFAULT_PORTS.get(self.server, 993)
        self.connection = None
    
    def _determine_server(self, username: str, server: str = None) -> str:
        """Determine IMAP server based on email domain"""
        if server:
            return server
        
        if '@gmail.com' in username:
            return 'imap.gmail.com'
        elif '@hotmail.com' in username or '@outlook.com' in username:
            return 'imap.zmailservice.com'
        else:
            return 'imap.gmail.com'  # Default
    
    def connect(self) -> bool:
        """Establish connection to IMAP server"""
        try:
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            self.connection.login(self.username, self.password)
            logger.info(f"Successfully connected to {self.server}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("Disconnected from IMAP server")
            except:
                pass
    
    def search_emails(self, criteria: List[Tuple[str, str]], folder: str = 'inbox') -> List[bytes]:
        """Search emails based on criteria"""
        if not self.connection:
            raise EmailParsingError("Not connected to IMAP server")
        
        try:
            self.connection.select(folder)
            
            # Build search criteria
            search_args = ['HEADER'] + [item for pair in criteria for item in pair]
            
            status, data = self.connection.search(None, *search_args)
            
            if status == 'OK' and data[0]:
                return data[0].split()
            return []
            
        except Exception as e:
            logger.error(f"Email search failed: {e}")
            return []
    
    def fetch_email(self, email_id: bytes) -> Optional[Message]:
        """Fetch email by ID"""
        if not self.connection:
            raise EmailParsingError("Not connected to IMAP server")
        
        try:
            status, data = self.connection.fetch(email_id, '(RFC822)')
            
            if status == 'OK' and data[0]:
                return email.message_from_bytes(data[0][1])
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch email: {e}")
            return None


class OTPExtractor:
    """Base class for OTP extraction strategies"""
    
    def extract(self, content: str) -> Optional[str]:
        """Extract OTP from content"""
        raise NotImplementedError


class UberOTPExtractor(OTPExtractor):
    """Extracts OTP from Uber emails"""
    
    OTP_PATTERNS = [
        r'\b\d{4}\b',  # 4-digit code
        r'verification code[:\s]+(\d{4})',
        r'code[:\s]+(\d{4})',
        r'>\s*(\d{4})\s*<'
    ]
    
    def extract(self, html_content: str) -> Optional[str]:
        """Extract OTP from Uber email HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for specific class
            otp_element = soup.find('td', class_='p2b')
            if otp_element:
                text = otp_element.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    return text
            
            # Method 2: Search for verification text
            verification_text = soup.find(string=re.compile(r'verification code', re.I))
            if verification_text:
                parent = verification_text.parent
                if parent:
                    for sibling in parent.find_next_siblings():
                        if sibling.name:
                            text = sibling.get_text(strip=True)
                            if text.isdigit() and len(text) == 4:
                                return text
            
            # Method 3: Look in white boxes
            white_boxes = soup.find_all('td', style=re.compile(r'background-color:\s*#ffffff', re.I))
            for box in white_boxes:
                for pattern in self.OTP_PATTERNS:
                    match = re.search(pattern, str(box))
                    if match:
                        code = match.group(1) if match.lastindex else match.group(0)
                        if code.isdigit() and len(code) == 4:
                            return code
            
            # Method 4: General text search
            text_content = soup.get_text()
            for pattern in self.OTP_PATTERNS:
                matches = re.findall(pattern, text_content, re.I)
                for match in matches:
                    if isinstance(match, str) and match.isdigit() and len(match) == 4:
                        return match
            
            return None
            
        except Exception as e:
            logger.error(f"OTP extraction failed: {e}")
            return None


class EmailOTPExtractor:
    def __init__(self):
        self.extractors = {
            'uber': UberOTPExtractor(),
            'default': UberOTPExtractor()  # Use Uber extractor as default
        }
    
    def get_otp_from_email(
        self,
        email_client: IMAPClient,
        target_email: str,
        service: str = 'uber',
        timeout: int = 60
    ) -> Optional[str]:
        """
        Extract OTP from email
        
        Args:
            email_client: IMAP client instance
            target_email: Email address to search for
            service: Service type for specific extraction
            timeout: Maximum time to wait for email
        
        Returns:
            OTP code if found, None otherwise
        """
        if not email_client.connect():
            logger.error("Failed to connect to email server")
            return None
        
        try:
            start_time = datetime.now()
            extractor = self.extractors.get(service, self.extractors['default'])
            
            while (datetime.now() - start_time).seconds < timeout:
                # Search for emails to target address
                email_ids = email_client.search_emails([('To', target_email)])
                
                if email_ids:
                    # Get the latest email
                    latest_email_id = email_ids[-1]
                    msg = email_client.fetch_email(latest_email_id)
                    
                    if msg:
                        otp = self._extract_otp_from_message(msg, extractor)
                        if otp:
                            logger.info(f"Successfully extracted OTP: {otp}")
                            return otp
                
                # Wait before checking again
                asyncio.sleep(2)
            
            logger.warning(f"Timeout waiting for OTP email")
            return None
            
        except Exception as e:
            logger.error(f"Error getting OTP: {e}")
            return None
        finally:
            email_client.disconnect()
    
    def _extract_otp_from_message(
        self,
        msg: Message,
        extractor: OTPExtractor
    ) -> Optional[str]:
        """Extract OTP from email message"""
        try:
            # Process all parts of the email
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/html':
                    html_content = part.get_payload(decode=True)
                    if html_content:
                        html_str = html_content.decode('utf-8', errors='ignore')
                        otp = extractor.extract(html_str)
                        if otp:
                            return otp
                
                elif content_type == 'text/plain':
                    text_content = part.get_payload(decode=True)
                    if text_content:
                        text_str = text_content.decode('utf-8', errors='ignore')
                        # Try to extract from plain text
                        for pattern in UberOTPExtractor.OTP_PATTERNS:
                            match = re.search(pattern, text_str)
                            if match:
                                code = match.group(1) if match.lastindex else match.group(0)
                                if code.isdigit() and len(code) == 4:
                                    return code
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract OTP from message: {e}")
            return None
    
    async def get_otp_async(
        self,
        email_client: IMAPClient,
        target_email: str,
        service: str = 'uber',
        timeout: int = 60
    ) -> Optional[str]:
        """Async wrapper for OTP extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.get_otp_from_email,
            email_client,
            target_email,
            service,
            timeout
        )


class SecureOTPHandler:
    def __init__(self):
        self.rate_limiter = {}
        self.max_attempts = 3
        self.cooldown_period = 300  # 5 minutes
    
    def validate_otp_request(self, email: str) -> bool:
        """Check if OTP request is within rate limits"""
        current_time = datetime.now()
        
        if email in self.rate_limiter:
            last_attempt, attempts = self.rate_limiter[email]
            
            # Check cooldown
            if (current_time - last_attempt).seconds < self.cooldown_period:
                if attempts >= self.max_attempts:
                    logger.warning(f"Rate limit exceeded for {email}")
                    return False
            else:
                # Reset after cooldown
                self.rate_limiter[email] = (current_time, 1)
                return True
            
            # Update attempts
            self.rate_limiter[email] = (current_time, attempts + 1)
            return attempts < self.max_attempts
        else:
            # First attempt
            self.rate_limiter[email] = (current_time, 1)
            return True
    
    def generate_secure_otp(self, length: int = 6) -> str:
        """Generate cryptographically secure OTP"""
        import secrets
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    def hash_otp(self, otp: str) -> str:
        """Hash OTP for storage"""
        import hashlib
        return hashlib.sha256(otp.encode()).hexdigest()


# Legacy function for backwards compatibility
def get_otp_from_email(username: str, password: str, target_email: str) -> Optional[str]:
    client = IMAPClient(username, password)
    extractor = EmailOTPExtractor()
    
    return extractor.get_otp_from_email(client, target_email)


def extract_otp_from_uber_email(html_content: str) -> Optional[str]:
    extractor = UberOTPExtractor()
    return extractor.extract(html_content)
