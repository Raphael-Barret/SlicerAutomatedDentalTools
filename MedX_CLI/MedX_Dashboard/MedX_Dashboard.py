#!/usr/bin/env python-real
import argparse
import sys, os


# ADTLib sits next to the modules in an installed build, in the directory Slicer
# already has on sys.path. A source tree has no such entry -- a module search
# path only gets there once Slicer finds a module in it, and ADT holds none --
# so the entry points walk up to the holder directory and add it themselves.
_adt_root = os.path.dirname(os.path.realpath(__file__))
while not os.path.isdir(os.path.join(_adt_root, "ADT", "ADTLib")) \
        and _adt_root != os.path.dirname(_adt_root):
    _adt_root = os.path.dirname(_adt_root)
if os.path.join(_adt_root, "ADT") not in sys.path:
    sys.path.append(os.path.join(_adt_root, "ADT"))

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger

logger = get_logger("MedX_dashboard_CLI")

# realpath, not __file__: this CLI sits in a sub-folder, so it is registered
# through a flat folder of symlinks into the source tree. __file__ then names
# the link, whose parent holds no MedX_CLI_utils. Resolving first lands in
# MedX_CLI either way; a built install has the package on sys.path already.
fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.append(fpath)

from MedX_CLI_utils import show_dashboard


def main(args):
    os.makedirs(args.output_folder, exist_ok=True)
    
    show_dashboard(args.summary_folder, args.output_folder)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("summary_folder", type=str)
    parser.add_argument("output_folder", type=str)
    parser.add_argument("log_path", type=str)

    args = parser.parse_args()

    main(args)
