import unittest
from unittest.mock import patch, Mock
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

    @patch('sim.requests.post')
    def test_start_simulation_posts_xml(self, mock_post):
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'simId': 12345}
        mock_post.return_value = mock_response

        # Call the function
        sim_id = sim.start_simulation(sim.biosim_config_xml)

        # Assert post was called with correct arguments
        mock_post.assert_called_once_with(
            "http://localhost:8009/api/simulation/start",
            data=sim.biosim_config_xml,
            headers={'Content-Type': 'text/plain'}
        )

        # Assert returned simID is correct
        self.assertEqual(sim_id, 12345)

    def test_biosim_xml_config(self):
        import xml.etree.ElementTree as ET

        # Parse the XML config
        try:
            root = ET.fromstring(sim.biosim_config_xml)
        except AttributeError:
            self.fail("sim.biosim_config_xml is not defined.")
        except ET.ParseError:
            self.fail("sim.biosim_config_xml is not valid XML.")

        # Assert root is biosim
        self.assertEqual(root.tag, 'biosim')

        # Assert 15 crew members, each with an activity schedule
        crew_members = root.findall('.//crew_member')
        self.assertEqual(len(crew_members), 15, "There should be exactly 15 crew members")
        for crew in crew_members:
            schedules = crew.findall('.//activity_schedule')
            self.assertGreaterEqual(len(schedules), 1, "Each crew member must have an activity_schedule to avoid NPE")

        # Assert 28 plant growth shelves
        shelves = root.findall('.//shelf')
        self.assertEqual(len(shelves), 28, "There should be exactly 28 plant growth shelves")

        # Assert Potable_Water_Store with capacity 20000
        water_store = root.find('.//Potable_Water_Store')
        self.assertIsNotNone(water_store, "Potable_Water_Store is missing")
        self.assertEqual(water_store.get('capacity'), '20000', "Potable_Water_Store must have capacity 20000")

        # Assert O2_Store is present
        o2_store = root.find('.//O2_Store')
        self.assertIsNotNone(o2_store, "O2_Store is missing")
        self.assertIsNotNone(o2_store.get('capacity'), "O2_Store must have a capacity defined")

    @patch('sim.requests.get')
    def test_open_mct_connectivity(self, mock_get):
        # Assert First pattern: We test for a 200 HTTP response.
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Check Open MCT connectivity
        is_connected = sim.verify_open_mct_connectivity()

        # Assert the correct URL was hit and the connection is True
        mock_get.assert_called_once_with('http://localhost:9091')
        self.assertTrue(is_connected, "Should return True on HTTP 200 from Open MCT")

    @patch('sim.websocket.create_connection')
    def test_websocket_telemetry(self, mock_ws_connect):
        # Assert First pattern: test JSON parsing from ws
        mock_ws = Mock()
        mock_ws.recv.return_value = '{"o2Moles": 500.5, "co2Moles": 150.2, "relativeHumidity": 45.0, "otherData": "ignore"}'
        mock_ws_connect.return_value = mock_ws

        # Execute
        data = sim.websocket_listener(sim_id=1)

        # Assertions
        mock_ws_connect.assert_called_once_with('ws://localhost:8009/ws/simulation/1')
        self.assertEqual(data.get('o2Moles'), 500.5)
        self.assertEqual(data.get('co2Moles'), 150.2)
        self.assertEqual(data.get('relativeHumidity'), 45.0)

if __name__ == '__main__':
    unittest.main()
