"""
Address correction functionality with fuzzy matching.
"""

from typing import List, Optional, Set
import re
from difflib import get_close_matches
from .data_loader import DataLoader


class AddressCorrector:
    """Correct mistyped address components."""

    def __init__(self, data_loader: DataLoader):
        self.data = data_loader

    def correct_city(self, city: str, postcode: Optional[str] = None) -> List[str]:
        """
        Correct a city name.

        Args:
            city: (Possibly mistyped) city name
            postcode: Optional PC4 or PC6 for filtering

        Returns:
            List of possible correct city names
        """
        normalized_input = self.data._normalize_name(city)
        results = set()

        # Determine postcode filter
        pc4_filter = None
        if postcode:
            clean_pc = postcode.replace(' ', '').upper()
            if len(clean_pc) >= 4 and clean_pc[:4].isdigit():
                pc4_filter = clean_pc[:4]

        # Strategy 1: Exact match
        all_city_names = []
        for city_id, city_name in self.data._city_map.items():
            if pc4_filter:
                if city_id not in self.data.get_cities_by_pc4(pc4_filter):
                    continue

            normalized_city = self.data._normalize_name(city_name)
            all_city_names.append((city_name, normalized_city))

            if normalized_input == normalized_city:
                results.add(city_name)

        if results:
            return sorted(results)

        # Strategy 2: Fuzzy matching
        city_names = [name for name, norm in all_city_names]
        normalized_names = [norm for name, norm in all_city_names]

        # Use difflib for fuzzy matching
        matches = get_close_matches(normalized_input, normalized_names,
                                    n=10, cutoff=0.6)

        for match in matches:
            # Find original city name
            for orig_name, norm_name in all_city_names:
                if norm_name == match:
                    results.add(orig_name)

        return sorted(results)

    def correct_street(self, street: str, postcode: Optional[str] = None) -> List[str]:
        """
        Correct a street name.

        Args:
            street: (Possibly mistyped) street name
            postcode: Optional PC4 or PC6 for filtering

        Returns:
            List of possible correct street names
        """
        normalized_input = self.data._normalize_name(street)
        results = set()

        # Determine postcode filter
        pc6_filter = None
        if postcode:
            clean_pc = postcode.replace(' ', '').upper()
            if len(clean_pc) == 6 and clean_pc[:4].isdigit() and clean_pc[4:].isalpha():
                pc6_filter = clean_pc

        # Strategy 1: Exact match
        all_street_names = []
        for street_id, street_name in self.data._street_map.items():
            if pc6_filter:
                # Check if this street exists in the postcode area
                entries = self.data.get_addresses_by_pc6(pc6_filter)
                street_ids_in_pc6 = {e['street_id'] for e in entries if e.get('street_id')}
                if street_id not in street_ids_in_pc6:
                    continue

            normalized_street = self.data._normalize_name(street_name)
            all_street_names.append((street_name, normalized_street))

            if normalized_input == normalized_street:
                results.add(street_name)

        if results:
            return sorted(results)

        # Strategy 2: Fuzzy matching
        street_names = [name for name, norm in all_street_names]
        normalized_names = [norm for name, norm in all_street_names]

        matches = get_close_matches(normalized_input, normalized_names,
                                    n=10, cutoff=0.6)

        for match in matches:
            for orig_name, norm_name in all_street_names:
                if norm_name == match:
                    results.add(orig_name)

        return sorted(results)

    def search_addresses(self, query: str, limit: int = 10) -> List[dict]:
        """
        Search addresses by partial input.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching addresses
        """
        results = []
        query = query.strip().upper()

        if not query or len(query) < 2:
            return results

        # Check if it's a postcode
        pc_match = re.match(r'(\d{4})\s?([A-Za-z]{2})?', query)
        if pc_match:
            pc4 = pc_match.group(1)
            if pc_match.group(2):
                pc6 = pc4 + pc_match.group(2)
                entries = self.data.get_addresses_by_pc6(pc6)
                for entry in entries[:limit]:
                    street = self.data.get_street_by_id(entry['street_id'])
                    city = self.data.get_city_by_id(entry['city_id'])
                    if street and city:
                        results.append({
                            'street': street,
                            'house_number_range': f"{entry['hnr_from']}-{entry['hnr_to']}",
                            'postcode': f"{pc4} {pc6[4:]}",
                            'city': city
                        })
            else:
                # PC4 search
                city_ids = self.data.get_cities_by_pc4(pc4)
                for city_id in list(city_ids)[:5]:
                    city = self.data.get_city_by_id(city_id)
                    if city:
                        results.append({
                            'city': city,
                            'postcode_prefix': pc4,
                            'type': 'city'
                        })

        # City search
        if len(results) < limit:
            city_suggestions = self.correct_city(query)
            for city in city_suggestions[:3]:
                # Find postcodes for this city
                for pc6, entries in self.data._pc6_index.items():
                    for entry in entries:
                        if entry.get('city_id'):
                            city_name = self.data.get_city_by_id(entry['city_id'])
                            if city_name == city:
                                street = self.data.get_street_by_id(entry['street_id'])
                                if street:
                                    results.append({
                                        'street': street,
                                        'city': city,
                                        'postcode': f"{pc6[:4]} {pc6[4:]}",
                                        'house_number_range': f"{entry['hnr_from']}-{entry['hnr_to']}"
                                    })
                                    break
                    if len(results) >= limit:
                        break

        return results[:limit]


# Convenience functions
def correct_city(city: str, postcode: Optional[str] = None) -> List[str]:
    """Public function to correct city name."""
    from .address import DutchAddressHandler
    handler = DutchAddressHandler()
    return handler.correct_city(city, postcode)


def correct_street(street: str, postcode: Optional[str] = None) -> List[str]:
    """Public function to correct street name."""
    from .address import DutchAddressHandler
    handler = DutchAddressHandler()
    return handler.correct_street(street, postcode)