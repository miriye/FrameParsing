from itertools import chain
from pathlib import Path
from random import randint, choice
from shutil import rmtree
from typing import Tuple, Generator

import pytest

import frameparsing as fp

class TestFinding:
    @pytest.fixture(scope="class")
    def frame_dir(self, tmp_path_factory, all_seqs_paths, all_non_sequence_filenames) \
        -> Generator[Path, None, None]:

        tmp_dir = tmp_path_factory.mktemp("frames")

        #for filename in (chain(chain(*all_seqs_paths), all_non_sequence_filenames)):
        for filename in chain(*all_seqs_paths):
            tmp_filepath = tmp_dir / filename
            tmp_filepath.parent.mkdir(parents = True, exist_ok = True)
            tmp_filepath.write_text("Succesfully created file.")

        yield tmp_dir
        
        # Teardown
        rmtree(tmp_dir)

    @pytest.mark.parametrize("frame_number", [0,100,-200, 58203949])
    def test_find_sequence_from_filename(self, frame_dir, template_filename, frame_number):
        sequence = fp.find_sequence(Path(frame_dir) / template_filename.format(frame_number))
        assert str(sequence.name) == str(Path(frame_dir) / template_filename)

    def test_find_sequence_from_formats(self, frame_dir, sequence_data, fc_type_non_digit, template_filename):
        sequence = fp.find_sequence(Path(frame_dir) / sequence_data[fc_type_non_digit])
        assert str(sequence.name) == str(Path(frame_dir) / template_filename)
        
    def test_find_all_sequences(self, frame_dir, all_seqs_data):
        result = {Path(seq.name) for seq in fp.find_all_sequences(frame_dir, "**/*.*")}
        expected_result = {Path(frame_dir) / seq["format_code"] for seq in all_seqs_data}
        assert result == expected_result

