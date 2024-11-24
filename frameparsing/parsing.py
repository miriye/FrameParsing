__all__ = ["generate_framecode", "get_framecode", "get_frame_number",
           "has_framecode", "get_framecode_type", "get_framecode_width", "replace_framecode",
           "replace_framecode", "translate_framecode", "create_regex",
           "parse_numbers", "format_numbers", "Seqname"]

from os import sep
from pathlib import Path
import re
from typing import Any, Generator, Sequence, Union

from .framecode_types import FRAMECODE_TYPES

class _Parser():
    """
    Class to parse and manipulate strings containing frame numbers, format codes or placeholders.
    """
    
    def __init__(self, string : Union[str, Path]) -> None :
        """
        Searches for a framecode in this string or pathlike object and creates an instance if one is found.
        Note: if the input is or resembles a path, only the basename will be searched for a framecode.

        Supported framecodes are:
        - 'format_code' : A Python 3-style format specifier.
        - 'modulo' : A C-style modulo format specifier.
        - 'numbersign' : The last continuous set of '#' characters in string, where the number of 
            consecutive '#' characters should equal the numebr of digits expected in a filename
            of this format.
        - 'digits' : the first continuous set of digits in a string.

        The string will look for each of these formats in the order listed above,
        and accept the first match.

        Args:
            string: The string to analyze.

        Raises:
            ValueError: if no framecode is found in this string.
        """
        self._string = string

        # Iterate over available encoding types in order to find a match
        for fc_type, fc_attrs in FRAMECODE_TYPES.items():
            if match := re.search(fc_attrs["pattern"], self.path.stem):
                break

        if match is None:
            raise ValueError(f"No framecode found in '{string}'")

        self._match = match
        self._type = fc_type
        
    @property
    def string(self) -> str:
        """The string this instance was created from."""
        return self._string
    
    @property
    def path(self) -> Path:
        """Path object created from string used to instantiate this object."""
        return Path(self.string)
    
    @property
    def match(self) -> re.Match:
        """re.Match object holding information about the framecode found in this string."""
        return self._match
          
    @property
    def type(self) -> str:
        """Type of framecode found in this string"""
        return self._type
    
    @property
    def framecode(self) -> str:
        """Frame number/framecode within this string"""
        return self._match.group()
    
    @property
    def width(self) -> int:
        """Frame number width represented by the framecode"""
        width_func = FRAMECODE_TYPES[self.type]["width"]
        return width_func(self._match.group(1))
          
    def replace_framecode(self, repl: str) -> str:
        """Replace the framecode in this string with a string.

        Args:
            repl: The string to replace the framecode with.

        Returns:
            The string with its framecode replaced.
        """
   
        new_stem = re.sub(self.match.re.pattern, repl, self.path.stem)
        return str(self.path.parent / (new_stem + self.path.suffix))
    
    def translate(self, to_type: str, **kwargs: Any) -> str:
        """
        Translate this string to another framecode type.

        Args:
            to_type: The framecodetype to translate this string to.

        Returns:
            The string with its framecode translated.
        """
        if to_type == "regex":
            return self.create_regex(**kwargs)
        
        framecode = generate_framecode(to_type, self.width)
        return self.replace_framecode(framecode)
    
    def create_regex(self, width: str = "any") -> str:
        """
        Create regex pattern that will match any string that has the same name 
        and variable frame number.

        Args:
            width: Defines how frame number width will be matched. Options:
                any (default): Frame numbers of any width will match.
                min: Frame numbers with the same width or wider will match.
                max: Frame numbers with the same width or narrower will match
                exact: Only frame numbers with the same width will match.      
        """

        width_options = {                                           
            "any" : r"-?\d+", 
            # The regex for posititve and negative integers has to be different
            #  due to the way format specifiers wotk. For example, given format specifier
            # '{:03d}', the number 4 will be formatted as "004" and -4 will be formatted as "-04".
            # "Both strings are considered to have a fill width of 3, but regex will count 2 digits 
            # for the first string and 2 for the second.

            "exact" : fr"(?:\d{{{self.width}}}|-\d{{{self.width-1}}})", # width or -(width-1)
            "min" : fr"(?:\d{{{self.width},}}|-\d{{{self.width-1},}})", # (width, inf) or -(width-1, inf)
            "max" : fr"(?:\d{{1,{self.width}}}|-\d{{1,{self.width-1}}})" # (1, width) or -(1, wdith-1)
            
        }
        

        if not isinstance(width, str):
            raise TypeError("'width' must be a string.")
        
        regex_code = width_options.get(width, None)
        if not regex_code:
            raise ValueError(f"'{width}' not supported as an option."
                             f"""Available options: '{"', '".join(width_options)}'.""")

        # Deconstruct the original string and reconstruct it with special characters escaped 
        stem_parts = re.split(self.match.re.pattern, self.path.stem) # Extract everything before and after framecode
        new_stem = re.escape(stem_parts[0]) + regex_code + re.escape(stem_parts[-1])
        new_name = new_stem + re.escape(self.path.suffix)

        if (parent := str(self.path.parent)) == ".": # no parent directory
            return new_name       
        else:
            return re.escape(parent) + re.escape(sep) + new_name # sep == os.sep
        
    
