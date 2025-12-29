import pytest
import tempfile
import os
from pathlib import Path
from dutch_postal_address.data_loader import DataLoader


class TestDataLoader:
    """Test data loading functionality."""

    def setup_method(self):
        """Create temporary test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        """Create minimal test data files."""
        # Create PCS_WPL.dat with ~ delimiter
        wpl_content = """1000~AMSTERDAM
3800~AMERSFOORT
3811~AMERSFOORT
9999~TEST CITY"""

        wpl_path = self.data_dir / "PCS_WPL.dat"
        wpl_path.write_text(wpl_content, encoding='utf-8')

        # Create PCS_STR.dat
        str_content = """12345~SMALLEPAD
12346~KALVERSTRAAT
99999~TEST STREET"""

        str_path = self.data_dir / "PCS_STR.dat"
        str_path.write_text(str_content, encoding='utf-8')

        # Create PCS_HNR.dat with pipe delimiter
        hnr_content = """3811MG|30|30|12345|3811|
3811MG|31|50|12345|3811|
1012PA|1|100|12346|1000|
9999ZZ|1|999|99999|9999|"""

        hnr_path = self.data_dir / "PCS_HNR.dat"
        hnr_path.write_text(hnr_content, encoding='utf-8')

    def test_data_loader_initialization(self):
        """Test DataLoader can be initialized."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        assert loader is not None
        assert len(loader._city_map) > 0
        assert len(loader._street_map) > 0
        assert len(loader._pc6_index) > 0

    def test_city_loading(self):
        """Test city data is loaded correctly."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        # Check specific cities
        assert loader.get_city_by_id(3811) == "AMERSFOORT"
        assert loader.get_city_by_id(1000) == "AMSTERDAM"
        assert loader.get_city_by_id(9999) == "TEST CITY"
        assert loader.get_city_by_id(99999) is None  # Non-existent ID

    def test_street_loading(self):
        """Test street data is loaded correctly."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        assert loader.get_street_by_id(12345) == "SMALLEPAD"
        assert loader.get_street_by_id(12346) == "KALVERSTRAAT"
        assert loader.get_street_by_id(99999) == "TEST STREET"

    def test_pc6_index(self):
        """Test postcode indexing."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        # Check entries for a specific postcode
        entries = loader.get_addresses_by_pc6("3811MG")
        assert len(entries) == 2

        # Verify entry structure
        entry = entries[0]
        assert entry['pc6'] == "3811MG"
        assert entry['street_id'] == 12345
        assert entry['city_id'] == 3811
        assert entry['hnr_from'] == 30
        assert entry['hnr_to'] == 30

    def test_pc4_index(self):
        """Test PC4 to city mapping."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        cities_3811 = loader.get_cities_by_pc4("3811")
        assert 3811 in cities_3811

        cities_1012 = loader.get_cities_by_pc4("1012")
        assert 1000 in cities_1012

    def test_normalize_name(self):
        """Test name normalization."""
        from dutch_postal_address.data_loader import DataLoader

        test_cases = [
            ("Amsterdam", "amsterdam"),
            ("AMSTERDAM", "amsterdam"),
            ("'s-Gravenhage", "s gravenhage"),
            ("Den Haag", "den haag"),
            ("Test-Street", "test street"),
            ("  Extra  Spaces  ", "extra spaces"),
        ]

        for input_name, expected_normalized in test_cases:
            normalized = DataLoader._normalize_name(input_name)
            assert normalized == expected_normalized, \
                f"Failed for '{input_name}': got '{normalized}', expected '{expected_normalized}'"

    def test_find_city_ids_by_name(self):
        """Test finding city IDs by name."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        # Exact match
        city_ids = loader.find_city_ids_by_name("AMERSFOORT")
        assert 3811 in city_ids

        # Case insensitive
        city_ids = loader.find_city_ids_by_name("amersfoort")
        assert 3811 in city_ids

        # With PC4 filter
        city_ids = loader.find_city_ids_by_name("AMERSFOORT", "3811")
        assert 3811 in city_ids

        # Wrong PC4 filter (should return empty)
        city_ids = loader.find_city_ids_by_name("AMERSFOORT", "9999")
        assert 3811 not in city_ids

    def test_find_street_ids_by_name(self):
        """Test finding street IDs by name."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        # Exact match
        street_ids = loader.find_street_ids_by_name("SMALLEPAD")
        assert 12345 in street_ids

        # Case insensitive
        street_ids = loader.find_street_ids_by_name("smallepad")
        assert 12345 in street_ids

        # With PC6 filter
        street_ids = loader.find_street_ids_by_name("SMALLEPAD", "3811MG")
        assert 12345 in street_ids

        # Wrong PC6 filter
        street_ids = loader.find_street_ids_by_name("SMALLEPAD", "9999ZZ")
        assert 12345 not in street_ids

    def test_house_number_validation(self):
        """Test house number validation."""
        self.create_test_files()
        loader = DataLoader(self.temp_dir)

        # Valid house numbers
        assert loader.is_house_number_valid(12345, "3811MG", 30) is True
        assert loader.is_house_number_valid(12345, "3811MG", 35) is True  # In range 31-50
        assert loader.is_house_number_valid(12345, "3811MG", 50) is True

        # Invalid house numbers
        assert loader.is_house_number_valid(12345, "3811MG", 29) is False  # Below range
        assert loader.is_house_number_valid(12345, "3811MG", 51) is False  # Above range
        assert loader.is_house_number_valid(99999, "3811MG", 1) is False  # Wrong street ID

    def test_missing_data_files(self):
        """Test error handling for missing data files."""
        # Create empty directory
        loader = DataLoader(self.temp_dir)

        # Should raise FileNotFoundError or similar
        with pytest.raises((FileNotFoundError, RuntimeError)):
            # This will fail because files don't exist
            loader._load_all_data()

    def test_malformed_data(self):
        """Test handling of malformed data lines."""
        # Create malformed WPL file
        wpl_content = """invalid_line
1000~AMSTERDAM
~City without ID
ID~"""

        wpl_path = self.data_dir / "PCS_WPL.dat"
        wpl_path.write_text(wpl_content, encoding='utf-8')

        # Create empty other files
        (self.data_dir / "PCS_STR.dat").write_text("", encoding='utf-8')
        (self.data_dir / "PCS_HNR.dat").write_text("", encoding='utf-8')

        # Should handle gracefully (skip invalid lines)
        loader = DataLoader(self.temp_dir)
        assert loader.get_city_by_id(1000) == "AMSTERDAM"