
# The identifier read off a file name, checked against the six chains it
# replaces: standard library only, no scan and no Slicer.
slicer_add_python_unittest(SCRIPT test_naming.py)

# check_lib_installed : les contraintes de version, et les orthographes heritees.
slicer_add_python_unittest(SCRIPT test_deps.py)

# ReadSurf, WriteSurf et OFFReader : les cinq copies divergeaient, ces cas
# figent ce qui a ete retenu et les quatre comportements qui changent.
slicer_add_python_unittest(SCRIPT test_surface.py)

# search : les deux parametres qui portent ce que les quinze copies
# faisaient differemment, et rien d autre.
slicer_add_python_unittest(SCRIPT test_fs.py)

# Le tableau de numerotation des dents : la preference etait ignoree des
# qu elle n etait pas le dernier tableau du maillage.
slicer_add_python_unittest(SCRIPT test_labels.py)

# Le canal <filter-progress> : ce sont les octets emis qui comptent, la
# fenetre comparant la valeur recue a des entiers en dur.
slicer_add_python_unittest(SCRIPT test_progress_protocol.py)

# Les requetes typees : ce qui compte est que le champ absent leve
# exactement ce que le dictionnaire levait.
slicer_add_python_unittest(SCRIPT test_requests.py)

# Balaye le depot : toute paire (bibliotheque, version) doit produire une
# chaine que pip accepte. Ce que le grep avait manque deux fois.
slicer_add_python_unittest(SCRIPT test_pip_requirements.py)

# Le rapatriement d un jeu de test : archive ou non, page HTML refusee,
# et un telechargement interrompu qui ne doit pas passer pour complet.
slicer_add_python_unittest(SCRIPT test_testdata.py)

# Ou l agent d ALI CBCT a le droit de se poser : la ligne qui en decidait
# acceptait les coordonnees negatives et refusait la marge rembourree.
slicer_add_python_unittest(SCRIPT test_ali_cbct_bounds.py)

# Ce qui arrete une recherche d ALI CBCT : un nombre de pas, pas des
# secondes de mur. Le meme scan doit rendre le meme repere sur une machine
# chargee comme sur une machine au repos.
slicer_add_python_unittest(SCRIPT test_ali_cbct_budget.py)

# Un repere qu ALI CBCT n a pas trouve est absent du fichier de sortie,
# sans rien pour le dire : la liste part desormais a cote des predictions.
slicer_add_python_unittest(SCRIPT test_ali_cbct_missing.py)
