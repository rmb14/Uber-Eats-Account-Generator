# Account Generator Security Analysis Tool

## ⚠️ DISCLAIMER

**This project is strictly for educational and research purposes only.** It is designed to help security professionals and students understand web automation vulnerabilities and implement better defenses. 

**DO NOT USE THIS CODE FOR:**
- Creating unauthorized accounts
- Violating any Terms of Service
- Any illegal or unethical activities
- Production use of any kind

**By using this code, you acknowledge that:**
- You will use it only in controlled, educational environments
- You understand the legal and ethical implications
- You take full responsibility for your actions
- The authors are not liable for any misuse

---

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Code Architecture](#code-architecture)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Features

### Core Functionality
- **Automated Request Flow**: Demonstrates how account creation workflows can be automated
- **Email Integration**: Shows vulnerabilities in email-based verification systems
- **Device Spoofing**: Illustrates how device fingerprints can be manipulated
- **OTP Extraction**: Demonstrates automated OTP retrieval from emails

### Educational Features
- **Comprehensive Logging**: Detailed logs for understanding each step
- **Error Handling**: Robust error management with educational messages
- **Security Demonstrations**: Shows both attack vectors and defense mechanisms
- **Modular Architecture**: Clean code structure for easy understanding

### Security Research Tools
- **Rate Limiting Examples**: Demonstrates proper rate limiting implementation
- **Proxy Support**: Shows how requests can be routed through proxies
- **Device Fingerprinting**: Illustrates various device spoofing techniques
- **Session Management**: Demonstrates session handling vulnerabilities

## 📦 Requirements

### System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Python Dependencies
```txt
curl-cffi>=0.5.9
beautifulsoup4>=4.12.0
colorama>=0.4.6
aiofiles>=23.0.0
python-dotenv>=1.0.0
```

### Email Requirements
- IMAP-enabled email account (for OTP extraction)
- App-specific password (for Gmail/Outlook)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/account-generator-security-tool.git
cd account-generator-security-tool
pip install -r requirements.txt
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Settings
```bash
# Copy example configuration
cp config.example.json config.json

# Edit with your settings
nano config.json  # or use your preferred editor
```

## ⚙️ Configuration

### Basic Configuration (config.json)

```json
{
  "proxy": "http://user:pass@proxy:port",
  "proxy_enabled": false,
  "imap": {
    "username": "your_email@gmail.com",
    "password": "your_app_password",
    "server": "imap.gmail.com",
    "domain": "yourdomain.com"
  },
  "security": {
    "use_proxy": true,
    "rotate_user_agents": true,
    "randomize_timing": true
  }
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `proxy` | Proxy server URL | None |
| `proxy_enabled` | Enable proxy usage | false |
| `imap.username` | Email for OTP retrieval | Required |
| `imap.password` | Email app password | Required |
| `rate_limiting.requests_per_minute` | Max requests per minute | 10 |
| `security.randomize_timing` | Add random delays | true |

## 💻 Usage

### Basic Usage

```bash
# Run the main program
python main.py

# Run with specific configuration
python main.py --config custom_config.json

# Run in debug mode
python main.py --debug
```

### Menu Options

1. **Generate using IMAP**: Uses configured IMAP email for OTP retrieval
2. **Generate using Hotmail**: Uses Hotmail accounts from `hotmailaccs.txt`
3. **Exit**: Safely exits the program

### Example Workflow

```python
# Import the modules
from main import AccountGenerator, IMAPClient
from otp import EmailOTPExtractor

# Initialize components
generator = AccountGenerator('config.json')
email_client = IMAPClient('email@gmail.com', 'password')

# Run the workflow
email = await generator.create_account('domain.com', email_client)
```

## 🏗️ Code Architecture

### Main Components

#### 1. **main.py**
- `AccountGenerator`: Orchestrates the account creation workflow
- `DeviceSpoofer`: Generates realistic device fingerprints
- `RequestHandler`: Manages HTTP requests with retry logic
- `CLIInterface`: Provides command-line interaction

#### 2. **otp.py**
- `IMAPClient`: Handles email server connections
- `OTPExtractor`: Base class for OTP extraction strategies
- `EmailOTPExtractor`: Main extraction implementation
- `SecureOTPHandler`: Demonstrates secure OTP handling

#### 3. **config.json**
- Centralized configuration management
- Security settings and rate limits

### Class Hierarchy

```
RequestHandler
    └── HTTP request management with proxy support

AccountGenerator
    ├── DeviceSpoofer (device fingerprinting)
    ├── RequestHandler (network requests)
    └── Workflow orchestration

EmailOTPExtractor
    ├── IMAPClient (email connections)
    └── OTPExtractor implementations
        └── UberOTPExtractor
```

### Data Flow

1. **Initialization**: Load config, create device fingerprint
2. **Email Signup**: Submit email to initiate process
3. **OTP Retrieval**: Monitor email for verification code
4. **OTP Submission**: Submit code to verify email
5. **Registration**: Complete remaining steps
6. **Finalization**: Save account details

## 🚨 Error Handling

### Built-in Error Types

1. **Network Errors**: Automatic retry with exponential backoff
2. **Authentication Errors**: Clear messages about credentials
3. **Parsing Errors**: Detailed logging for debugging
4. **Timeout Errors**: Configurable timeout periods

### Error Recovery

```python
try:
    result = await generator.create_account(domain, email_client)
except NetworkError:
    # Automatic retry logic
except AuthenticationError:
    # Credential validation
except TimeoutError:
    # Timeout handling
```

### Logging Levels

- **DEBUG**: Detailed execution flow
- **INFO**: Normal operation events
- **WARNING**: Potential issues
- **ERROR**: Operation failures
- **CRITICAL**: System failures

## 🔒 Security Considerations

### For Defenders

1. **Implement CAPTCHA**: Add human verification
2. **Device Fingerprinting**: Use advanced fingerprinting
3. **Rate Limiting**: Limit requests per IP/device
4. **Email Verification**: Use secure email verification
5. **Behavioral Analysis**: Monitor for automated patterns

### For Researchers

1. **Session Management**: Understanding authentication flows
2. **Fingerprinting Spoofing**: Device identification bypass
3. **Timing Analysis**: Avoiding detection through delays
4. **Proxy Rotation**: Understanding proxy chains

## 🤝 Contributing

We welcome contributions that enhance the educational value of this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/enhancement`)
3. Commit your changes (`git commit -m 'Add educational feature'`)
4. Push to the branch (`git push origin feature/enhancement`)
5. Open a Pull Request

### Contribution Guidelines

- Focus on educational value
- Add comprehensive documentation
- Include security implications
- Follow PEP 8 style guide

## 📄 License

This project is licensed under the **MIT License with Educational Use Clause** - see the [LICENSE](LICENSE) file for details.

---

**Remember**: The purpose of understanding these vulnerabilities is to build better, more secure systems. Always use this knowledge responsibly and ethically.