class TestFrameSequenceClass:
    @pytest.fixture(scope="class")
    def framesequence_instance(self, sequence_paths) -> fp.FrameSequence:
        return fp.FrameSequence(sequence_paths)
    
    @pytest.mark.parametrize("frames", [
        ("A100.png", "B101.png"), # Different naming convention
        ("A100.png", "A101.jpg"), # Different file extensions
        ("A100.png", "foo\\A101.png") # Not in same directory
    ])
    def test_inconsistent_sequences(self, frames):
        with pytest.raises(ValueError, match = r"'.*' does not match the format '.*'"):
            fp.FrameSequence(frames)

    def test_name(self, framesequence_instance, template_filename):
        assert framesequence_instance.name == template_filename
    
    def test_start(self, framesequence_instance, seq_frame_range):
        assert framesequence_instance.start == min(seq_frame_range)
    
    def test_end(self, framesequence_instance, seq_frame_range):
        assert framesequence_instance.end == max(seq_frame_range)
    
    def test_range(self, framesequence_instance, seq_frame_range):
        bounds = (min(seq_frame_range), max(seq_frame_range))
        assert framesequence_instance.range == bounds

    def test_full_range(self, framesequence_instance, seq_frame_range):
        assert list(framesequence_instance.full_range) == seq_frame_range

    def test_equality(self, framesequence_instance, sequence_paths):
        assert framesequence_instance == sequence_paths
        
    def test_contains_true(self, framesequence_instance, template_filename, filename_dtype, seq_frame_range):
        frame_number = choice(seq_frame_range) # Randomly pick a frame
        test_filename = template_filename.format(frame_number)
        test_filename = filename_dtype(test_filename)
        assert test_filename in framesequence_instance

    def test_contains_false(self, framesequence_instance, template_filename, filename_dtype, seq_frame_range):
        frame_number = min(seq_frame_range) - 1
        test_filename = template_filename.format(frame_number)
        test_filename = filename_dtype(test_filename)
        assert test_filename not in framesequence_instance

    def test_iter(self, framesequence_instance, sequence_paths):
        assert tuple(framesequence_instance) == tuple(sequence_paths)

    def test_index(self, framesequence_instance, sequence_paths, filename_dtype):
        for _ in range(5):
            frame = choice(sequence_paths) # Randomly pick a frame
            assert sequence_paths.index(frame) == framesequence_instance.index(filename_dtype(frame))

    def test_getitem(self, framesequence_instance, template_filename, seq_frame_range):
        for _ in range(5):
            frame_index = randint(0, len(seq_frame_range) - 1) # Randomly pick a frame
            frame_number = seq_frame_range[frame_index]
            expected_filename = template_filename.format(frame_number)
            assert framesequence_instance[frame_index] == Path(expected_filename)

    def test_getitem_out_of_range(self, framesequence_instance, seq_frame_range):
        frame_index = len(seq_frame_range)
        with pytest.raises(IndexError):
            framesequence_instance[frame_index]

    def test_length(self, framesequence_instance, seq_frame_range):
        assert len(framesequence_instance) == len(seq_frame_range)

    def test_get_frame(self, framesequence_instance, template_filename, seq_frame_range):
        frame_number = choice(seq_frame_range)
        expected_filename = template_filename.format(frame_number)
        assert framesequence_instance.get_frame(frame_number) == Path(expected_filename)

    def test_get_frame_none(self, framesequence_instance, seq_frame_range):
        frame_number = min(seq_frame_range) - 1
        assert framesequence_instance.get_frame(frame_number) is None

    def test_get_frame_relative(self, framesequence_instance, template_filename, seq_frame_range):
        frame_index = randint(0, len(seq_frame_range) - 1)
        frame_number = seq_frame_range[frame_index]
        expected_filename = template_filename.format(frame_number)
        assert framesequence_instance.get_frame(frame_index, absolute=False) == Path(expected_filename)

    def test_get_frame_relative_none(self, framesequence_instance, seq_frame_range):
        frame_index = len(seq_frame_range)
        assert framesequence_instance.get_frame(frame_index, absolute=False) is None

    @pytest.mark.parametrize("absolute", [True, False])
    def test_get_frames_all(self, framesequence_instance, absolute):
        all_frames = tuple(frame for frame in framesequence_instance.get_frames(absolute=True) 
                           if frame is not None)
        assert all_frames == tuple(framesequence_instance)

    
    def test_get_frames_with_params_absolute(self, 
                                             framesequence_instance, 
                                             param_seq_start, 
                                             param_seq_end, 
                                             param_seq_step):

        
        start, end, step = param_seq_start, param_seq_end, param_seq_step

        # Reverse direction for negative ranges
        if (step is not None) and (step > 0):
            start, end = end, start

        frames = framesequence_instance.get_frames(start=start, end=end, step=step)

        if step is None: step = 1

        # If start and end are not set in the method call, the result should start at and end at the
        # First and last possible frames of all sequences combined
        if start is None: 
            if step >= 0:
                start = framesequence_instance.start
            else:
                start = framesequence_instance.end
        if end is None: 
            if step >= 0:
                end = framesequence_instance.end
            else:
                end = framesequence_instance.start
        
        end += 1 if step >= 0 else -1

        # Check each frame has the expected frame number
        for n in range(start, end, step):
            frame = next(frames)
            print(f"n: {n}  FRAME: {frame}")
            assert (frame is None) or (fp.get_frame_number(frame) == n)

        # Check there aren't more frames than there should be    
        with pytest.raises(StopIteration):
            next(frames)


    def test_get_frames_with_params_relative(self, 
                                             framesequence_instance,
                                             seq_frame_range, 
                                             param_seq_start, 
                                             param_seq_end, 
                                             param_seq_step):

        start, end, step = param_seq_start, param_seq_end, param_seq_step

        # Reverse direction for negative step
        if (step is not None) and (step > 0):
            start, end = end, start

        frames = framesequence_instance.get_frames(start=start, end=end, step=step, absolute=False)

        if step is None:
            step = 1
        
        # If start and/or end are not set in the method call, the result should start at and end at the
        # First and/or last possible frames
        if start is None:
            if step >= 0:
                start = 0
            else:
                start = len(seq_frame_range) - 1
        if end is None:
            if step >= 0:
                end = len(seq_frame_range)
            else:
                end = -1
        else:
            end += 1 if step >=0 else -1
            
        for n in range(start, end, step):
            try: 
                expected_frame_number = seq_frame_range[n]          
            except:
                expected_frame_number = None
            frame = next(frames)
            assert ((frame is None and expected_frame_number is None) 
                or (fp.get_frame_number(frame)) == expected_frame_number)

        # Check there aren't more frames than there should be    
        with pytest.raises(StopIteration):
            next(frames)

    @pytest.mark.parametrize("range_arg", ["number_string", "number_sequence"])
    def test_get_frames_with_frame_range_absolute(
        self, 
        framesequence_instance, 
        number_sequence, 
        seq_frame_range,
        range_arg,
        request):
        # Test both number_sequence and equivalent number_string
        frames = framesequence_instance.get_frames(frame_range = request.getfixturevalue(range_arg))
        for n in number_sequence:
            frame = next(frames)
            assert ((n not in seq_frame_range and frame is None)
                    or fp.get_frame_number(frame) == n)
        
    @pytest.mark.parametrize("range_arg", ["number_string", "number_sequence"])        
    def test_get_frames_with_frame_range_relative(self, 
                                                   framesequence_instance, 
                                                   range_arg,
                                                   number_sequence, 
                                                   seq_frame_range,
                                                   request):
        frames = framesequence_instance.get_frames(
            frame_range = request.getfixturevalue(range_arg),
            absolute=False)
        for n in number_sequence:
            frame = next(frames)
            assert frame is None or fp.get_frame_number(frame) == seq_frame_range[n]

        # Check all frames are accounted for
        with pytest.raises(StopIteration):
            next(frames)

    @pytest.mark.parametrize("start, end, step, frame_range_arg", [
        (0, 10, 2, [100,101,102,103,104,105]),
        (0, 10, 2, "100-105")
    ])
    def test_get_frames_frame_range_overrides_other_params(
        self, framesequence_instance, start, end, step, seq_frame_range, frame_range_arg):
        frames = framesequence_instance.get_frames(start=start, end=end, step=step, frame_range=frame_range_arg)
        for n in range(100, 106):
            frame = next(frames)
            assert ((n not in seq_frame_range and frame is None)
                    or (fp.get_frame_number(frame)) == n)

    def test_no_duplicates(self, sequence_paths):
        paths = tuple(sequence_paths)
        duplicated_paths = paths + paths # Duplicate all paths
        assert len(duplicated_paths) == len(paths) * 2
        instance = fp.FrameSequence(paths) 
        assert len(instance) == len(paths) # Assert all duplicates were purged when creating instance
   
