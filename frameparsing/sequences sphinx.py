__all__ = ["FrameSequence", "find_sequence", "find_all_sequences", "zip_sequences"]

from pathlib import Path
from typing import Sequence, Generator, Tuple, Union, Set

from . import parsing
class FrameSequence():
    """Represents a sequence of filenames that follow the same naming convention,
    with different frame numbers.


    """
    def __init__(self, frames : Sequence[Union[str, Path]]) -> None:
        """
        Create a FrameSequence instance from a series of filenames.
        Please use 'find_sequence' to create a FrameSequence object
        from a series of existing files, or 'find_all_sequences' to create multiple
        FrameSequence objects from a directory.

        :param frames: list of filenames
        :type frames: list
        :raises ValueError: if filenames don't match the same format
        """
        
        self._frames = {Path(frame) for frame in frames}
        self._start = parsing.get_frame_number(self[0])
        self._end = parsing.get_frame_number(self[-1])
        self._name = parsing.Seqname(self[0])
        
        for frame in self:
            if not self.name.matches(frame):
                raise ValueError(f"Item '{frame}' does not match the format '{self.name}'")

    @property    
    def name(self) -> parsing.Seqname: 
        """Formattable string representing the names of image files"""
        return self._name
    
    @property
    def frames(self) -> Set[Path]:
        """Paths to all frames in this FrameSequence."""
        return self._frames
    
    @property
    def start(self) -> int:
        """Frame number of the first frame."""
        return self._start
    
    @property
    def end(self) -> int:
        """Frame number of the last frame."""
        return self._end
    
    @property
    def range(self) -> Tuple[int]:
        """Frame numbers of first and last frames as a tuple (first, last)"""
        return (self.start, self.end)
    
    @property
    def full_range(self) -> Generator[int, None, None]:
        """Frame numbers of all frames in this sequence, in ascending order."""
        return (parsing.get_frame_number(frame) for frame in self)
    
    def __eq__(self, other) -> bool:
        try:
            return self.frames == set(other)
        except TypeError:
            return False
    
    def __contains__(self, frame):
        return Path(frame) in self.frames
    
    def __iter__(self):
        return iter(sorted(self.frames, 
                           key = lambda frame: parsing.get_frame_number(frame)))
    
    def __getitem__(self, i):
        return tuple(self)[i]
    
    def __len__(self):
        return len(self.frames)
    
    def __repr__(self):
        broad_rangestr = f"{self.range[0]}-{self.range[1]}"
        precise_rangestr = parsing.format_numbers(tuple(self.full_range))

        repr = f"{self.name.translate('numbersign')} {broad_rangestr}"
        # Display precise range only if it is different from broad range (i.e the sequence is not continuous)
        repr += f" ({precise_rangestr})" if precise_rangestr != broad_rangestr else ""
        return repr
    
    def get_frame(self, n: int, absolute: bool = True) -> Union[Path, None]:
        """
        Returns the path to frame n.

        :param n: The frame number to look for.
        :type n: int
        :param absolute: Determines how to interpret the frame number.
                If True, retrieve the frame with frame number n.
                If False, retrieve the frame at index n.
                Defaults to True.
        :type absolute: bool, optional
        :raises TypeError: if n is not an int
        :return: the Path to the appropriate frame, or None
        :rtype: Path
        """

        if not isinstance(n, int):
            raise TypeError("'n' must be an integer.")
        
        if absolute:
            frame = Path(self.name.format(n))
            return frame if frame in self else None
        
        else:
            try:
                return self[n]
            except IndexError:
                return None
    
    def get_frames(self, 
                   start: Union[int, None] = None, 
                   end: Union[int, None] = None,
                   step: Union[int, None] = None, 
                   frame_range: Union[Sequence[int], str, None] = None,
                   absolute: bool = True
                   ) -> Generator[Path, None, None]:
        """Yield all frames with the specified frame numbers.

        :param start: The frame to start on. If None, start on the first frame.
                Defaults to None.
        :type start: int, optional
        :param end: The frame to end on. If None, end on the last frame.
                Defaults to None.
        :type end: int, optional
        :param step: Increment between frames.
        :type step: int, optional
        :param frame_range: A specific set of frame numbers, expressed
                either as a sequence of integers, or a string describing a sequence of integers (see
                parsing.parse_numbers for more information). If this parameter is used, it will
                override the 'start', 'end' and 'step' parameters. Defaults to None.
        :type frame_range: str | list, optional
        :param absolute: Determines how to interpret the frame number.
                If True, retrieve the frame with frame number n.
                If False, retrieve the frame at index n.
        :type absolute: bool, optional
        :raises TypeError: if 'frame_range' is not a sequence or string.
        :yield: Path to the next frame
        :rtype: Path

        """

        for param in (start, end, step):
            if param is not None and not isinstance(param, int):
                raise TypeError(f"{param} must be of type 'int' or 'None'.")
        
        # frame_range parameter takes precedence over start and end
        if frame_range is not None:
            if isinstance(frame_range, str):
                frame_range = parsing.parse_numbers(frame_range)

            try:
                iter(frame_range)
            except:
                raise TypeError("'frame_range' must be a sequence of integers" 
                                "or a string representing a sequence of integers")
            
            for frame_number in frame_range:
                yield self.get_frame(frame_number, absolute)

        # frame_range parameter is not used
        else:
            if step is None:
                step = 1

            if start is None:
                if step >= 0:
                    start = self.start if absolute else 0
                else:
                    start = self.end if absolute else len(self) - 1
            if end is None:
                if step >= 0:
                    end = self.end if absolute else len(self) - 1
                else:
                    end = self.start if absolute else 0

            end += 1 if step >= 0 else -1 # Endpoint inclusivity
            for frame_number in range(start, end, step):
                yield self.get_frame(frame_number, absolute)

     
    def index(self, path: Union[str, Path]):
        """Find the index of the given frame path.

        :param path: path to the desired frame
        :type path: Path
        :return: the index of the desired frame in this sequence
        :rtype: int

        """
        return tuple(self).index(Path(path))

