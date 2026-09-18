# Ce qui arrete une recherche d'ALI CBCT : du travail, pas des secondes.
#
# La boucle s'arretait sur `time.time() - tic < max_time`, avec 15 secondes
# sur GPU et 60 sinon. Le meme scan convergeait donc ou non selon que le GPU
# etait occupe, le disque lent, ou qu'un autre module tournait : pour un
# outil clinique, un resultat qu'on ne peut pas reproduire.
#
# La borne porte desormais sur le nombre de PAS -- une passe avant du reseau
# chacun. C'est la meme quantite de travail partout, donc le meme resultat.
# Ces cas le montrent en ralentissant artificiellement un pas : le compte de
# pas ne bouge pas, alors qu'un budget en secondes en aurait rendu moins.
#
# Ni modele ni GPU ici : le cerveau et l'environnement sont des doublures,
# seule la boucle de Agent.Search est sous test.
import os
import sys
import time
import types
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
for _path in (os.path.join(_ROOT, "ADT"), os.path.join(_ROOT, "ALI_CBCT")):
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)

# Voir test_ali_cbct_bounds : dicom2nifti ne s'importe pas hors de Slicer.
sys.modules.setdefault("dicom2nifti", types.ModuleType("dicom2nifti"))

import numpy as np  # noqa: E402

from ALI_CBCT_utils.agent import (  # noqa: E402
    Agent, DEFAULT_MAX_STEPS, SearchStepBudget, SearchTimeGuard,
)
from ALI_CBCT_utils.constants import MOVEMENTS  # noqa: E402

FOV = [64, 64, 64]
SCALE = "1"
# Assez grand pour que la marche des doublures ne touche jamais un bord.
SIZE = np.array([10000, 10000, 10000])


class FakeEnvironment:
    """Un volume qui ne contient rien : seules les bornes sont lues."""

    scale_nbr = 1

    def __init__(self):
        self.predicted = {}

    def GetSpacing(self, scale):
        return np.array([1.0, 1.0, 1.0])

    def GetSize(self, scale):
        return SIZE

    def GetSamplableBounds(self, scale, crop_size):
        return np.array([-1, -1, -1]), SIZE + 1

    def GetZone(self, scale, center, crop_size):
        return None

    def AddPredictedLandmark(self, lm_id, lm_pos):
        self.predicted[lm_id] = lm_pos


class FakeBrain:
    """Un cerveau qui compte ses passes et peut en rendre une lente.

    Les deplacements alternent sur deux axes : l'agent ne repasse jamais sur
    une position, donc `Visited()` n'est jamais vrai et la recherche va au
    bout de son budget. C'est le cas qu'il faut mesurer.
    """

    def __init__(self, delay=0.0):
        self.calls = 0
        self.delay = delay

    def Predict(self, dim, state):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        return 0 if self.calls % 2 else 2


def an_agent(brain):
    agent = Agent(targeted_landmark="Me", movements=MOVEMENTS,
                  scale_keys=[SCALE], FOV=FOV, speed_per_scale=[1, 1])
    agent.SetBrain(brain)
    agent.SetEnvironment(FakeEnvironment())
    return agent


def steps_for(budget, delay=0.0):
    """Les passes avant reellement faites, sous ce budget."""
    os.environ["ALI_SEARCH_MAX_STEPS"] = str(budget)
    try:
        brain = FakeBrain(delay=delay)
        result = an_agent(brain).Search()
    finally:
        del os.environ["ALI_SEARCH_MAX_STEPS"]
    return brain.calls, result


class StepBudgetTest(unittest.TestCase):

    def test_a_search_that_never_settles_spends_exactly_its_budget(self):
        calls, result = steps_for(40)
        self.assertEqual(calls, 40)
        self.assertEqual(result, -1)

    def test_the_same_budget_gives_the_same_work_twice(self):
        self.assertEqual(steps_for(40), steps_for(40))

    def test_a_slow_machine_does_not_shorten_the_search(self):
        """Le coeur de l'affaire.

        Avec 2 ms par pas, quarante pas prennent plus de quarante fois ce que
        prend un pas instantane. Sous un budget en secondes, la course lente
        se serait arretee bien avant la rapide ; sous un budget en pas, les
        deux font exactement le meme travail.
        """
        fast_calls, fast_result = steps_for(40)
        tic = time.time()
        slow_calls, slow_result = steps_for(40, delay=0.002)
        slow_seconds = time.time() - tic

        self.assertEqual(slow_calls, fast_calls)
        self.assertEqual(slow_result, fast_result)
        self.assertGreater(slow_seconds, 0.04,
                           "la course lente doit vraiment etre plus lente")

    def test_the_budget_is_what_changes_the_work(self):
        self.assertEqual(steps_for(7)[0], 7)
        self.assertEqual(steps_for(23)[0], 23)


class BudgetSettingTest(unittest.TestCase):

    def setUp(self):
        self.saved = {name: os.environ.pop(name, None)
                      for name in ("ALI_SEARCH_MAX_STEPS",
                                   "ALI_SEARCH_TIME_GUARD")}

    def tearDown(self):
        for name, value in self.saved.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value

    def test_the_default_is_used_when_nothing_is_set(self):
        self.assertEqual(SearchStepBudget(), DEFAULT_MAX_STEPS)

    def test_the_environment_variable_wins(self):
        os.environ["ALI_SEARCH_MAX_STEPS"] = "250"
        self.assertEqual(SearchStepBudget(), 250)
        os.environ["ALI_SEARCH_TIME_GUARD"] = "12.5"
        self.assertEqual(SearchTimeGuard(), 12.5)

    def test_a_value_that_is_not_a_number_falls_back_to_the_default(self):
        os.environ["ALI_SEARCH_MAX_STEPS"] = "beaucoup"
        self.assertEqual(SearchStepBudget(), DEFAULT_MAX_STEPS)

    def test_the_time_guard_stays_far_above_the_step_budget(self):
        """Ce n'est plus lui qui decide dans le cas normal."""
        self.assertGreater(SearchTimeGuard(), 60.0)


if __name__ == "__main__":
    unittest.main()
