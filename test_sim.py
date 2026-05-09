import unittest
import sim
import os

class TestBioSimSimulation(unittest.TestCase):
    def test_simulation(self):
        s = sim.BioSimSimulation()
        days_survived = s.catastrophic_power_failure()
        self.assertAlmostEqual(days_survived, 154.50, places=1)

        hours_to_critical = s.thermal_loop_failure()
        self.assertEqual(hours_to_critical, 17)

if __name__ == '__main__':
    unittest.main()
