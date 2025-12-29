import re
from typing import List
from .address import Address, DutchAddressHandler


def validate(street_name: str, house_number: int,
             house_number_extension: str, postcode: str, city: str) -> bool:
    """
    Validate a Dutch postal address.

    Args:
        street_name: Name of the street
        house_number: House number (integer)
        house_number_extension: House number extension (letter/s)
        postcode: Postal code (format: '1234 AB' or '1234AB')
        city: City name

    Returns:
        True if address is valid, False otherwise
    """
    # Create a handler with default data directory
    handler = DutchAddressHandler()
    return handler.validate(street_name, house_number,
                            house_number_extension, postcode, city)


def validate_lines(address_lines: List[str]) -> bool:
    """
    Validate address from two-line format.

    Args:
        address_lines: List of two address lines

    Returns:
        True if address is valid, False otherwise
    """
    handler = DutchAddressHandler()
    return handler.validate_lines(address_lines)