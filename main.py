"""
Uber Eats Account Generator

WARNING: This code is for educational purposes only. 
Do not use for actual account creation or unauthorized activities.
"""

import json
import uuid
import random
import asyncio
import time
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pathlib import Path

from curl_cffi import requests
from colorama import Fore, init

from otp import EmailOTPExtractor, IMAPClient

# Initialize colorama for cross-platform colored output
init(autoreset=True)


@dataclass
class DeviceInfo:
    """Device Info that we store and send to Uber to represent a real Device"""
    env_id: str
    device_name: str
    version: str
    device_os_name: str
    rooted: bool
    location_service_enabled: bool
    device_os_version: str
    battery_status: str
    env_checksum: str
    device_ids: Dict[str, str]
    ip_address: str
    source_app: str
    battery_level: float
    epoch: float
    device_model: str
    lib_count: int
    wifi_connected: bool
    cpu_abi: str
    version_checksum: str


class DeviceSpoofer:
    """Generates realistic spoofed device info to appear as a real phone"""
    
    DEVICE_MODELS = ["iPhone8,4", "iPhone10,3", "iPhone12,5", "iPhone13,2", "iPhone14,6"]
    BATTERY_STATUSES = ["full", "charging", "discharging"]
    
    @classmethod
    def generate_device_info(cls) -> DeviceInfo:
        """Generate randomized device information"""
        return DeviceInfo(
            env_id=uuid.uuid4().hex,
            device_name="iPhone",
            version=f"6.{random.randint(100, 999)}.{random.randint(10000, 99999)}",
            device_os_name="iOS",
            rooted=False,
            location_service_enabled=False,
            device_os_version=f"{random.randint(13, 17)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            battery_status=random.choice(cls.BATTERY_STATUSES),
            env_checksum=uuid.uuid4().hex,
            device_ids={
                "advertiserId": str(uuid.uuid4()),
                "uberId": str(uuid.uuid4()).upper(),
                "perfId": str(uuid.uuid4()).upper(),
                "vendorId": str(uuid.uuid4()).upper()
            },
            ip_address=f"{random.randint(10, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            source_app="eats",
            battery_level=round(random.uniform(0.5, 1.0), 2),
            epoch=time.time() * 1000,
            device_model=random.choice(cls.DEVICE_MODELS),
            lib_count=random.randint(600, 1000),
            wifi_connected=True,
            cpu_abi=f"{random.randint(10000000, 20000000)}-{random.randint(0, 1)}",
            version_checksum=str(uuid.uuid4()).upper()
        )


