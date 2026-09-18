"""Le canal `<filter-progress>`, nommé une fois.

Les CLI de l'extension parlent à leur interface par une seule voie : une ligne
`<filter-progress>x</filter-progress>` sur la sortie standard. Slicer la lit,
**multiplie x par cent**, et range le résultat sur le nœud du CLI, d'où
`caller.GetProgress()` le ressort côté fenêtre.

Ce facteur cent n'est écrit nulle part, et c'est lui qui a produit les trois
conventions qu'on trouvait dans le dépôt :

- un CLI qui imprime une **fraction** `0.42` fait afficher 42 : c'est l'usage
  prévu, et la barre avance ;
- un CLI qui imprime l'entier `2` fait afficher 200, ce qu'aucune barre ne sait
  représenter. Ce n'est pas une progression, c'est un **événement** : les
  interfaces comparent la valeur à `200` pour savoir qu'un patient de plus est
  fini. Le CLI l'envoie en **impulsion** `0 → 2 → 0`, parce que Slicer ne
  prévient sa fenêtre que lorsque la valeur *change* ;
- et AMASSS, qui recevait les deux, devinait à l'exécution laquelle il tenait
  (`if progress > 1: progress /= 100`).

Ici les trois sont nommées. Les constantes portent la valeur **telle que
l'interface la voit**, puisque c'est là qu'on la compare ; la division par cent
n'existe qu'à un seul endroit, juste en dessous.

Bibliothèque standard seulement : importé depuis l'environnement Conda par les
CLI, et depuis Slicer par les fenêtres.
"""
import sys
import time

# Ce que Slicer fait de la valeur imprimée avant de la donner à la fenêtre.
SCALE = 100

# Les deux événements, dans l'unité où l'interface les lit.
STEP_DONE = 100      # le CLI a imprimé 1 : une étape de plus est finie
PATIENT_DONE = 200   # le CLI a imprimé 2 : un patient de plus est fini

# Slicer ne signale que les changements de valeur : une impulsion doit donc
# redescendre, et laisser à la boucle d'événements le temps de la voir. Le
# délai est celui qu'utilisaient les quatre CLI qui envoyaient déjà 0 → 2 → 0.
PULSE_PAUSE = 0.2


def emit(value, flush=True):
    """Écrit une valeur brute sur le canal. Les deux fonctions suivantes l'appellent."""
    print(f"<filter-progress>{value}</filter-progress>")
    if flush:
        sys.stdout.flush()


def emit_fraction(fraction):
    """Où en est le traitement, entre 0 et 1.

    C'est l'usage prévu du canal : la barre de progression suit.
    """
    emit(f"{fraction:.4f}")


def emit_event(event, pause=PULSE_PAUSE):
    """Signale un événement à l'interface, en impulsion.

    `event` est une des constantes ci-dessus. La valeur redescend à zéro parce
    que Slicer ne réveille la fenêtre que sur un changement : sans le retour à
    zéro, deux événements de suite passeraient pour un seul.
    """
    emit(0)
    time.sleep(pause)
    emit(event // SCALE)
    time.sleep(pause)
    emit(0)
    time.sleep(pause)


def is_event(progress, event):
    """La valeur reçue par la fenêtre est-elle cet événement ?"""
    return progress == event


def as_fraction(progress):
    """La valeur reçue, ramenée entre 0 et 1.

    Une fenêtre qui reçoit à la fois des fractions et des impulsions ne peut
    pas les distinguer autrement que par l'échelle : au-delà de 1, la valeur
    vient du facteur cent. C'est ce que faisait AMASSS à la main.
    """
    return progress / SCALE if progress > 1 else progress
