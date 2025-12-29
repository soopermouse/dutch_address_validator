"""Test validation functions."""
import pytest
from dutch_postal_address import validate, validate_lines


class TestValidation:
    def test_validate_function_exists(self):
        """Test that the required function exists."""
        assert callable(validate)

    def test_validate_lines_function_exists(self):
        """Test that the required function exists."""
        assert callable(validate_lines)

    def test_validate_returns_boolean(self):
        """Test that validate returns a boolean."""
        result = validate(
            street_name="Test",
            house_number=1,
            house_number_extension="",
            postcode="1234AB",
            city="Test"
        )
        assert isinstance(result, bool)

    def test_validate_lines_returns_boolean(self):
        """Test that validate_lines returns a boolean."""
        result = validate_lines(["Test 1", "1234 AB  Test"])
        assert isinstance(result, bool)