class RequestHandler:
    """Handles HTTP requests with proxy support"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.proxy = config.get('proxy')
        self.proxies = {
            'http': self.proxy,
            'https': self.proxy
        } if self.proxy else None
    
    async def post(self, name: str, url: str, headers: Dict, data: Dict) -> Optional[requests.Response]:
        """Make POST request with error handling"""
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=data, 
                proxies=self.proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f'{Fore.GREEN}[✓] {name} request successful')
                return response
            else:
                print(f'{Fore.RED}[✗] {name} failed: {response.status_code}')
                print(f'    Response: {response.text[:200]}...')
                return None
                
        except Exception as e:
            print(f"{Fore.RED}[!] Request error in {name}: {e}")
            return None


class AccountGenerator:
    """Main class for account generation workflow"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.request_handler = RequestHandler(self.config)
        self.device_info = DeviceSpoofer.generate_device_info()
        self.first_names = self.config.get('first_names', [])
        self.last_names = self.config.get('last_names', [])
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Fore.YELLOW}[!] Config file not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "proxy": None,
            "endpoints": {
                "submit_form": "https://auth.uber.com/v2/submit-form",
                "submit_form_geo": "https://cn-geo1.uber.com/rt/silk-screen/submit-form"
            },
            "first_names": ["James", "Mary", "John", "Patricia"],
            "last_names": ["Smith", "Johnson", "Williams", "Brown"]
        }
    
    def generate_user_info(self, domain: str) -> Tuple[str, str]:
        """Generate random user information"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}@{domain}"
        return email, name
    
    def _get_headers(self, variant: str = "standard") -> Dict:
        """Get request headers based on variant"""
        base_headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-Uber-Client-Name": "eats",
            "X-Uber-App-Variant": "ubereats",
            "X-Uber-Client-Id": "com.ubercab.UberEats",
            "X-Uber-Device": "iphone",
        }
        
        if variant == "standard":
            base_headers.update({
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
                "X-Uber-Client-Version": "6.129.10001",
            })
        
        return base_headers
    
    async def email_signup(self, email: str) -> Optional[str]:
        """Initiate email signup process"""
        data = {
            "formContainerAnswer": {
                "inAuthSessionID": "",
                "formAnswer": {
                    "flowType": "INITIAL",
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "codeChallenge": "XQt42Ii1O9Qzg69ULyVHcQs8uvhvIznGQniUsVI-mEA",
                    "firstPartyClientID": "S_Fwp1YMY1qAlAf5-yfYbeb7cfJE-50z",
                    "screenAnswers": [{
                        "screenType": "PHONE_NUMBER_INITIAL",
                        "eventType": "TypeInputEmail",
                        "fieldAnswers": [{
                            "fieldType": "EMAIL_ADDRESS",
                            "emailAddress": email
                        }]
                    }]
                }
            }
        }
        
        response = await self.request_handler.post(
            "Email Signup",
            self.config['endpoints']['submit_form'],
            self._get_headers(),
            data
        )
        
        if response:
            return response.json().get('inAuthSessionID')
        return None
    
    async def submit_otp(self, session_id: str, otp: str) -> Optional[str]:
        """Submit OTP verification code"""
        data = {
            "formContainerAnswer": {
                "inAuthSessionID": session_id,
                "formAnswer": {
                    "flowType": "SIGN_UP",
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "screenAnswers": [{
                        "screenType": "EMAIL_OTP_CODE",
                        "eventType": "TypeEmailOTP",
                        "fieldAnswers": [{
                            "fieldType": "EMAIL_OTP_CODE",
                            "emailOTPCode": otp
                        }]
                    }]
                }
            }
        }
        
        response = await self.request_handler.post(
            "Submit OTP",
            self.config['endpoints']['submit_form_geo'],
            self._get_headers(),
            data
        )
        
        if response:
            return response.json().get('inAuthSessionID')
        return None
    
    async def complete_registration(self, email: str, name: str, session_id: str) -> bool:
        """Complete the registration process"""
        # Skip submit
        session_id = await self._skip_submit(session_id)
        if not session_id:
            return False
        
        # Submit name
        session_id = await self._submit_name(session_id, name)
        if not session_id:
            return False
        
        # Legal confirmation
        session_id, auth_code = await self._submit_legal_confirmation(session_id)
        if not session_id or not auth_code:
            return False
        
        # Final auth code submission
        await self._submit_auth_code(session_id, auth_code)
        
        return True
    
    async def _skip_submit(self, session_id: str) -> Optional[str]:
        """Skip optional registration step"""
        data = {
            "formContainerAnswer": {
                "inAuthSessionID": session_id,
                "formAnswer": {
                    "flowType": "PROGRESSIVE_SIGN_UP",
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "screenAnswers": [{
                        "screenType": "SKIP",
                        "eventType": "TypeSkip",
                        "fieldAnswers": []
                    }]
                }
            }
        }
        
        response = await self.request_handler.post(
            "Skip Submit",
            self.config['endpoints']['submit_form_geo'],
            self._get_headers("mobile"),
            data
        )
        
        if response:
            return response.json().get('inAuthSessionID')
        return None
    
    async def _submit_name(self, session_id: str, name: str) -> Optional[str]:
        """Submit user name information"""
        first_name, last_name = name.split(' ', 1)
        
        data = {
            "formContainerAnswer": {
                "inAuthSessionID": session_id,
                "formAnswer": {
                    "flowType": "PROGRESSIVE_SIGN_UP",
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "screenAnswers": [{
                        "screenType": "FULL_NAME_PROGRESSIVE",
                        "eventType": "TypeInputNewUserFullName",
                        "fieldAnswers": [
                            {
                                "fieldType": "FIRST_NAME",
                                "firstName": first_name
                            },
                            {
                                "fieldType": "LAST_NAME",
                                "lastName": last_name
                            }
                        ]
                    }]
                }
            }
        }
        
        response = await self.request_handler.post(
            "Submit Name",
            self.config['endpoints']['submit_form_geo'],
            self._get_headers("mobile"),
            data
        )
        
        if response:
            return response.json().get('inAuthSessionID')
        return None
    
    async def _submit_legal_confirmation(self, session_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Submit legal confirmation"""
        data = {
            "formContainerAnswer": {
                "inAuthSessionID": session_id,
                "formAnswer": {
                    "flowType": "SIGN_UP",
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "screenAnswers": [{
                        "screenType": "LEGAL",
                        "eventType": "TypeSignupLegal",
                        "fieldAnswers": [
                            {
                                "fieldType": "LEGAL_CONFIRMATION",
                                "legalConfirmation": True
                            },
                            {
                                "fieldType": "LEGAL_CONFIRMATIONS",
                                "legalConfirmations": {
                                    "legalConfirmations": [{
                                        "isAccepted": True
                                    }]
                                }
                            }
                        ]
                    }]
                }
            }
        }
        
        response = await self.request_handler.post(
            "Submit Legal",
            self.config['endpoints']['submit_form_geo'],
            self._get_headers("mobile"),
            data
        )
        
        if response:
            resp_json = response.json()
            try:
                fields = resp_json.get('form', {}).get('screens', [{}])[0].get('fields', [])
                auth_code = fields[0].get('authCode') if fields else None
                session_id = resp_json.get('inAuthSessionID')
                return session_id, auth_code
            except (IndexError, KeyError):
                print(f"{Fore.RED}[!] Failed to extract auth code")
                return None, None
        
        return None, None
    
    async def _submit_auth_code(self, session_id: str, auth_code: str) -> bool:
        """Submit final authentication code"""
        data = {
            "formContainerAnswer": {
                "formAnswer": {
                    "screenAnswers": [{
                        "fieldAnswers": [
                            {
                                "sessionVerificationCode": auth_code,
                                "fieldType": "SESSION_VERIFICATION_CODE"
                            },
                            {
                                "codeVerifier": "zZlmodq2L3ly2tJu6GqOa7Yx7AjJpx3TpiXWFfhUDsZ1QSgTObHzgKn5IBLDxtQBd6Gpj8z1BZki6SwEIg2WRg--",
                                "fieldType": "CODE_VERIFIER"
                            }
                        ],
                        "eventType": "TypeVerifySession",
                        "screenType": "SESSION_VERIFICATION"
                    }],
                    "standardFlow": True,
                    "deviceData": json.dumps(asdict(self.device_info)),
                    "firstPartyClientID": "S_Fwp1YMY1qAlAf5-yfYbeb7cfJE-50z",
                    "flowType": "SIGN_IN"
                },
                "inAuthSessionID": f"{session_id}.{auth_code}"
            }
        }
        
        response = await self.request_handler.post(
            "Submit Auth Code",
            self.config['endpoints']['submit_form_geo'],
            self._get_headers("mobile"),
            data
        )
        
        return response is not None
    
    async def create_account(self, domain: str, email_client: IMAPClient) -> Optional[str]:
        """Main account creation workflow"""
        email, name = self.generate_user_info(domain)
        print(f"\n{Fore.CYAN}[*] Creating account for: {email}")
        
        # Start signup
        session_id = await self.email_signup(email)
        if not session_id:
            print(f"{Fore.RED}[!] Failed to initiate signup")
            return None
        
        # Get OTP
        print(f"{Fore.YELLOW}[*] Waiting for OTP...")
        await asyncio.sleep(5)  # Wait for email
        
        otp_extractor = EmailOTPExtractor()
        otp = await otp_extractor.get_otp_async(email_client, email)
        
        if not otp:
            print(f"{Fore.RED}[!] Failed to retrieve OTP")
            return None
        
        print(f"{Fore.GREEN}[✓] OTP received: {otp}")
        
        # Submit OTP
        session_id = await self.submit_otp(session_id, otp)
        if not session_id:
            print(f"{Fore.RED}[!] Failed to verify OTP")
            return None
        
        # Complete registration
        if await self.complete_registration(email, name, session_id):
            print(f"{Fore.GREEN}[✓] Account created successfully!")
            self._save_account(email)
            return email
        else:
            print(f"{Fore.RED}[!] Failed to complete registration")
            return None
    
    def _save_account(self, email: str):
        """Save created account to file"""
        with open('accounts.txt', 'a') as f:
            f.write(f'{email}\n')


