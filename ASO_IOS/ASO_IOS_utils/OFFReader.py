"""Le lecteur OFF vit maintenant dans ADTLib.

Les deux exemplaires -- celui-ci et celui d'`ASO/ASO_Method/IOS_utils/Reader.py`
-- etaient identiques au caractere pres, preambule de journalisation mis a part.
Ce module reste pour les appelants qui l'importent par son chemin d'origine.
"""
from ADTLib.io.surface import OFFReader  # noqa: F401  (re-exporte)
