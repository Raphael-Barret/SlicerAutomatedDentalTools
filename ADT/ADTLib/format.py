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


def format_timer(seconds):
    """La durée telle que l'affichent les étiquettes de progression.

    Ces trois branches existaient en douze exemplaires, mot pour mot, dans les
    fenêtres d'ALI, ASO, AREG, MedX et AutoMatrix. Le format est conservé au
    caractère près -- c'est une étiquette que l'utilisateur lit pendant le
    traitement, pas un format à moderniser au passage.

        5      -> "Time : 5s"
        192    -> "Time : 3min and 12s"
        3723   -> "Time : 1h, 2min and 3s"

    Une treizieme copie existe, dans `MRI2CBCT.py`, et elle ecrit `"Time: "`
    sans espace avant le deux-points. Elle reste chez elle : l'aligner
    changerait une etiquette que l'utilisateur lit pendant son traitement, ce
    qui n'est pas le sujet de cette passe.
    """
    if seconds < 60:
        return f"Time : {int(seconds)}s"
    if seconds < 3600:
        return f"Time : {int(seconds/60)}min and {int(seconds%60)}s"
    return (f"Time : {int(seconds/3600)}h, {int(seconds%3600/60)}min "
            f"and {int(seconds%60)}s")


def elapsed_since(start_time):
    """Seconds since `start_time`, as returned by `time.time()`."""
    return time.time() - start_time