class CLIInterface:
    """Command-line interface for the account generator"""
    
    def __init__(self):
        self.generator = AccountGenerator()
    
    def display_banner(self):
        """Display application banner"""
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}ACCOUNT GENERATOR - EDUCATIONAL TOOL")
        print(f"{Fore.RED}⚠️  FOR EDUCATIONAL PURPOSES ONLY ⚠️")
        print(f"{Fore.CYAN}{'='*50}\n")
    
    def display_menu(self):
        """Display main menu"""
        print(f"{Fore.GREEN}Select option:")
        print("1) Generate using IMAP")
        print("2) Generate using Hotmail")
        print("3) Exit")
        print(f"{Fore.YELLOW}\nChoice: ", end="")
    
    async def run(self):
        """Main CLI loop"""
        self.display_banner()
        
        while True:
            self.display_menu()
            choice = input().strip()
            
            if choice == '1':
                await self.generate_with_imap()
            elif choice == '2':
                await self.generate_with_hotmail()
            elif choice == '3':
                print(f"\n{Fore.CYAN}Exiting...")
                break
            else:
                print(f"{Fore.RED}Invalid option!")
    
    async def generate_with_imap(self):
        """Generate account using IMAP configuration"""
        # Load IMAP config from config.json
        config = self.generator.config.get('imap', {})
        
        if not config:
            print(f"{Fore.RED}[!] IMAP configuration not found in config.json")
            return
        
        email_client = IMAPClient(
            config['username'],
            config['password'],
            config.get('server', 'imap.gmail.com')
        )
        
        result = await self.generator.create_account(
            config['domain'],
            email_client
        )
        
        if result:
            print(f"\n{Fore.GREEN}[✓] Successfully created: {result}")
        else:
            print(f"\n{Fore.RED}[✗] Account creation failed")
    
    async def generate_with_hotmail(self):
        """Generate accounts using Hotmail list"""
        hotmail_file = Path('hotmailaccs.txt')
        
        if not hotmail_file.exists():
            print(f"{Fore.RED}[!] hotmailaccs.txt not found")
            return
        
        accounts = hotmail_file.read_text().strip().split('\n')
        
        for account in accounts:
            try:
                username, password = account.strip().split(':')
                email_client = IMAPClient(
                    username,
                    password,
                    'imap.zmailservice.com'
                )
                
                await self.generator.create_account('hotmail.com', email_client)
                
            except ValueError:
                print(f"{Fore.RED}[!] Invalid format in hotmailaccs.txt")
                continue
            except Exception as e:
                print(f"{Fore.RED}[!] Error processing {username}: {e}")
                continue


async def main():
    cli = CLIInterface()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())