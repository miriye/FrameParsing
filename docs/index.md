# FrameParsing

FrameParsing is a bundle of tools to handle sequences of image frames. Its main purpose is to find frame sequences based on user specifications, and extract information from filenames.

### Filenames and sequence names

In this package, the portion of a string that represents the frame number is referred to as the **framecode**. In a literal filename, this is simply the frame number. (e.g: "se0100/frame0200.exr" has framecode "0200".) This package will always assume the last continuous set of digits in the *basename* of a file path to be the frame number.

The name of a sequence can be presented in three different formats:

-   **format_code:**  frame{:04d}.png
-	**modulo:** frame%04d.png
-	**numbersign:** frame####.png

In which the framecodes are "{:04d}", "%04d" and "####" respectively.

### Frame range formatting
Additionally, this package contains functionality to extract frame numbers from user friendly strings representing a frame range, such as "1-20, 23, 24". It supports the following syntax:

-   **A:** Integer A
-   **-A:** Integer A, where A is a negative 
-   **A-B:** All integers from A to B (both inclusive)
-   **A-B-C:** All integers from A to B (both inclusive) in increments of C
-   **A, B, C:** Integers A, B and C
-   **A B C:** Integers A, B and C
-   number

### Frame sequences
**FrameSequence** is a class to store image paths that belong to a sequence, and obtain information about the sequence. They can be found using the **find_sequence** and **find_all_sequences** functions. 