def find_sequence(path: str) -> FrameSequence:
    """Find a frame sequence matching the given path or seqname.

    :param path: String or path representing the frames to look for. This can be either a literal filepath
            (e.g 'seq100\\frame000.png') or a representattion (e.g 'seq100\\frame{:03d}.png' or
            'seq100\\frame###.png')
    :type path: Path:
    :returns: FrameSequence instance containing all files in this sequence.
    :rtype: FrameSequence

    """

    path = Path(path)
    seqname = parsing.Seqname(str(path))
    frames = [file for file in path.parent.iterdir() 
              if file.is_file() and seqname.matches(str(file))]
    return FrameSequence(frames)

def find_all_sequences(dir: str = ".", pattern: str = "*.*") -> Tuple[FrameSequence]:
    """Find all frame sequences in the given directory that optionally match a certain pattern.

    :param dir: The directory to search. Defaults to "." (current working directory).
    :type dir: Path, optional
    :param pattern: glob-style pattern to match files against. Defaults to "*.*".
    :type pattern: str, optional
    :return: tuple of FrameSequence objects
    :rtype: tuple
    """
    dir = Path(dir)
    sequences = {}
    for file in dir.glob(pattern):
        # Check if this file matches an existing seqname
        match_generator = (seqname 
                           for seqname in sequences 
                           if seqname.matches(str(file)))

        if match := next(match_generator, None):
            sequences[match].append(file)
        else:
            if parsing.has_framecode(file):
                sequences[parsing.Seqname(file)] = [file]

    return tuple(FrameSequence(seq) for seq in sequences.values())

def zip_sequences(*sequences : Union[Sequence[FrameSequence], None, None], 
                  start: Union[int, None] = None, 
                  end: Union[int, None] = None,
                  step: int = 1,
                  frame_range: Union[Tuple[int], str, None] = None, 
                  absolute: bool = True
                  ) -> Generator[Tuple[Union[FrameSequence, None]], None, None] :

    """
    Iterate over a frame range. For each frame number n, produces a tuple that contains
    frame n of each input FrameSequence.

    :param start: The frame number (if absolute == True) or index
            (if absolute == False) of the first frame to fetch.
            If set to None, will start at the lowest frame number across all sequences, or index 0. 
            Defaults to None
    :type start: int, optional
    :param end: The number (if absolute == True) or index
            (if absolute == False) of the last frame to fetch.
            If set to None, will end once all sequences have been exhausted.
            Defaults to None
    :type end: int, optional
    :param step: Increment between frames, defaults to 1
    :type step: int, optional
    :param frame_range: A specific set of frame numbers, expressed
                either as a sequence of integers, or a string describing a sequence of integers (see
                parsing.parse_numbers for more information). If this parameter is used, it will
                override the 'start', 'end' and 'step' parameters. 
                Defaults to None
    :type frame_range: str | list, optional
    :param absolute: Determines how to handle frame numbers. If True, group together frames
            that have the same frame number in their names. If False, group together frames
            that have the same index within their respective FrameSequences.
            Defaults to True
    :type absolute: bool, optional
    :yield: the next set of frames
    :rtype: tuple
    """
    if step is None:
        step = 1

    # Set start and end to lowest and highest frame numbers if undefined
    if start is None:
        if step >= 0:
            start = min(seq.start for seq in sequences) if absolute else 0
        else:
            start = max(seq.end for seq in sequences) if absolute else max(len(seq) for seq in sequences)
    if end is None:
        if step >= 0:
            end = max(seq.end for seq in sequences) if absolute else max(len(seq) for seq in sequences)
        else:
            end = min(seq.start for seq in sequences) if absolute else 0

    
    zipper = zip(*(seq.get_frames(start=start, 
                                  end=end, 
                                  step=step, 
                                  absolute=absolute,
                                  frame_range = frame_range) for seq in sequences))
    for framegroup in zipper:
        yield framegroup


