import re
from pathlib import Path

import pytest

import frameparsing as fp

class TestAnalysis:

    def test_get_framecode_filename(self, input_filename, sequence_framecodes):
        assert fp.get_framecode(input_filename) == sequence_framecodes["digits"]

    def test_get_framecode_with_encodings(self, sequence_data, fc_type_non_digit, sequence_framecodes):
        assert (fp.get_framecode(sequence_data[fc_type_non_digit]) 
                == sequence_framecodes[fc_type_non_digit])

    def test_get_frame_number(self, input_filename, input_frame_number):
        assert fp.get_frame_number(input_filename) \
        == input_frame_number

    def test_get_frame_number_none(self, non_sequence_filename):
        assert fp.get_frame_number(non_sequence_filename) is None
          
    def test_has_framecode(self, encoded_filename):
        assert fp.has_framecode(encoded_filename)

    def test_has_framecode_with_Path_object(self, encoded_filename):
        assert fp.has_framecode(Path(encoded_filename))

    def test_has_framecode_false(self, non_sequence_filename):
        assert not fp.has_framecode(non_sequence_filename)

    def test_get_framecode_type(self, encoded_filename, fc_type_non_digit):
        assert fp.get_framecode_type(encoded_filename) == fc_type_non_digit

    def test_get_framecode_type_none(self, non_sequence_filename):
        assert fp.get_framecode_type(non_sequence_filename) is None

    def test_get_framecode_width(self, encoded_filename, framecode_width):
        assert fp.get_framecode_width(encoded_filename) == framecode_width

    def test_get_framecode_width_none(self, non_sequence_filename):
        assert fp.get_framecode_width(non_sequence_filename) is None


    @pytest.mark.parametrize("func", [
        fp.get_framecode,
        fp.get_frame_number,
        fp.has_framecode,
        fp.get_framecode_type,
        fp.get_framecode_width
    ])
    @pytest.mark.parametrize("val", [0, 12.0, ("frame100", "frame200")])
    def test_typechecking(self, func, val):
        with pytest.raises(TypeError):
            func(val)


class TestGenerateFramecode:

    @pytest.mark.parametrize("n, framecode_type, expected_result", [
            (6, "format_code", "{:06d}"),
            (6, "modulo", "%06d"),
            (6, "numbersign", "######")
    ])
    def test_generate_framecode_valid_width(self, n, framecode_type, expected_result):
        assert fp.generate_framecode(framecode_type, n) == expected_result

    @pytest.mark.parametrize("n", (0, -3))
    def test_generate_framecode_invalid_width(self, n, fc_type_non_digit):
        with pytest.raises(ValueError, match=r"\'width\' must be positive\."):
            fp.generate_framecode(fc_type_non_digit, n)

    def test_generate_framecode_nonexistent_type(self):
        with pytest.raises(ValueError, match=r"\'n/a' is not a supported framecode type\."):
            fp.generate_framecode("n/a", 10)

class TestTranslation:

    @pytest.fixture(scope="class", params = ["format_code", "modulo", "numbersign"])
    def to_type(self, request):
        yield request.param

    def test_equivalent_framecodes(self, encoded_filename, sequence_data, to_type):
        assert (fp.translate_framecode(encoded_filename, to_type)
            == sequence_data[to_type])

    def test_translation_from_digits(self, input_filename, sequence_data, to_type):
        assert (fp.translate_framecode(input_filename, to_type) 
            == sequence_data[to_type])

    def test_translation_to_digits(self):
        with pytest.raises(ValueError, match = "Cannot generate framecode of type 'digits'"):
            fp.translate_framecode("file####.exr", "digits")

    def test_translation_without_framecode(self, non_sequence_filename, to_type):
        assert fp.translate_framecode(non_sequence_filename, to_type) == non_sequence_filename

class TestRegex:
    
    @pytest.mark.parametrize("width_option", ["any", "min", "max", "exact"])
    def test_regex_against_self(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        assert re.fullmatch(regex, str(input_filename)) is not None

    @pytest.mark.parametrize("width_option", ["any", "min", "max", "exact"])
    def test_regex_without_frame_number(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        name = fp.replace_framecode(input_filename, "")
        assert re.fullmatch(regex, name) is None

    @pytest.mark.parametrize("width_option", ["any", "min", "max", "exact"])
    def test_regex_frame_number_replaced_with_non_digits(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        name = fp.replace_framecode(input_filename, "FOOBAR")
        assert re.fullmatch(regex, name) is None
    
    @pytest.mark.parametrize("width_option", ["any", "max"])
    def test_regex_with_narrower_frame_number_true(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        width = fp.get_framecode_width(input_filename)
        name = fp.replace_framecode(input_filename, "1" * (width - 1))
        assert re.fullmatch(regex, name) is not None

    @pytest.mark.parametrize("width_option", ["min", "exact"])
    def test_regex_with_narrower_frame_number_false(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        width = fp.get_framecode_width(input_filename)
        name = fp.replace_framecode(input_filename, "1" * (width - 1))
        assert re.fullmatch(regex, name) is None

    @pytest.mark.parametrize("width_option", ["any", "min"])
    def test_regex_with_wider_frame_number_true(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        width = fp.get_framecode_width(input_filename)
        name = fp.replace_framecode(input_filename, "1" * (width + 1) )
        assert re.fullmatch(regex, name) is not None

    @pytest.mark.parametrize("width_option", ["max", "exact"])
    def test_regex_with_wider_frame_number_false(self, input_filename, width_option):
        regex = fp.create_regex(input_filename, width_option)
        width = fp.get_framecode_width(input_filename)
        name = fp.replace_framecode(input_filename, "1" * (width + 1) )
        assert re.fullmatch(regex, name) is None

    @pytest.mark.parametrize("width_option", ["min", "max", "exact", "any"])
    def test_regex_nonsequence_filename_against_self(self, non_sequence_filename, width_option):
        regex = fp.create_regex(non_sequence_filename)
        assert re.fullmatch(regex, non_sequence_filename) is not None
