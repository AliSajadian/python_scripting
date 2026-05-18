"""
Configuration management for API settings
"""

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
