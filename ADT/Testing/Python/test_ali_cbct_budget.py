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

from ALI_CBCT_utils import agent as agent_module  # noqa: E402
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


class BrokenBrain:
    """Un cerveau qui echoue, comme le ferait un tenseur mal forme."""

    def __init__(self):
        self.calls = 0

    def Predict(self, dim, state):
        self.calls += 1
        raise IndexError("index 64 is out of bounds for axis 0 with size 64")


class FailedStepTest(unittest.TestCase):
    """Une erreur de pas etait avalee et devenait un « timeout ».

    Le `except ... continue` rejouait le meme pas sur le meme etat jusqu'a
    epuisement du budget : l'operateur lisait « pas trouve », jamais la
    cause. Rien ne change entre deux tentatives, donc il n'y a rien a
    reessayer.
    """

    def setUp(self):
        os.environ["ALI_SEARCH_MAX_STEPS"] = "500"

    def tearDown(self):
        os.environ.pop("ALI_SEARCH_MAX_STEPS", None)

    def test_a_failing_step_is_not_replayed_until_the_budget_runs_out(self):
        brain = BrokenBrain()
        result = an_agent(brain).Search()
        self.assertEqual(brain.calls, 1, "un seul essai, pas cinq cents")
        self.assertEqual(result, -1)

    def test_the_cause_reaches_the_log(self):
        brain = BrokenBrain()
        with self.assertLogs("ADT.ALI_CBCT_Agent", level="ERROR") as logged:
            an_agent(brain).Search()
        self.assertTrue(
            any("out of bounds" in line for line in logged.output),
            f"le message d'origine doit remonter : {logged.output}")


class RingWalkingBrain:
    """Un cerveau qui fait tourner l'agent sur un anneau de quarante pas.

    `Visited()` ne compare qu'aux DIX dernieres positions : sur un anneau
    plus long, aucune position ne revient assez vite, la recherche ne se
    pose jamais et depensait tout son budget a tourner.
    """

    RING = 40

    def __init__(self):
        self.calls = 0

    def Predict(self, dim, state):
        phase = self.calls % self.RING
        self.calls += 1
        if phase < 10:
            return 0   # +x
        if phase < 20:
            return 2   # +y
        if phase < 30:
            return 1   # -x
        return 3       # -y


class CyclingTest(unittest.TestCase):
    """Un agent qui tourne en rond est arrete bien avant la fin du budget."""

    BUDGET = 2000

    def setUp(self):
        os.environ["ALI_SEARCH_MAX_STEPS"] = str(self.BUDGET)

    def tearDown(self):
        os.environ.pop("ALI_SEARCH_MAX_STEPS", None)

    def test_the_ring_is_longer_than_the_short_memory(self):
        """Sinon le cas ne prouverait rien : `Visited()` s'en chargerait."""
        self.assertGreater(RingWalkingBrain.RING, Agent(
            targeted_landmark="Me", movements=MOVEMENTS, scale_keys=[SCALE],
            FOV=FOV).shortmem_size)

    def test_without_the_detection_the_whole_budget_goes_to_the_ring(self):
        """L'etat d'avant, mesure : le budget entier part en rond."""
        saved = agent_module.STALL_STEPS
        agent_module.STALL_STEPS = 10 ** 9
        try:
            brain = RingWalkingBrain()
            result = an_agent(brain).Search()
        finally:
            agent_module.STALL_STEPS = saved
        self.assertEqual(brain.calls, self.BUDGET)
        self.assertEqual(result, -1)

    def test_with_it_the_search_stops_far_earlier(self):
        brain = RingWalkingBrain()
        result = an_agent(brain).Search()
        self.assertEqual(result, -1)
        self.assertLess(brain.calls, self.BUDGET // 2,
                        "arrete bien avant la fin du budget")

    def test_the_diagnosis_says_what_happened(self):
        with self.assertLogs("ADT.ALI_CBCT_Agent", level="WARNING") as logged:
            an_agent(RingWalkingBrain()).Search()
        self.assertTrue(
            any("going in circles" in line for line in logged.output),
            f"le diagnostic doit etre lisible : {logged.output}")

    def test_a_converging_search_is_never_called_cycling(self):
        """FakeBrain ne repasse jamais sur une position : jamais d'alerte."""
        os.environ["ALI_SEARCH_MAX_STEPS"] = "300"
        agent = an_agent(FakeBrain())
        agent.Search()
        self.assertEqual(agent.steps_on_known_ground, 0)


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
