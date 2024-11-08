__all__ = ["parse_numbers", "format_numbers"]

import re
from typing import Sequence, Generator

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







    


