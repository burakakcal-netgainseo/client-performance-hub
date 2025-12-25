import re

def format_name(name):
    """
    Capitalize name (Title Case).
    Example: "jane doe" -> "Jane Doe"
    """
    if not name or str(name).lower() == 'nan':
        return ""
    return str(name).strip().title()

def format_phone(phone):
    """
    Format phone number to (XXX) XXX-XXXX.
    """
    if not phone or str(phone).lower() == 'nan':
        return ""
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', str(phone))
    
    # Handle Country Code +1
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
        
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        
    # Return original if it doesn't match standard 10-digit pattern
    return phone
