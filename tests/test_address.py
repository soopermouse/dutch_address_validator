"""Test address parsing and validation."""
import pytest
from dutch_postal_address import Address, DutchAddressHandler


class TestAddress:
    def test_address_creation(self):
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
        assert address.pc4 == "3811"
        assert address.pc6 == "3811MG"

    def test_postcode_normalization(self):
        address1 = Address(
            street_name="Test",
            house_number=1,
            house_number_extension="",
            postcode="1234ab",
            city="Test"
        )
        assert address1.postcode == "1234 AB"

        address2 = Address(
            street_name="Test",
            house_number=1,
            house_number_extension="",
            postcode="1234 AB",
            city="Test"
        )
        assert address2.postcode == "1234 AB"

    def test_address_lines(self):
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

    def test_from_lines(self):
        lines = [
            "Smallepad 30E",
            "3811 MG  Amersfoort"
        ]
        address = Address.from_lines(lines)
        assert address.street_name == "Smallepad"
        assert address.house_number == 30
        assert address.house_number_extension == "E"
        assert address.postcode == "3811 MG"
        assert address.city == "Amersfoort"


class TestDutchAddressHandler:
    def setup_method(self):
        self.handler = DutchAddressHandler(data_dir="test_data")

    def test_parse_valid_address(self):
        lines = ["Smallepad 30E", "3811 MG  Amersfoort"]
        address = self.handler.parse_address(lines)
        assert address is not None

    def test_parse_invalid_address(self):
        lines = ["Invalid Address", "Invalid Line"]
        address = self.handler.parse_address(lines)
        assert address is None