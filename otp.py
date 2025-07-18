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
import time

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
            return 'outlook.office365.com'
        else:
            return 'imap.gmail.com'  # Default
    
    def connect(self) -> bool:
        """Establish connection to IMAP server"""
        try:
            print(f"Connecting to {self.server} with port {self.port} with username {self.username} and password {self.password}")
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
            
            # Method 1: Look for class="p1b" which contains the OTP in bold
            otp_element = soup.find('td', class_='p1b')
            if otp_element:
                text = otp_element.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    return text
            
            # Method 2: Look for specific class
            otp_element = soup.find('td', class_='p2b')
            if otp_element:
                text = otp_element.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    return text
            
            # Method 3: Look for elements that contain "verification code" and find nearby 4-digit numbers
            verification_elements = soup.find_all(string=re.compile(r'verification code', re.I))
            for element in verification_elements:
                # Look in the next few siblings for a 4-digit number
                if element.parent:
                    parent = element.parent
                    # Search in the parent's next siblings
                    for sibling in parent.find_next_siblings():
                        if sibling.name:
                            text = sibling.get_text(strip=True)
                            if text.isdigit() and len(text) == 4:
                                return text
                    
                    # Also search in the parent's parent structure
                    if parent.parent:
                        grandparent = parent.parent
                        for sibling in grandparent.find_next_siblings():
                            if sibling.name:
                                # Look for 4-digit numbers in this sibling
                                digit_elements = sibling.find_all(string=re.compile(r'\b\d{4}\b'))
                                for digit_element in digit_elements:
                                    text = digit_element.strip()
                                    if text.isdigit() and len(text) == 4:
                                        return text
            
            # Method 4: Look for bold text that contains 4 digits
            bold_elements = soup.find_all(['b', 'strong']) + soup.find_all('td', class_=re.compile(r'bold|p1b|p2b'))
            for element in bold_elements:
                text = element.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    return text
            
            # Method 5: Look in white boxes or specific background colors
            white_boxes = soup.find_all('td', style=re.compile(r'background-color:\s*#ffffff', re.I))
            for box in white_boxes:
                text = box.get_text(strip=True)
                if text.isdigit() and len(text) == 4:
                    return text
                # Also check for patterns within the box
                for pattern in self.OTP_PATTERNS:
                    match = re.search(pattern, str(box))
                    if match:
                        code = match.group(1) if match.lastindex else match.group(0)
                        if code.isdigit() and len(code) == 4:
                            return code
            
            # Method 6: General text search for 4-digit numbers
            text_content = soup.get_text()
            four_digit_numbers = re.findall(r'\b\d{4}\b', text_content)
            for number in four_digit_numbers:
                # Filter out common non-OTP 4-digit numbers
                if number not in ['2024', '2025', '2023', '2022', '1999', '2000']:
                    return number
            
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
                time.sleep(2)
            
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
                            print(f"Found OTP in HTML: {otp}")
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
                                    print(f"Found OTP in plain text: {code}")
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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.get_otp_from_email,
            email_client,
            target_email,
            service,
            timeout
        )



#SAMPLE(used for testing, do not run this otp.py file directly unless u wanna test too)
async def main():
    otp_extractor = EmailOTPExtractor()
    otp = await otp_extractor.get_otp_async(
        IMAPClient(
            'email@gmail.com',
            'app password here',
            'imap.gmail.com'
        ),
        'email@gmail.com'
    )
    print(f"Final OTP: {otp}")

if __name__ == "__main__":
    asyncio.run(main())