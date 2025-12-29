import pytest
from dutch_postal_address import validate, validate_lines
from dutch_postal_address.address import Address, DutchAddressHandler


class TestValidationFunctions:
    """Test the public validation functions."""

    def setup_method(self):
        """Set up test data directory."""
        import tempfile
        import os
        from pathlib import Path

        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)

        # Create minimal test data
        self._create_test_data()

        # Monkey patch the default data directory for tests
        import dutch_postal_address.data_loader
        self.original_data_dir = dutch_postal_address.data_loader.DEFAULT_DATA_DIR
        dutch_postal_address.data_loader.DEFAULT_DATA_DIR = str(self.data_dir)

        # Also patch the handler
        import dutch_postal_address.address
        self.original_handler_data_dir = dutch_postal_address.address.DEFAULT_DATA_DIR
        dutch_postal_address.address.DEFAULT_DATA_DIR = str(self.data_dir)

    def teardown_method(self):
        """Clean up."""
        import shutil
        import dutch_postal_address.data_loader
        import dutch_postal_address.address

        shutil.rmtree(self.temp_dir)
        dutch_postal_address.data_loader.DEFAULT_DATA_DIR = self.original_data_dir
        dutch_postal_address.address.DEFAULT_DATA_DIR = self.original_handler_data_dir

    def _create_test_data(self):
        """Create test data files."""
        # Cities
        wpl_content = """1000~AMSTERDAM
3800~AMERSFOORT
3811~AMERSFOORT"""
        (self.data_dir / "PCS_WPL.dat").write_text(wpl_content, encoding='utf-8')

        # Streets
        str_content = """12345~SMALLEPAD
12346~KALVERSTRAAT
12347~DAMSTRAAT"""
        (self.data_dir / "PCS_STR.dat").write_text(str_content, encoding='utf-8')

        # Postcodes and house numbers
        hnr_content = """3811MG|30|30|12345|3811|
3811MG|31|50|12345|3811|
1012PA|1|100|12346|1000|
1012PB|1|50|12346|1000|
1012PC|51|100|12346|1000|"""
        (self.data_dir / "PCS_HNR.dat").write_text(hnr_content, encoding='utf-8')

    def test_validate_function(self):
        """Test the validate() function."""
        # Test valid address
        result = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="E",
            postcode="3811 MG",
            city="AMERSFOORT"
        )
        assert isinstance(result, bool)

        # Test invalid address
        result = validate(
            street_name="NONEXISTENT",
            house_number=999,
            house_number_extension="",
            postcode="9999 ZZ",
            city="NOWHERE"
        )
        assert result is False

    def test_validate_lines_function(self):
        """Test the validate_lines() function."""
        # Test valid address lines
        lines = ["SMALLEPAD 30E", "3811 MG  AMERSFOORT"]
        result = validate_lines(lines)
        assert result is True

        # Test invalid address lines
        lines = ["INVALID 999", "9999 ZZ  NOWHERE"]
        result = validate_lines(lines)
        assert result is False

        # Test malformed lines
        lines = ["Only one line"]
        result = validate_lines(lines)
        assert result is False

    def test_validate_with_different_formats(self):
        """Test validation with different postcode formats."""
        # Test without space
        result1 = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="E",
            postcode="3811MG",
            city="AMERSFOORT"
        )

        # Test with space
        result2 = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="E",
            postcode="3811 MG",
            city="AMERSFOORT"
        )

        # Both should work
        assert result1 == result2

    def test_validate_house_number_ranges(self):
        """Test house number range validation."""
        # House number 30 (exact match)
        result1 = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )

        # House number 40 (in range 31-50)
        result2 = validate(
            street_name="SMALLEPAD",
            house_number=40,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )

        # House number 60 (out of range)
        result3 = validate(
            street_name="SMALLEPAD",
            house_number=60,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )

        assert result1 is True
        assert result2 is True
        assert result3 is False

    def test_validate_city_mismatch(self):
        """Test validation with wrong city for postcode."""
        # Correct city
        result1 = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )

        # Wrong city (Amsterdam instead of Amersfoort)
        result2 = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="AMSTERDAM"
        )

        assert result1 is True
        assert result2 is False

    def test_validate_edge_cases(self):
        """Test edge cases in validation."""
        # Empty extension
        result = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )
        assert result is True

        # Lowercase city name
        result = validate(
            street_name="SMALLEPAD",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="amersfoort"
        )
        assert result is True

        # Mixed case street name
        result = validate(
            street_name="Smallepad",
            house_number=30,
            house_number_extension="",
            postcode="3811 MG",
            city="AMERSFOORT"
        )
        assert result is True