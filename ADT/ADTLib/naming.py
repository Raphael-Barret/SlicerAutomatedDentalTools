"""Reading a patient identifier off a file name.

Six sites built the same identifier by chaining fourteen `.split(...)[0]` calls
in the same order, and the order is load-bearing: a longer marker has to be cut
before a shorter one it contains, or `_Scanreg` loses its tail to `_Scan` and
two files stop pairing. Written once, that ordering is a property of this
module instead of something each copy has to remember.

Standard library only: the CLIs call this from the Conda environment.

TIMEPOINT-SUFFIX -- still not implemented, but now in one place. The identifier
is what is left once these markers are cut, and the only timepoints among them
are _T1 and _T2, so an input named P001_T3.nii.gz keeps the id "P001_T3" and
never matches the P001_T4.nii.gz in the T2 folder: the pair is dropped rather
than raising. Accepting any _T<digit> means adding a `re.sub(r"_[Tt]\\d+$", "")`
to `patient_id` below -- and *also* to the sites that still carry their own
chain, which are not the same list: ASO_Method/CBCT.py, ASO_CBCT_utils/utils.py,
AREG_Method/IOSCBCT.py and MRI2CBCT_CLI_utils/TMJ_crop.py. Grep for
TIMEPOINT-SUFFIX to find them.
"""

# Cut longest-first where one marker contains another: _Scanreg before _Scan,
# _MAND before _MD, _MAX before _MX. This is the order the six chains used.
PATIENT_ID_MARKERS = (
    "_Scan", "_scan", "_Or", "_OR", "_MAND", "_MD", "_MAX", "_MX",
    "_CB", "_lm", "_T2", "_T1", "_Cl", ".",
)


def patient_id(name, markers=PATIENT_ID_MARKERS):
    """The identifier that pairs a scan with its follow-up.

    `name` is a base name, not a path: the callers pass os.path.basename.
    """
    for marker in markers:
        name = name.split(marker)[0]
    return name
