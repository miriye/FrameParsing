from pathlib import Path
import re

import pytest

from frameparsing import parsing

@pytest.fixture(scope = "module")
def template_instance(input_filename) -> parsing.Template:
    return parsing.Template(input_filename)

class TestCreation:
    def test_valid(self, template_instance, sequence_data):
        assert template_instance == sequence_data["format_code"]

    def test_invalid(self, non_sequence_filename):
        with pytest.raises(ValueError):
            parsing.Template(non_sequence_filename)

class TestProperties:

    @pytest.fixture(scope = "class", params=["format_code", "modulo", "hash", "width"])
    def prop(self, request) -> str:
        return request.param

    def test_get_properties(self, template_instance, sequence_data, prop):
        assert template_instance.__getattribute__(prop) == sequence_data[prop]

    def test_set_properties(self, template_instance, prop):
        with pytest.raises(AttributeError):
            template_instance.__setattr__(prop, None)

class TestRegex:
    # Regex pattern to match filenames of same format
    @pytest.fixture
    def regexp(self, template_instance) -> str:
        return template_instance.regex
    
    def test_against_original_filename(self, regexp, input_filename):
        assert (re.fullmatch(regexp, str(input_filename)) 
                            is not None)
        
    def test_with_different_folder(self, regexp, input_filename):
        filepath = Path(input_filename)
        fake_path = Path("fake_dir") / Path(input_filename).name
        assert fake_path != filepath # Check path replacement worked
        assert re.fullmatch(regexp, str(fake_path)) is None

    def test_with_different_extension(self, regexp, input_filename):
        filepath = Path(input_filename)
        fake_path = filepath.with_suffix(".fake_ext")
        assert fake_path != filepath 
        assert re.fullmatch(regexp, str(fake_path)) is None

    def test_replacement_with_non_digits(self, input_filename, regexp):
        modified_filename = parsing.replace_framecode(input_filename, "foobar")
        assert modified_filename != input_filename
        assert re.fullmatch(regexp, modified_filename) is None

    def test_replacement_with_empty(self, input_filename, regexp):
        modified_filename = parsing.replace_framecode(input_filename, "")
        assert modified_filename != input_filename
        assert re.fullmatch(regexp, modified_filename) is None
    
    @pytest.mark.parametrize("frame_number", [0, 1, -1, 999, 220349353, -20])
    def test_format_against_regex(self, template_instance, regexp, frame_number):
        frame = template_instance.format(frame_number)
        assert re.fullmatch(regexp, frame) is not None

class TestMatch:
    # Tests the "matches" methode of the Template class.

    def test_against_original_filename(self, template_instance, input_filename):
        assert template_instance.matches(input_filename)
        
    def test_against_original_filename_as_path_objecct(self, template_instance, input_filename):
        assert template_instance.matches(Path(input_filename))

    @pytest.mark.parametrize("frame_number", [0, 1, -1, 999, 220349353, -20])
    def test_other_frame_numbers(self, template_instance, frame_number):
        frame = template_instance.format(frame_number)
        assert template_instance.matches(frame)

    def test_surrounding_chars_strict(self, template_instance, input_filename):
        modified_string = f"FOO{input_filename}BAR"
        assert modified_string != input_filename
        assert not template_instance.matches(modified_string)

    def test_surrounding_chars_non_strict(self, template_instance, input_filename):
        modified_string = f"FOO{input_filename}BAR"
        assert modified_string != input_filename
        assert template_instance.matches(modified_string, strict=False)
                            
