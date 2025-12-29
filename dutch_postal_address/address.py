import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """
    Immutable data class representing a Dutch postal address.
    """
    street_name: str
    house_number: int
    house_number_extension: str
    postcode: str
    city: str

    def __post_init__(self):
        """Normalize address components."""
        object.__setattr__(self, 'house_number_extension',
                           self.house_number_extension.upper())
        object.__setattr__(self, 'postcode', self._normalize_postcode(self.postcode))

    @staticmethod
    def _normalize_postcode(postcode: str) -> str:
        """Normalize postcode to '1234 AB' format."""
        if not postcode:
            return ''

        postcode = postcode.upper().replace(' ', '')

        if len(postcode) != 6:
            return postcode

        if not (postcode[:4].isdigit() and postcode[4:].isalpha()):
            return postcode

        return f"{postcode[:4]} {postcode[4:]}"

    @property
    def pc4(self) -> str:
        """First 4 digits of postcode."""
        return self.postcode[:4].strip() if self.postcode and len(self.postcode) >= 4 else ''

    @property
    def pc6(self) -> str:
        """Full postcode without space."""
        return self.postcode.replace(' ', '') if self.postcode else ''

    def to_lines(self) -> List[str]:
        """Convert to standard two-line format."""
        street_part = f"{self.street_name} {self.house_number}{self.house_number_extension}".strip()
        city_part = f"{self.postcode}  {self.city}"
        return [street_part, city_part]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'street_name': self.street_name,
            'house_number': self.house_number,
            'house_number_extension': self.house_number_extension,
            'postcode': self.postcode,
            'city': self.city,
            'pc4': self.pc4,
            'pc6': self.pc6
        }

    @classmethod
    def from_lines(cls, address_lines: List[str]) -> 'Address':
        """Parse address from two lines."""
        if len(address_lines) != 2:
            raise ValueError("Address must be exactly two lines")

        line1 = address_lines[0].strip()
        line2 = address_lines[1].strip()

        # Parse street line
        street_match = re.match(r'^(.+?)\s+(\d+)([A-Za-z]*?)$', line1)
        if not street_match:
            raise ValueError(f"Cannot parse street address: {line1}")

        street_name = street_match.group(1).strip()
        house_number = int(street_match.group(2))
        house_extension = street_match.group(3).upper()

        # Parse city line
        # Remove multiple spaces and split
        line2 = re.sub(r'\s{2,}', '  ', line2)
        parts = line2.split('  ')

        if len(parts) >= 2:
            postcode = parts[0].strip()
            city = parts[1].strip()
        else:
            # Fallback parsing
            parts = line2.split()
            if len(parts) >= 3:
                postcode = f"{parts[0]} {parts[1]}"
                city = ' '.join(parts[2:])
            else:
                raise ValueError(f"Cannot parse city line: {line2}")

        return cls(
            street_name=street_name,
            house_number=house_number,
            house_number_extension=house_extension,
            postcode=postcode,
            city=city
        )


class DutchAddressHandler:
    """
    Main handler for Dutch postal address operations.
    """

    def __init__(self, data_dir: str = 'data'):
        from .data_loader import DataLoader
        from .validator import AddressValidator
        from .corrector import AddressCorrector

        self.data_loader = DataLoader(data_dir)
        self.validator = AddressValidator(self.data_loader)
        self.corrector = AddressCorrector(self.data_loader)

    def parse_address(self, address_lines: List[str]) -> Optional[Address]:
        """Parse address from two lines."""
        try:
            return Address.from_lines(address_lines)
        except ValueError:
            return None

    def validate(self, street_name: str, house_number: int,
                 house_number_extension: str, postcode: str, city: str) -> bool:
        """Validate address components."""
        address = Address(
            street_name=street_name,
            house_number=house_number,
            house_number_extension=house_number_extension,
            postcode=postcode,
            city=city
        )
        return self.validator.validate(address)

    def validate_lines(self, address_lines: List[str]) -> bool:
        """Validate address from two lines."""
        address = self.parse_address(address_lines)
        return self.validator.validate(address) if address else False

    def correct_city(self, city: str, postcode: Optional[str] = None) -> List[str]:
        """Correct city name."""
        return self.corrector.correct_city(city, postcode)

    def correct_street(self, street: str, postcode: Optional[str] = None) -> List[str]:
        """Correct street name."""
        return self.corrector.correct_street(street, postcode)

    def search_addresses(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search addresses by partial input."""
        return self.corrector.search_addresses(query, limit)