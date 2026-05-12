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
        # Assert First pattern: assert the slope strictly decreases over time
        def assert_slope_strictly_decreases(temps_array):
            slopes = [temps_array[i] - temps_array[i-1] for i in range(1, len(temps_array))]
            for i in range(1, len(slopes)):
                self.assertLess(slopes[i], slopes[i-1], "Cooling rate (slope) should strictly decrease over time")

        s = sim.BioSimSimulation()
        hours_to_critical, temps = s.thermal_loop_failure(return_temps=True)
        assert_slope_strictly_decreases(temps)

    def test_thermal_extreme_conditions(self):
        s = sim.BioSimSimulation()
        with self.assertRaises(ZeroDivisionError):
            # Zero water mass should raise ZeroDivisionError
            s.thermal_loop_failure(water_mass_kg=0)

        # Handle a sudden 100C ambient spike
        hours, temps = s.thermal_loop_failure(ambient_temp=100.0, return_temps=True)
        # It should heat up very quickly, assert some behavior here if needed, or just that it doesn't crash
        self.assertTrue(len(temps) > 0)

if __name__ == '__main__':
    unittest.main()
