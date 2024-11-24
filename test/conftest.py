from typing import List, Tuple, Dict, Union

from itertools import chain
import json
from pathlib import Path
import pytest

FRAMESEQUENCES_FILE = "test\\test_framesequences.json"
NUMBER_RANGES_FILE = "test\\test_numbers.json"

with open(FRAMESEQUENCES_FILE) as f:
    data = json.load(f)
    SEQUENCES = data["SEQUENCES"]
    NON_SEQUENCES = data["NON_SEQUENCES"]
    FC_TYPES = data["FC_TYPES"]
    SEQ_RANGE_PARAMS = data["SEQ_RANGE_PARAMS"]


# PARAMETRIZED TYPES
# All recognized framecode types (digits, format_code, modulo, numbersign)
@pytest.fixture(scope="package" , params = FC_TYPES)
def fc_type(request) -> str:
    return request.param

# All recognized framecode types except digits
@pytest.fixture(scope="package" , params = [fc_type for fc_type in FC_TYPES if fc_type != "digits"])
def fc_type_non_digit(request) -> str:
    return request.param

# Available datatypes for filenames. Most functions in this package should work identically on both.
@pytest.fixture(scope="package" , params = [str, Path])
def filename_dtype(request) -> type:
    return request.param

# PARAMETRIZED FRAME SEQUENCES

# Base fixture containing all data about a frame sequence
@pytest.fixture(scope="package" , params = SEQUENCES)
def sequence_data(request) -> Dict:       
    return request.param

# Example filename contained within the data package. 
# Will return the same filename as a str and then as Path.
@pytest.fixture(scope="package" )
def input_filename(sequence_data, filename_dtype) -> str:
    return filename_dtype(sequence_data["filename"])

# Framecode portion of the filename in all available formats
@pytest.fixture(scope="package" )
def sequence_framecodes(sequence_data) -> Dict:
    return sequence_data["framecodes"]

# Filename as a formattable string (identical to "format_code" framecode type)
@pytest.fixture(scope="package" )
def seqname_filename(sequence_data) -> str:
    return sequence_data["format_code"]

# Frame number in input filename
@pytest.fixture(scope="package" )
def input_frame_number(sequence_data) -> int:
    return sequence_data["frame_number"]

# Filename encoded into one of the available framecode types. 
# Will output both str and Path versions.
@pytest.fixture(scope="package" )
def encoded_filename(fc_type_non_digit, sequence_data, filename_dtype) -> str:
    return filename_dtype(sequence_data[fc_type_non_digit])

# Fill width of the framecode within this filename.
@pytest.fixture(scope="package" )
def framecode_width(sequence_data) -> int:
    return sequence_data["width"]

# Dummy file paths in this sequence
@pytest.fixture(scope="package" )
def sequence_paths(seqname_filename, seq_frame_range) -> Tuple[Path]:
    return tuple(Path(seqname_filename.format(n)) for n in seq_frame_range)

# List of integers representing the frame numbers in this sequence
@pytest.fixture(scope="package" )
def seq_frame_range(sequence_data) -> List[int]:
    return sequence_data["full_range"]

# NON SEQUENCES
@pytest.fixture(scope="package" , params = NON_SEQUENCES)
def non_sequence_filename(request) -> str:
    return request.param

# PARAMETERS TO TEST FUNCTIONS GATHERING FRAME RANGES
@pytest.fixture(scope="package" , params = SEQ_RANGE_PARAMS["start"])
def param_seq_start(request) -> Union[int, None]:
    return request.param

@pytest.fixture(scope="package" , params = SEQ_RANGE_PARAMS["end"])
def param_seq_end(request) -> Union[int, None]:
    return request.param

@pytest.fixture(scope="package" , params = SEQ_RANGE_PARAMS["step"])
def param_seq_step(request) -> Union[int, None]:
    return request.param


# GROUPED TEST DATA

@pytest.fixture(scope="package" )
def all_seqs_data() -> List[Dict]:
    return SEQUENCES

@pytest.fixture(scope="package" )
def all_non_sequence_filenames() -> List[str]:
    return NON_SEQUENCES

@pytest.fixture(scope="package" )
def all_seqs_paths(all_seqs_data) -> List[Tuple[Path]]:

    return tuple(
        tuple(Path(seq["format_code"].format(n)) for n in seq["full_range"])
        for seq in all_seqs_data
    )
   

# Full frame range of all sequences combined
@pytest.fixture(scope="package" )
def combined_frame_range(all_seqs_data) -> List[int]:
    all_frame_numbers = chain(*(seq["full_range"] for seq in all_seqs_data))
    return sorted(set(all_frame_numbers))

# SEQUENCES OF NUMBERS
with open(NUMBER_RANGES_FILE) as f:
    data = json.load(f)
    NUMBER_SEQUENCES = data["SEQUENCES"]
    PY_RANGES = data["RANGES"]
    INVALID_NUMBER_SEQUENCES = data["INVALID_SEQUENCES"]

# Data package for sequence of numbers
@pytest.fixture(scope="package" , params = NUMBER_SEQUENCES)
def number_sequence_data(request) -> Dict:
    return request.param

# Sequence of integers
@pytest.fixture(scope="package" )
def number_sequence(number_sequence_data) -> Tuple[int]:  
    return tuple(number_sequence_data["sequence"])

# String representation of sequence of integers
@pytest.fixture(scope="package" )
def number_string(number_sequence_data) -> str:
    return number_sequence_data["string"]

# Data package for a range test case
@pytest.fixture(scope="package" , params = PY_RANGES)
def py_range_data(request):
    return request.param

# Range object created from test case data
@pytest.fixture(scope="package")
def range_obj(py_range_data) -> range:
    start = py_range_data.get("start", 0)
    end = py_range_data.get("end", 0)
    step = py_range_data.get("step", 1)
    return range(start, end, step)  

# String representation of range
@pytest.fixture(scope="package")
def range_string(py_range_data) -> str:
    return py_range_data["string"]

# Illegal number sequence (contains non-integer data types)
@pytest.fixture(scope="package", params=INVALID_NUMBER_SEQUENCES)
def invalid_number_sequence(request):
    return request.param   

