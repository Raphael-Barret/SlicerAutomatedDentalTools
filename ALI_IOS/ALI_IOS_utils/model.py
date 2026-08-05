# Constants and lookup dictionaries for landmark mappings and model configurations
import numpy as np
from scipy import linalg

LOWER_DENTAL = ['LL7','LL6','LL5','LL4','LL3','LL2','LL1','LR1','LR2','LR3','LR4','LR5','LR6','LR7']
UPPER_DENTAL = ['UL7','UL6','UL5','UL4','UL3','UL2','UL1','UR1','UR2','UR3','UR4','UR5','UR6','UR7']
TYPE_LM = ['O','MB','DB','CL','CB','MG']

LANDMARKS = {
    "L": [tooth + lm for tooth in LOWER_DENTAL for lm in TYPE_LM],
    "U": [tooth + lm for tooth in UPPER_DENTAL for lm in TYPE_LM]
}

LABEL_L = [str(x) for x in range(18, 32)]  # "18" to "31"
LABEL_U = [str(x) for x in range(2, 16)]   # "2" to "15"

# Names written in the predicted MG json, assigned positionally to the 13
# trained teeth taken in arch order (universal ids 19 -> 31). Tooth 25 carries
# the midline name L0MG, so the right side is shifted by one against the tooth
# numbers: LR1MG sits on tooth 26, not 25. Tooth 18 has no MG label (excluded
# from training). Six of these names collide with the training name of a
# DIFFERENT tooth (e.g. LR1MG is the training name of tooth 25 but the output
# name of tooth 26): any translation between the two conventions must decide
# from the whole label set, never label by label.
MG_OUTPUT_NAME = ['LL6MG','LL5MG','LL4MG','LL3MG','LL2MG','LL1MG','L0MG',
                  'LR1MG','LR2MG','LR3MG','LR4MG','LR5MG','LR6MG']

# Where the MG landmark sits relative to the centre of its tooth, in unit-sphere
# space, expressed in the tooth's local frame: (buccal, along-the-arch, vertical).
# Median over the 155 training scans (no test scan used); spread is 0.02-0.03 on
# the buccal and vertical axes, so this is a stable anatomical prior, not a
# per-scan fit. The cameras aim here instead of at a flat "0.2 below the tooth
# centre", which only ever matched the incisors: on the molars the landmark is
# ~0.15 further buccal, which is exactly why it fell outside the render.
MG_AIM_OFFSET = {
    '19': ( 0.149, -0.154, -0.125),   # LL6
    '20': ( 0.130, -0.099, -0.156),   # LL5
    '21': ( 0.077, -0.106, -0.164),   # LL4
    '22': ( 0.035, -0.110, -0.182),   # LL3
    '23': ( 0.012, -0.071, -0.200),   # LL2
    '24': (-0.008, -0.063, -0.202),   # LL1
    '25': (-0.014, -0.057, -0.189),   # L0
    '26': (-0.008, -0.059, -0.199),   # LR1
    '27': ( 0.003, -0.074, -0.190),   # LR2
    '28': ( 0.058, -0.073, -0.186),   # LR3
    '29': ( 0.096, -0.082, -0.171),   # LR4
    '30': ( 0.135, -0.124, -0.168),   # LR5
    '31': ( 0.160, -0.107, -0.156),   # LR6
}

dic_label = {
    'O': {
        **{str(15 - i): LANDMARKS["U"][i*6:i*6+3] for i in range(14)},  # teeth 15 to 2
        **{str(18 + i): LANDMARKS["L"][i*6:i*6+3] for i in range(14)}   # teeth 18 to 31
    },
    'C': {
        **{str(15 - i): LANDMARKS["U"][i*6+3:i*6+5] for i in range(14)},
        **{str(18 + i): LANDMARKS["L"][i*6+3:i*6+5] for i in range(14)}
    },
    # Mucogingival: one landmark per tooth, lower jaw only (universal ids 19 to 31)
    'MG': {
        **{str(19 + i): [MG_OUTPUT_NAME[i]] for i in range(13)}
    }
}

dic_cam = {
    'O': {
        'L': ([0,0,1],
              np.array([0.5,0.,1.0])/linalg.norm([0.5,0.5,1.0]),
              np.array([-0.5,0.,1.0])/linalg.norm([-0.5,-0.5,1.0]),
              np.array([0,0.5,1])/linalg.norm([1,0,1]),
              np.array([0,-0.5,1])/linalg.norm([0,1,1])),
        'U': ([0,0,-1],
              np.array([0.5,0.,-1])/linalg.norm([0.5,0.5,-1]),
              np.array([-0.5,0.,-1])/linalg.norm([-0.5,-0.5,-1]),
              np.array([0,0.5,-1])/linalg.norm([1,0,-1]),
              np.array([0,-0.5,-1])/linalg.norm([0,1,-1]))
    },
    'C': {
        'L': tuple(np.array(vec)/linalg.norm(vec) for vec in [
            [1,0,0], [-1,0,0], [1,-1,0], [-1,-1,0], [1,1,0], [-1,1,0],
            [1,0,0.5], [-1,0,0.5], [1,-1,0.5], [-1,-1,0.5], [1,1,0.5], [-1,1,0.5]
        ]),
        'U': tuple(np.array(vec)/linalg.norm(vec) for vec in [
            [1,0,0], [-1,0,0], [1,-1,0], [-1,-1,0], [1,1,0], [-1,1,0],
            [1,0,-0.5], [-1,0,-0.5], [1,-1,-0.5], [-1,-1,-0.5], [1,1,-0.5], [-1,1,-0.5]
        ])
    },
    # MG uses the adaptive buccal 3-camera scheme computed by the Agent;
    # these directions are kept only so the Agent interface stays uniform.
    'MG': {
        'L': tuple(np.array(vec)/linalg.norm(vec) for vec in [
            [1,0,0], [-1,0,0], [1,-1,0]
        ]),
        'U': tuple(np.array(vec)/linalg.norm(vec) for vec in [
            [1,0,0], [-1,0,0], [1,-1,0]
        ])
    }
}

MODELS_DICT = {
    'O': {'O': 0, 'MB': 1, 'DB': 2},
    'C': {'CL': 0, 'CB': 1},
    'MG': {'MG': 0}
}