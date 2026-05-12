import unittest
import sim
import os

class TestBioSimSimulation(unittest.TestCase):
    def test_simulation(self):
        s = sim.BioSimSimulation()
        hours_survived = s.catastrophic_power_failure()
        self.assertEqual(hours_survived, 13755)

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
        with self.assertRaises(ZeroDivisionError):
            # Zero water mass should raise ZeroDivisionError
            s.thermal_loop_failure(water_mass_kg=0)

    def test_metabolic_logistic_growth(self):
        # Assert First pattern: biomass accumulation is non-linear (growth rate accelerates then decelerates)
        def assert_logistic_growth(buffer_array):
            rates_of_change = [buffer_array[i] - buffer_array[i-1] for i in range(1, len(buffer_array))]
            
            # Find the index where the growth rate is maximum (inflection point)
            max_rate = max(rates_of_change)
            max_index = rates_of_change.index(max_rate)
            
            # Assert it accelerates initially (up to max_index)
            for i in range(1, max_index):
                self.assertGreater(rates_of_change[i], rates_of_change[i-1])
                
            # Assert it decelerates after reaching the maximum rate
            for i in range(max_index + 1, len(rates_of_change)):
                self.assertLess(rates_of_change[i], rates_of_change[i-1])

        s = sim.BioSimSimulation()
        final_buffer, buffer_over_time = s.metabolic_banking()
        assert_logistic_growth(buffer_over_time)

    def test_metabolic_extreme_capacity(self):
        s = sim.BioSimSimulation()
        with self.assertRaises(ValueError):
            # Negative buffer
            s.metabolic_banking(current_buffer=-10)
        
        with self.assertRaises(ValueError):
            # Zero carrying capacity
            s.metabolic_banking(carrying_capacity=0)

    def test_circadian_metabolism_drain(self):
        # Assert First: assert hours_survived is non-zero positive integer and food_buffer is <= 0
        s = sim.BioSimSimulation()
        hours_survived, final_food_buffer = s.catastrophic_power_failure(return_details=True)

        self.assertIsInstance(hours_survived, int)
        self.assertGreater(hours_survived, 0)
        self.assertLessEqual(final_food_buffer, 0)

if __name__ == '__main__':
    unittest.main()