class TestZipSequences:
    @pytest.fixture(scope="class")
    def all_instances(self, all_seqs_paths) -> Tuple[fp.FrameSequence]:
        return tuple(fp.FrameSequence(
            paths) for paths in all_seqs_paths)

    def test_zip_absolute(self, 
                          param_seq_start, 
                          param_seq_end, 
                          param_seq_step, 
                          all_instances, 
                          combined_frame_range):

        start, end, step = param_seq_start, param_seq_end, param_seq_step

        if step is not None and step < 0:
            start, end = end, start
        
        zipper = fp.zip_sequences(*all_instances, start=start, end=end, step=step)

        if step is None:
            step = 1

        if start is None:
            if step >= 0:
                start = combined_frame_range[0]
            else:
                start = combined_frame_range[-1]
        if end is None:
            if step >= 0:
                end = combined_frame_range[-1]
            else:
                end = combined_frame_range[0]

        end += 1 if step >= 0 else -1

        for frame_group, n in zip(zipper, range(start, end, step)):
        
            for frame, instance in zip(frame_group, all_instances):
                # Check frames appear in the correct order in the zip group
                assert frame is None or instance.name.matches(frame)
                # Check frame number is correct
                assert frame is None or fp.get_frame_number(frame) == n

        # Check zipper covers entire expected range
        with pytest.raises(StopIteration):
            next(zipper)


    def test_zip_relative(self, 
                          param_seq_start, 
                          param_seq_end, 
                          param_seq_step, 
                          all_instances):
        
        start, end, step = param_seq_start, param_seq_end, param_seq_step

        if step is not None and step < 0:
            start, end = end, start
        
        zipper = fp.zip_sequences(*all_instances, start=start, end=end, step=step, absolute=False)

        if step is None:
            step = 1

        if start is None:
            if step >= 0:
                start = 0
            else:
                start = max(len(seq) for seq in all_instances)
        if end is None:
            if step >= 0:
                end = max(len(seq) for seq in all_instances)
            else:
                end = 0

        for frame_group, n in zip(zipper, range(start, end, step)):
        
            for frame, instance in zip(frame_group, all_instances):
                # Check frames appear in the correct order in the zip group
                assert frame is None or instance.name.matches(frame)
                # Check frame number is correct
                assert frame == instance.get_frame(n, absolute=False)
        
        # Check zipper covers entire expected range
        with pytest.raises(StopIteration):
            next(zipper)

    @pytest.mark.parametrize("range_arg", ["number_string", "number_sequence"])           
    def test_zip_with_frame_range_absolute(self, all_instances, range_arg, number_sequence, request):
        zipper = fp.zip_sequences(*all_instances, frame_range=request.getfixturevalue(range_arg))

        for frame_group, n in zip(zipper, number_sequence):
        
            for frame, instance in zip(frame_group, all_instances):
                # Check frames appear in the correct order in the zip group
                assert frame is None or instance.name.matches(frame)
                # Check frame number is correct
                assert frame is None or fp.get_frame_number(frame) == n

        # Check zipper covers entire expected range
        with pytest.raises(StopIteration):
            next(zipper)

    @pytest.mark.parametrize("range_arg", ["number_string", "number_sequence"])           
    def test_zip_with_frame_range_relative(self, all_instances, range_arg, number_sequence, request):
        zipper = fp.zip_sequences(*all_instances, frame_range=request.getfixturevalue(range_arg),
                                         absolute = False)

        for frame_group, n in zip(zipper, number_sequence):
        
            for frame, instance in zip(frame_group, all_instances):
                # Check frames appear in the correct order in the zip group
                assert frame is None or instance.name.matches(frame)
                # Check frame number is correct
                assert frame == instance.get_frame(n, absolute=False)

        # Check zipper covers entire expected range
        with pytest.raises(StopIteration):
            next(zipper)



        
    
    
    
    
    
            

    
        

        


                  
        



   
        



    