import pytest

import frameparsing as fp

class TestSequences:
    def test_parse_numbers(self, number_sequence, number_string):
        assert tuple(fp.parse_numbers(number_string)) == number_sequence

    def test_format_numbers(self, number_sequence, number_string):
        assert fp.format_numbers(number_sequence) == number_string

class TestRanges:
    def test_parse_numbers(self, range_obj, range_string):
        assert tuple(fp.parse_numbers(range_string)) == tuple(range_obj)

    def test_format_numbers(self, range_obj, range_string):
        assert fp.format_numbers(range_obj) == range_string

class TestInvalid:
    def test_format_numbers_invalid_types_in_iterables(self, invalid_number_sequence):
        with pytest.raises(TypeError, match = "'numbers' should only contain integers."):
            fp.format_numbers(invalid_number_sequence)

