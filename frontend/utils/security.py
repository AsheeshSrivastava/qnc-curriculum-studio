"""Security utilities for Curriculum Studio frontend."""

import html
import re
from typing import Optional


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    For static HTML (like branding), this is less critical.
    For user-generated content, always sanitize before using unsafe_allow_html=True.
    
    Args:
        html_content: HTML string to sanitize
        
    Returns:
        Sanitized HTML string
    """
    # Escape HTML special characters
    # This is a basic sanitization - for production, consider using bleach library
    sanitized = html.escape(html_content)
    
    # Allow only safe HTML tags (if needed, uncomment and customize)
    # safe_tags = ['div', 'p', 'span', 'strong', 'em', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    # You would need a proper HTML parser like BeautifulSoup for full sanitization
    
    return sanitized


def sanitize_user_input(user_input: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        user_input: User-provided string
        
    Returns:
        Sanitized string safe for display
    """
    # Remove any HTML tags
    cleaned = re.sub(r'<[^>]+>', '', user_input)
    
    # Escape HTML entities
    sanitized = html.escape(cleaned)
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password string to validate
        
    Returns:
        (is_valid: bool, message: str)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Note: Supabase Auth has its own password requirements
    # This is just basic frontend validation
    return True, "Password is valid"




