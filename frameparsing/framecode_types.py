__all__ = ["FRAMECODE_TYPES"]

FRAMECODE_TYPES = {
    
    "format_code": {
        "pattern": r"[{]:0(\d+)d*[}]", # Matches Python format code with "0" as the fill characcter
        "width" : int,  # Function to apply to capture group to obtain width
        "generate_framecode" : lambda n : f"{{:0{n}d}}" # Function to create a framecode with width n
    },

    "modulo": {
        "pattern": r"%0(\d+)d", # Matches C-style modulo format with "0" as the fill character
        "width" : int,
        "generate_framecode" : lambda n : f"%0{n}d" 
    },

    "numbersign": {
        "pattern": r"(#+)(?!.*#)", # Matches last set of "#"
        "width" : len,
        "generate_framecode" : lambda n : "#" * n
    },

    "digits": {
        "pattern": r"(-?\d+)(?!.*\d)", # Matches last set of digits
        "width" : len,
        "generate_framecode" : None
    },
    
}