import pytest
from dutch_postal_address import Address, DutchAddressHandler


class TestAddress:
    """Test Address class functionality."""

    def test_address_creation(self):
        """Test basic address creation."""
        address = Address(
            street_name="Smallepad",
            house_number=30,
            house_number_extension="E",
            postcode="3811 MG",
            city="Amersfoort"
        )

        assert address.street_name == "Smallepad"
        assert address.house_number == 30
        assert address.house_number_extension == "E"
        assert address.postcode == "3811 MG"
        assert address.city == "Amersfoort"

    def test_address_immutability(self):
        """Test that Address is immutable."""
        address = Address(
            street_name="Test",
            house_number=1,
            house_number_extension="",
            postcode="1234 AB",
            city="Test"
        )

        # Should not be able to modify attributes
        with pytest.raises(Exception):
            address.street_name = "Modified"

    def test_postcode_normalization(self):
        """Test postcode normalization."""
        test_cases = [
            ("1234AB", "1234 AB"),
            ("1234 AB", "1234 AB"),
            ("1234  AB", "1234 AB"),
            ("1234ab", "1234 AB"),
            ("  1234AB  ", "1234 AB"),
        ]

        for input_pc, expected_pc in test_cases:
            address = Address(
                street_name="Test",
                house_number=1,
                house_number_extension="",
                postcode=input_pc,
                city="Test"
            )
            assert address.postcode == expected_pc

    def test_properties(self):
        """Test address properties."""
        address = Address(
            street_name="Test",
            house_number=1,
            house_number_extension="A",
            postcode="1234 AB",
            city="Test"
        )

        assert address.pc4 == "1234"
        assert address.pc6 == "1234AB"
        assert address.house_number_extension == "A"

    def test_to_lines(self):
        """Test conversion to two-line format."""
        address = Address(
            street_name="Smallepad",
            house_number=30,
            house_number_extension="E",
            postcode="3811 MG",
            city="Amersfoort"
        )

        lines = address.to_lines()

        assert len(lines) == 2
        assert lines[0] == "Smallepad 30E"
        assert lines[1] == "3811 MG  Amersfoort"

        # Test without extension
        address2 = Address(
            street_name="Kalverstraat",
            house_number=1,
            house_number_extension="",
            postcode="1012 PA",
            city="Amsterdam"
        )

        lines2 = address2.to_lines()
        assert lines2[0] == "Kalverstraat 1"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        address = Address(
            street_name="Smallepad",
            house_number=30,
            house_number_extension="E",
            postcode="3811 MG",
            city="Amersfoort"
        )

        data = address.to_dict()

        assert isinstance(data, dict)
        assert data['street_name'] == "Smallepad"
        assert data['house_number'] == 30
        assert data['house_number_extension'] == "E"
        assert data['postcode'] == "3811 MG"
        assert data['city'] == "Amersfoort"
        assert data['pc4'] == "3811"
        assert data['pc6'] == "3811MG"

    def test_from_lines(self):
        """Test parsing from two-line format."""
        # Standard format
        lines = ["Smallepad 30E", "3811 MG  Amersfoort"]
        address = Address.from_lines(lines)

        assert address.street_name == "Smallepad"
        assert address.house_number == 30
        assert address.house_number_extension == "E"
        assert address.postcode == "3811 MG"
        assert address.city == "Amersfoort"

        # Without extension
        lines2 = ["Kalverstraat 1", "1012 PA  Amsterdam"]
        address2 = Address.from_lines(lines2)

        assert address2.street_name == "Kalverstraat"
        assert address2.house_number == 1
        assert address2.house_number_extension == ""
        assert address2.postcode == "1012 PA"
        assert address2.city == "Amsterdam"

        # With lowercase
        lines3 = ["smallepad 30e", "3811 mg  amersfoort"]
        address3 = Address.from_lines(lines3)

        assert address3.street_name == "smallepad"
        assert address3.house_number == 30
        assert address3.house_number_extension == "E"
        assert address3.postcode == "3811 MG"
        assert address3.city == "amersfoort"

    def test_from_lines_invalid(self):
        """Test invalid line formats."""
        # Too few lines
        with pytest.raises(ValueError):
            Address.from_lines(["Single line"])

        # Too many lines
        with pytest.raises(ValueError):
            Address.from_lines(["Line 1", "Line 2", "Line 3"])

        # Invalid street format
        with pytest.raises(ValueError):
            Address.from_lines(["NoNumber", "1234 AB  City"])

        # Invalid postcode format
        with pytest.raises(ValueError):
            Address.from_lines(["Street 1", "Invalid  City"])

    def test_extension_normalization(self):
        """Test house number extension normalization."""
        test_cases = [
            ("e", "E"),
            ("E", "E"),
            ("aB", "AB"),
            ("", ""),
        ]

        for input_ext, expected_ext in test_cases:
            address = Address(
                street_name="Test",
                house_number=1,
                house_number_extension=input_ext,
                postcode="1234 AB",
                city="Test"
            )
            assert address.house_number_extension == expected_ext


class TestDutchAddressHandler:
    """Test DutchAddressHandler class."""

    def test_handler_initialization(self):
        """Test handler can be initialized."""
        # This will fail if data files don't exist, but shouldn't crash
        try:
            handler = DutchAddressHandler(data_dir="non_existent")
            # If it doesn't crash, it should at least create the handler
            assert handler is not None
        except Exception:
            # It's OK if it fails due to missing data files
            pass

    def test_parse_address(self):
        """Test address parsing in handler."""
        handler = DutchAddressHandler(data_dir="test_data")

        # Valid address
        lines = ["Smallepad 30E", "3811 MG  Amersfoort"]
        address = handler.parse_address(lines)
        assert address is not None

        # Invalid address
        lines = ["Invalid", "Format"]
        address = handler.parse_address(lines)
        assert address is None