def generate_framecode(framecode_type: str, width: int) -> str:
    """Generate a format code or frame number placeholder.

    Args:
        framecode_type: The framecode type to output. Currently supported:
            'format_code', 'modulo', 'numbersign'
        width: The (minimum) fill width of the output code.
    
    Returns:
        The output code.
    """
    
    if not isinstance(width, int):
        raise TypeError("'width' must be an integer.")
    
    if width < 1:
        raise ValueError("'width' must be positive.")
    
    if not isinstance(framecode_type, str):
        raise TypeError("'framecode_type' must be a string.")
    
    # Fetch data of desired framecode type
    attrs = FRAMECODE_TYPES.get(framecode_type, None)
    if not attrs:
        raise ValueError(f"'{framecode_type}' is not a supported framecode type.")
    
    # Fetch the code generation function belonging to the selected framecode type
    generate = attrs.get("generate_framecode")
    if not generate:
        raise ValueError(f"Cannot generate framecode of type '{framecode_type}'")
    
    return generate(width)

def get_framecode(string: Union[str, Path]) -> str:
    """
    Extract framecode (part that represents a frame number) from a string or Path.
    Note that if the input is or resembles a path, only the basename 
    will be checked for a frame number.

    Args:
        string: The string or Path to parse.

    Returns:
        The framecode portion of the string.
    """
    try:
        parser = _Parser(string)
        return parser.framecode
    except ValueError:
        return None
       
def get_frame_number(string: Union[str, Path]) -> int :
    """
    Extract frame number from the given string or Path. The frame number is defined as
    the last consecutive set of digits in the string. Note that if the input is or resembles
    a path, only the basename will be checked for a frame number.

    Args:
        string: The string or Path to extract the frame number form.

    Returns:
        The frame number found in this string as an integer.
    """
    try:
        parser = _Parser(string)
        if parser.type == "digits":
            return int(parser.framecode)
    except ValueError:
        return None
    
    
    
def has_framecode(string: Union[str, Path]) -> bool:
    """
    Determine whether the given string or path contains a framecode.

    Args:
        string: The string or Path to analyze.

    Returns:
        True if a framecode is found, False if not.
    """
    try:
        _Parser(string)
        return True
    except ValueError:
        return False

def get_framecode_type(string: str) -> Union[str, None]:
    """
    Determine the framecode type of this string or Path.

    Args:
        string: The string or Path to analyze.
    Returns:
        The determined framecode type. None if no framecode is found.
    """
    try:
        parser = _Parser(string)
        return parser.type
    except ValueError:
        return None

def get_framecode_width(string: str) -> Union[str, None]:
    """
    Determine the fill width of the framecode in string or Path.

    Args:
        string: The string or Path to analyze.

    Returns:
        The fill width. None if not framecode is found.
    """
    try:
        parser = _Parser(string)
        return parser.width
    except ValueError:
        return None

