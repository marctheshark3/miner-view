from datetime import datetime, timezone
from dateutil import parser
from dateutil.relativedelta import relativedelta

def format_date(date_string: str) -> str:
    """
    Parse an ISO 8601 date string and return a human-readable format.
    Also includes a relative time descriptor (e.g., '2 days ago').
    
    Args:
    date_string (str): An ISO 8601 formatted date string.
    
    Returns:
    str: A human-readable date string with relative time.
    """
    try:
        # Parse the ISO 8601 date string
        date = parser.isoparse(date_string)
        
        # Calculate the time difference
        now = datetime.now(timezone.utc)
        diff = relativedelta(now, date)
        
        # Create a relative time string
        if diff.years > 0:
            relative = f"{diff.years} year{'s' if diff.years != 1 else ''} ago"
        elif diff.months > 0:
            relative = f"{diff.months} month{'s' if diff.months != 1 else ''} ago"
        elif diff.days > 0:
            relative = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.hours > 0:
            relative = f"{diff.hours} hour{'s' if diff.hours != 1 else ''} ago"
        elif diff.minutes > 0:
            relative = f"{diff.minutes} minute{'s' if diff.minutes != 1 else ''} ago"
        else:
            relative = "just now"
        
        # Format the date
        formatted_date = date.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # return f"{formatted_date} ({relative})"
        return relative
    except Exception as e:
        print(e)
        return date_string
