import unittest
import sim
import os

class TestBioSimSimulation(unittest.TestCase):
    def test_simulation(self):
        s = sim.BioSimSimulation()
        days_survived = s.catastrophic_power_failure()
        self.assertAlmostEqual(days_survived, 154.50, places=1)

        hours_to_critical = s.thermal_loop_failure()
        self.assertEqual(hours_to_critical, 19)

    def test_thermal_non_linearity(self):
        s = sim.BioSimSimulation()
        hours_to_critical, temps = s.thermal_loop_failure(return_temps=True)

        # Calculate rates of change (slopes)
        slopes = [temps[i] - temps[i-1] for i in range(1, len(temps))]

        # Assert that the slope strictly decreases over time (cooling is proportional to temp diff)
        for i in range(1, len(slopes)):
            self.assertLess(slopes[i], slopes[i-1], "Cooling rate (slope) should strictly decrease over time")

    def test_thermal_extreme_conditions(self):
        s = sim.BioSimSimulation()
        # Test a sudden 100C ambient spike to ensure it does not crash
        hours, temps = s.thermal_loop_failure(ambient_temp=100.0, return_temps=True)
        self.assertGreater(len(temps), 0)

if __name__ == '__main__':
    unittest.main()
