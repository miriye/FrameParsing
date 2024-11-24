__all__ = ["Seqname"]

import re
from pathlib import Path

from .parsenames import _Parser

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
    