def replace_framecode(string: str, repl: str) -> str :
    """Replace framecode in this string or Path.
    
    Args:
        string: The string to search.
        repl: The string to sub in.

    Returns:
        string: The input string with its framecode replaced. If no framecode is found, returns the
            original string.
    """
    try:
        parser = _Parser(string)
        return parser.replace_framecode(repl)
    except ValueError:
        return string

def translate_framecode(string: Union[str, Path], to_type: str) -> str:
    """
    Translate framecode to specified type. If no framecode is found, return the original string.

    Args:
        string: the string or Path to translate.
        to_type: the framecode type to translate to.

    Returns:
        The input string with its framecode translated. 
        Returns the original string if no framecode was found.

    Raises:
        ValueError: if "to_type" is set to a framecode type that 
            does not exist or does not allow framecode creation.
      
    """

    try:
        parser = _Parser(string)
    except ValueError:
        return string
      
    return parser.translate(to_type)
    
def create_regex(string: Union[str, Path], width: str = "any") -> str:
    """
    Create regex pattern to match paths/strings resembling the format of the input string.

    Args:
        string: The string or path to use as a basis for the pattern.
        Args:
            width: Defines how frame number width will be matched. Options:
                - any (default): Frame numbers of any width will match.
                - min: Frame numbers with the same width or wider will match.
                - max: Frame numbers with the same width or narrower will match
                - exact: Only frame numbers with the same width will match.      

    Returns:
        The resulting regex pattern. If no framecode is found, will return a regex pattern
            that matches the original string exactly.
    """
    try:
        parser = _Parser(string)       
    except ValueError:
        return re.escape(string) # return a regex that will match the original string/path
    
    return parser.create_regex(width)



def parse_numbers(string: str) -> Generator[int, None, None]:

    """
    Generate a set of integers from a string representation.

    The following syntax, and any combination thereof, is supported:
        - A-B: All integers from A to B (both inclusive)
        - A-B-C: All integers from A to B (both inclusive) in increments of C
        - A, B, C: Integers A, B and C
        - A B C: Integers A, B and C
        - A: Integer A, where A is a negative number
    Units can be separated by either spaces or commas. Any syntax not understood will be skipped over.

    Args:
        string: The string to parse.

    Yields:
        The next integer found in the string representation.
    """

    # Strip any whitespace not separating two numbers     
    string = re.sub(r"\s(?!\d)", "", string)
    string = re.sub(r"(?<!\d)\s", "", string)
    
    pattern = r"""
                (-?\d+) # Captures A
                (?:-(-?\d+))? # Captures B
                (?:x(-?\d+))? # Captures C
               """

    for match in re.finditer(pattern, string, flags=re.VERBOSE):

        # Convert any captured numbers to integers
        A, B, C = (int(n) 
                   if n is not None else None
                   for n in match.groups() 
                   )

        
        if B is None and C is None: # Single number (A)
            yield A
            
        elif C is not None and B is None: # Repeated number (AxC)
            for i in range(C):
                yield A

        else: # Range (A-B) or (A-BxC)
            # Set C to 1 for ranges with unspecified step
            if C is None: C = 1

            # Make endpoint inclusive
            B +=1 if C >= 0 else -1
            
            for i in range (A, B, C):
                yield i


