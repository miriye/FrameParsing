__all__ = ["generate_framecode", "get_framecode", "get_frame_number",
           "has_framecode", "get_framecode_type", "get_framecode_width", "replace_framecode",
           "replace_framecode", "translate_framecode", "create_regex"]

from os import sep
from pathlib import Path
import re
from typing import Union, Any

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


