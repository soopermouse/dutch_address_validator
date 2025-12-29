"""
Dutch Postal Address - A comprehensive Dutch postal address validation and correction library.
"""

__version__ = "1.0.0"
__author__ = "Address Validation Team"
__email__ = "dev@bluem.nl"
__license__ = "Proprietary"

from .address import Address, DutchAddressHandler
from .validator import validate, validate_lines
from .corrector import correct_city, correct_street

__all__ = [
    'Address',
    'DutchAddressHandler',
    'validate',
    'validate_lines',
    'correct_city',
    'correct_street'
]