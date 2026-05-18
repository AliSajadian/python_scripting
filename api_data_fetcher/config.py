"""
Configuration management for API settings
"""
import os
from dotenv import load_dotenv


load_dotenv()


# Default log Format string
LOG_OUTPUT_FORMAT = 'common'  # Change this to switch formats

# Format string mappings
LOG_FORMATS = {
    'syslog': {
        'format': '%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s',
        'datefmt': '%b %d %H:%M:%S'
    },
    'common': {
        'format': '%(asctime)s,%(msecs)03d %(levelname)s %(name)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    },
    'simple': {
        'format': '%(levelname)s: %(message)s',
        'datefmt': None
    },
    'custom': {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    },
    'access': {
        'format': '%(remote_addr)s - %(remote_user)s [%(asctime)s] \
            "%(request)s" %(status)s %(body_bytes_sent)s',
        'datefmt': '%d/%b/%Y:%H:%M:%S %z'
    }
}


class APIConfig:
    """Centralized configuration for API connections"""

    def __init__(self):
        self.api_key = os.getenv('API_KEY', '')
        self.api_secret = os.getenv('API_SECRET', '')
        self.base_url = os.getenv('BASE_URL', 'https://api.example.com')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.rate_limit = int(os.getenv('RATE_LIMIT', '100'))  # requests per minute
        self.batch_size = int(os.getenv('BATCH_SIZE', '50'))

    def get_headers(self):
        """Returns default headers for API requests"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    