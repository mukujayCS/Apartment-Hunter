"""
Input validation utilities for API requests.
"""

def validate_listing_text(text):
    """
    Validate apartment listing text.

    Args:
        text (str): Listing text to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not isinstance(text, str):
        return False, "Listing text is required and must be a string"

    if len(text.strip()) < 50:
        return False, "Listing text too short. Please provide a more detailed description (minimum 50 characters)"

    if len(text) > 10000:
        return False, "Listing text too long. Please keep it under 10,000 characters"

    return True, None


def validate_university(university):
    """
    Validate university name.

    Args:
        university (str): University name

    Returns:
        tuple: (is_valid, error_message)
    """
    if not university or not isinstance(university, str):
        return False, "University name is required"

    # This is flexible - we accept any university name
    if len(university.strip()) < 2:
        return False, "University name too short"

    return True, None


def validate_address(address):
    """
    Validate address (optional field).

    Args:
        address (str): Address to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not address:
        # Address is optional
        return True, None

    if not isinstance(address, str):
        return False, "Address must be a string"

    if len(address) > 500:
        return False, "Address too long"

    return True, None


def validate_images(images):
    """
    Validate image files.

    Args:
        images (list): List of file objects or PIL Images

    Returns:
        tuple: (is_valid, error_message)
    """
    if not images:
        # Images are optional
        return True, None

    if not isinstance(images, list):
        return False, "Images must be provided as a list"

    if len(images) > 5:
        return False, "Maximum 5 images allowed"

    return True, None
