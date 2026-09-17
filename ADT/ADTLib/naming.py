"""Reading a patient identifier off a file name.

Six sites built the same identifier by chaining fourteen `.split(...)[0]` calls
in the same order, and the order is load-bearing: a longer marker has to be cut
before a shorter one it contains, or `_Scanreg` loses its tail to `_Scan` and
two files stop pairing. Written once, that ordering is a property of this
module instead of something each copy has to remember.

Standard library only: the CLIs call this from the Conda environment.

TIMEPOINT-SUFFIX -- toujours pas implémenté, mais désormais à une seule ligne
d'ici. L'identifiant est ce qui reste une fois les marqueurs coupés, et les
seuls timepoints des jeux ci-dessous sont _T1 et _T2 : une entrée nommée
P001_T3.nii.gz garde l'identifiant "P001_T3" et ne rencontre jamais le
P001_T4.nii.gz du dossier T2. La paire est abandonnée, pas signalée.

L'accepter tient en une ligne dans `patient_id`, après la boucle :

    name = re.sub(r"_[Tt]\d+$", "", name)

et elle vaut alors pour **tous** les jeux de marqueurs, ce qui n'était pas le
cas quand dix sites portaient chacun leur chaîne. Ajoutée après la boucle, elle
est strictement additive : un nom que la boucle réduisait déjà n'est pas touché.
Attention tout de même à _T10, que "_T1" coupe aujourd'hui en "P001" -- ce
défaut-là existe avant le changement et ne disparaît pas avec.

Laissé en l'état sciemment : accepter _T3 change quels scans s'apparient, ce
qui est une décision et non un refactor. La réponse supportée reste de nommer
les entrées _T1/_T2.
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

# Les autres jeux de marqueurs du dépôt. Ils ne sont pas fondus dans celui du
# dessus parce qu'ils ne décrivent pas les mêmes fichiers : un même nom n'y
# donne pas le même identifiant, et changer cela déciderait quels scans
# s'apparient. Les nommer ici les rend au moins comparables côte à côte, et
# fait que l'algorithme -- l'ordre des coupes, la partie fragile -- n'existe
# qu'une fois.

#: ASO, orientation CBCT. Coupe `_Scanreg` avant `_Scan`, et ignore les
#: marqueurs d'anatomie (`_MAND`, `_MAX`, `_CB`) que le jeu par défaut retire.
ASO_CBCT_MARKERS = (
    "_scan", "_Scanreg", "_Scan", "_Or", "_OR", "_lm", "_T1", "_T2", ".",
)

#: ASO_CBCT, le CLI. Même vocabulaire que ci-dessus mais dans un autre ordre --
#: `_Or` d'abord -- et sans les timepoints, qui restent donc dans l'identifiant.
ASO_CBCT_CLI_MARKERS = (
    "_Or", "_OR", "_scan", "_Scanreg", "_Scan", "_lm", ".",
)

#: AREG, appariement IOS/CBCT. Volontairement court : il apparie des surfaces
#: dont le nom ne porte ni anatomie ni timepoint.
AREG_IOSCBCT_MARKERS = ("_scan", "_Scanreg", "_lm")

#: MRI2CBCT, recadrage TMJ. Le jeu par défaut plus dix-sept marqueurs propres à
#: cette chaîne : segmentation, masque, prédiction, recadrage, côté, modalité.
TMJ_CROP_MARKERS = PATIENT_ID_MARKERS[:-1] + (
    "_seg", "_Seg", "_mask", "_Mask", "_pred", "_Pred", "_crop", "_Crop",
    "_Left", "_left", "_Right", "_right", "_approximate", "_Approximate",
    "_CBCT", "_MRI", "_MR", ".",
)

#: Retirer le suffixe d'un fichier de points de repère, sans toucher au reste
#: du nom. Utilisé là où l'identifiant complet n'est pas ce qu'on cherche.
LANDMARK_SUFFIX_MARKERS = ("_lm", "_Or", ".")
