from datetime import datetime

def format_timestamp(timestamp: int) -> str:
    """
    Format a Unix timestamp to a human-readable date string.
    
    Args:
        timestamp: Unix timestamp in seconds
        
    Returns:
        Formatted date string like "May 1, 2023"
    """
    return datetime.fromtimestamp(timestamp).strftime("%B %d, %Y") 