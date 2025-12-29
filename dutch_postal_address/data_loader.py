import re
from typing import Dict, List, Set, Optional, DefaultDict
from collections import defaultdict
from pathlib import Path
import unicodedata
from functools import lru_cache


class DataLoader:
    """
    Loads and indexes Dutch postal address data.

    Memory Optimizations:
    - Uses defaultdict for automatic key creation
    - LRU caching for frequent queries
    - Builds reverse indexes for fast lookups
    """

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)

        # Primary indexes
        self._pc6_index: DefaultDict[str, List[Dict]] = defaultdict(list)
        self._street_map: Dict[int, str] = {}
        self._city_map: Dict[int, str] = {}

        # Reverse indexes for fast searching
        self._street_name_to_id: DefaultDict[str, List[int]] = defaultdict(list)
        self._city_name_to_id: DefaultDict[str, List[int]] = defaultdict(list)
        self._pc4_index: DefaultDict[str, Set[int]] = defaultdict(set)
        self._street_id_to_pc6: DefaultDict[int, Set[str]] = defaultdict(set)

        self._load_all_data()

    def _load_all_data(self):
        """Load all data files."""
        self._load_wpl_data()
        self._load_str_data()
        self._load_hnr_data()
        self._build_reverse_indexes()

    def _load_wpl_data(self):
        """Load city data (PCS_WPL.dat)."""
        wpl_path = self.data_dir / 'PCS_WPL.dat'

        with open(wpl_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Handle ~ delimiter (from sample)
                if '~' in line:
                    city_id_str, city_name = line.split('~', 1)
                else:
                    # Try other delimiters
                    parts = line.replace('|', '~').split('~', 1)
                    if len(parts) == 2:
                        city_id_str, city_name = parts
                    else:
                        continue

                try:
                    city_id = int(city_id_str.strip())
                    self._city_map[city_id] = city_name.strip()
                except (ValueError, IndexError):
                    continue

    def _load_str_data(self):
        """Load street data (PCS_STR.dat)."""
        str_path = self.data_dir / 'PCS_STR.dat'

        with open(str_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Try different delimiters
                if '~' in line:
                    street_id_str, street_name = line.split('~', 1)
                elif '|' in line:
                    street_id_str, street_name = line.split('|', 1)
                else:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        street_id_str, street_name = parts
                    else:
                        continue

                try:
                    street_id = int(street_id_str.strip())
                    self._street_map[street_id] = street_name.strip()
                except (ValueError, IndexError):
                    continue

    def _load_hnr_data(self):
        """Load postcode-house number data (PCS_HNR.dat)."""
        hnr_path = self.data_dir / 'PCS_HNR.dat'

        with open(hnr_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Split by pipe (expected format)
                parts = line.split('|')
                if len(parts) < 5:
                    continue

                try:
                    pc6 = parts[0].strip()
                    if len(pc6) != 6:
                        continue

                    hnr_from = int(parts[1]) if parts[1].strip() else 0
                    hnr_to = int(parts[2]) if parts[2].strip() else hnr_from

                    street_id = int(parts[3]) if parts[3].strip() else None
                    city_id = int(parts[4]) if parts[4].strip() else None

                    if street_id is None or city_id is None:
                        continue

                    entry = {
                        'pc6': pc6,
                        'hnr_from': hnr_from,
                        'hnr_to': hnr_to,
                        'street_id': street_id,
                        'city_id': city_id
                    }

                    self._pc6_index[pc6].append(entry)
                    self._pc4_index[pc6[:4]].add(city_id)
                    self._street_id_to_pc6[street_id].add(pc6)

                except (ValueError, IndexError):
                    continue

    def _build_reverse_indexes(self):
        """Build reverse indexes for name-based lookups."""
        for city_id, city_name in self._city_map.items():
            normalized = self._normalize_name(city_name)
            self._city_name_to_id[normalized].append(city_id)

        for street_id, street_name in self._street_map.items():
            normalized = self._normalize_name(street_name)
            self._street_name_to_id[normalized].append(street_id)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for case-insensitive comparison."""
        name = unicodedata.normalize('NFKD', name)
        name = name.lower()
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    # Public API with caching

    @lru_cache(maxsize=10000)
    def get_addresses_by_pc6(self, pc6: str) -> List[Dict]:
        """Get entries for a specific PC6."""
        return self._pc6_index.get(pc6.upper(), [])

    @lru_cache(maxsize=1000)
    def get_cities_by_pc4(self, pc4: str) -> Set[int]:
        """Get city IDs for a PC4."""
        return self._pc4_index.get(pc4, set())

    def get_city_by_id(self, city_id: int) -> Optional[str]:
        """Get city name by ID."""
        return self._city_map.get(city_id)

    def get_street_by_id(self, street_id: int) -> Optional[str]:
        """Get street name by ID."""
        return self._street_map.get(street_id)

    def find_city_ids_by_name(self, city_name: str, pc4: Optional[str] = None) -> List[int]:
        """Find city IDs by name."""
        normalized = self._normalize_name(city_name)
        city_ids = self._city_name_to_id.get(normalized, [])

        if pc4:
            pc4_cities = self.get_cities_by_pc4(pc4)
            city_ids = [cid for cid in city_ids if cid in pc4_cities]

        return city_ids

    def find_street_ids_by_name(self, street_name: str, pc6: Optional[str] = None) -> List[int]:
        """Find street IDs by name."""
        normalized = self._normalize_name(street_name)
        street_ids = self._street_name_to_id.get(normalized, [])

        if pc6:
            pc6_entries = self.get_addresses_by_pc6(pc6)
            pc6_street_ids = {e['street_id'] for e in pc6_entries if e.get('street_id')}
            street_ids = [sid for sid in street_ids if sid in pc6_street_ids]

        return street_ids

    def is_house_number_valid(self, street_id: int, pc6: str,
                              house_number: int) -> bool:
        """Check if house number is valid."""
        entries = self.get_addresses_by_pc6(pc6)

        for entry in entries:
            if entry.get('street_id') == street_id:
                if entry['hnr_from'] <= house_number <= entry['hnr_to']:
                    return True

        return False