def format_numbers(numbers: Sequence[int]) -> str: 
    """Generates a string representation of an iterable containing integers.

    Args:
        numbers: Iterable containing integers

    Returns:
        string (str): String representation of input numbers (example: "1-5, 10-16x2, 20, 21")
    """

    def typecheck(item):
        if not isinstance(item, int):
            raise TypeError("'numbers' should only contain integers.")
        
    def build_string():
        if step == 0: # Repeated numbers
                    string = f"{seq_start}x{seq_length}" 
        elif step == 1: # Step will not be written if it is 1
            string = f"{seq_start}-{seq_end}"
        else:
            string = f"{seq_start}-{seq_end}x{step}"
        return string    
    
    try:
        numbers = iter(numbers)
    except TypeError:
        raise TypeError("'numbers' must be an iterable.")
    
    output = []

    # Evaluate three numbers at a time: seq_start, seq_end and next_number
    # Fetch 1st number
    try:
        seq_start = next(numbers)
        typecheck(seq_start)
    except StopIteration: 
        raise ValueError(f"Input is empty.")
    
    # Fetch 2nd number
    try:
        seq_end = next(numbers)
        typecheck(seq_end)
    except StopIteration: 
        return str(seq_start)

    # Fetch 3rd number
    try:
        next_number = next(numbers)
        typecheck(next_number)
    except StopIteration:
        if seq_start == seq_end:
            return f"{seq_start}x2"
        else: 
            return f"{seq_start}, {seq_end}"

    # The iterable contains at least three numbers, so we can proceed.   
    step = seq_end - seq_start
    seq_length = 2

    while True:
        # Ensure all items are integers
        for n in (seq_start, seq_end, next_number):
            typecheck(n)

        if next_number == seq_start + step * seq_length: # next number forms part of arithmetic sequence

            seq_end = next_number
            seq_length += 1

            try: # Proceed to next number             
                next_number = next(numbers)
                
            except StopIteration:
                output.append(build_string())
                break

        else: # Next number breaks arithmetic sequence 
                               
            if seq_length >= 3 or step == 0: 
                output.append(build_string())
                
                # Shift 2 numbers forward and continue checking
                seq_start = next_number 
                try:                                   
                    seq_end = next(numbers)
                    typecheck(seq_end)
                    step = seq_end - seq_start
                except StopIteration: # last number checked was last in sequence
                    output.append(str(seq_start))
                    break

            else: # Not a sequence or repeat 
                output.append((str(seq_start)))

                # Shift 1 number forward and continue checking
                seq_start = seq_end
                seq_end = next_number
                step = seq_end - seq_start

            try:            
                next_number = next(numbers)
            except StopIteration:
                if step == 0:
                    output.append(f"{seq_start}x{seq_length}")
                else:
                    output.extend((str(seq_start), str(seq_end)))
                break

            step = seq_end - seq_start
            seq_length = 2
            
    return ", ".join(output)


class Seqname(str):
    """Formattable string representing the names of a sequence of files."""
    def __new__(cls, string, *args, **kwargs):
        parser = _Parser(string)
        return super().__new__(cls, parser.translate("format_code"))
    
    def __init__(self, string: str):
        self._parser = _Parser(string)

    @property
    def format_code(self) -> str:
        """String in "format_code" format. E.g: "frame{:04d}.png"."""
        return self._parser.translate("format_code")
    
    @property
    def modulo(self) -> str:
        """String in "modulo" format. E.g: "frame%04d.png"."""
        return self._parser.translate("modulo")
    
    @property
    def numbersign(self) -> str:
        """String in "numbersign" format. e.g: "frame####.png"."""
        return self._parser.translate("numbersign")
    
    @property
    def regex(self) -> str:
        """Regex that will match files matching this format."""
        return self._parser.create_regex()
    
    @property
    def width(self) -> int:
        """The fill width of the framecode in this seqname."""
        return self._parser.width
    
    def matches(self, string: str, strict: bool = True) -> bool:
        """
        Determine whether the given string matches this format.

        Args:
            string: The string to check for a match.
            strict: If True, match seqname exactly from start to end of string. If False, 
                match anywhere in the string. Defaults to True. 

        Returns:
            True if the string matches this seqname, False if not.
        """
        if isinstance(string, Path):
            string = str(string)

        # Check if string matches seqname (works for digits)
        matchfunc = re.fullmatch if strict else re.search
        try:
            if matchfunc(self.regex, string) is not None:
                return True
        except TypeError:
            raise TypeError("Expected string, bytes-like or Path-like object.")
        
        # Check if seqname would be the same (works for any framecode)
        try:
            other_seqname = Seqname(string)
            return self == other_seqname
        except ValueError:
            return False
    








    



