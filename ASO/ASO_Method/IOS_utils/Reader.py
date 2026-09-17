"""Lecture et ecriture de maillages : le tout vit maintenant dans ADTLib.

Ce fichier portait une copie d'`OFFReader`, de `ReadSurf` et de `WriteSurf`.
Les trois existaient a l'identique ou presque dans quatre autres modules ; le
detail de ce qui divergeait et de ce qui a ete retenu est dans
`ADTLib/io/surface.py`. Ce module reste pour les appelants qui l'importent par
son chemin d'origine.

`WriteSurf` d'ici forcait la sortie en `.vtk` quelle que soit l'extension
d'entree. Son unique appelant, le contournement de la segmentation dans
`IOS.py`, voulait justement cette conversion : il demande desormais le `.vtk`
dans le nom qu'il passe, au lieu que la fonction le decide pour tout le monde.
"""
from ADTLib.io.surface import OFFReader, ReadSurf, WriteSurf  # noqa: F401  (re-exporte)
