"""Formatting shared by the modules' installation and progress labels.

Pure functions, standard library only: this module is imported by the widgets
inside Slicer and must stay importable from the lean Conda environment too.
"""
import time


def format_elapsed(seconds):
    """Seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def elapsed_since(start_time):
    """Seconds since `start_time`, as returned by `time.time()`."""
    return time.time() - start_time
