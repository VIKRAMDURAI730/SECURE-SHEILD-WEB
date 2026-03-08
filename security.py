"""Attack detection and security event logging."""
import re
import urllib.request
import json
from database import db_cursor

# Patterns that indicate attack attempts
SQLI_PATTERNS = [
    r"'\s*OR\s+1\s*=\s*1",
    r"'\s*OR\s+'1'\s*=\s*'1",
    r"--\s*$",
    r";\s*DROP\s+TABLE",
    r"UNION\s+SELECT",
    r"1\s*=\s*1",
    r"OR\s+1\s*=\s*1",
    r"'\s*;\s*--",
    r"admin\s*--",
]

XSS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
    r"<img\s+",
    r"<iframe",
    r"document\.cookie",
    r"alert\s*\(",
    r"eval\s*\(",
]


def _matches_patterns(text, patterns):
    """Check if text matches any attack pattern."""
    if not text:
        return False
    text_lower = text.lower()
    for pat in patterns:
        if re.search(pat, text_lower, re.IGNORECASE):
            return True
    return False


def is_sql_injection(text):
    """Detect SQL injection attempt in input."""
    return _matches_patterns(text, SQLI_PATTERNS)


def is_xss_attempt(text):
    """Detect XSS attempt in input."""
    return _matches_patterns(text, XSS_PATTERNS)


def get_client_ip():
    """Get client IP from request (handles proxies)."""
    from flask import request
    return (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.headers.get('X-Real-IP', '').strip()
        or request.remote_addr
        or '0.0.0.0'
    )


def get_location_for_ip(ip):
    """Get location string for IP using ip-api.com (free, no key)."""
    if not ip or ip in ('127.0.0.1', 'localhost', '0.0.0.0', '::1'):
        return 'Local'
    try:
        url = f'http://ip-api.com/json/{ip}?fields=country,regionName,city'
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            parts = [data.get('city'), data.get('regionName'), data.get('country')]
            return ', '.join(p for p in parts if p) or 'Unknown'
    except Exception:
        return 'Unknown'


def log_security_event(event_type, attacker_name=None, fixed=True, message=None, details=None):
    """Log a security event to the database."""
    from flask import request
    ip = get_client_ip()
    location = get_location_for_ip(ip)
    user_agent = (request.headers.get('User-Agent') or '')[:500]
    with db_cursor() as cur:
        cur.execute('''
            INSERT INTO security_events (event_type, attacker_name, ip_address, location, fixed, message, details, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (event_type, attacker_name or 'Unknown', ip, location, 1 if fixed else 0, message or '', details or '', user_agent))
