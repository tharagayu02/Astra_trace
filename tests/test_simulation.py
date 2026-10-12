import unittest
from time import perf_counter

from simulation import SCENARIOS, calculate_mission


class MissionCalculationTests(unittest.TestCase):
    def test_changing_only_reserve_target_preserves_physical_forecast(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                lower_target = calculate_mission(scenario, 40, "Autonomous")
                higher_target = calculate_mission(scenario, 75, "Autonomous")
                self.assertEqual(lower_target["hours"], higher_target["hours"])
                self.assertEqual(lower_target["battery"], higher_target["battery"])
                self.assertEqual(lower_target["energy_costs"], higher_target["energy_costs"])
                self.assertEqual(lower_target["solar_recovery"], higher_target["solar_recovery"])
                self.assertEqual(lower_target["required_reserve"], [40.0] * 7)
                self.assertEqual(higher_target["required_reserve"], [75.0] * 7)
                self.assertNotEqual(lower_target["status"], higher_target["status"])
                self.assertNotEqual(
                    lower_target["drift_score"], higher_target["drift_score"]
                )

    def test_scenarios_have_distinct_schedules_and_physical_forecasts(self):
        reports = {
            scenario: calculate_mission(scenario, 45, "Autonomous")
            for scenario in SCENARIOS
        }
        schedules = {tuple(report["schedule"]) for report in reports.values()}
        energy_profiles = {
            tuple(report["energy_costs"]) for report in reports.values()
        }
        forecasts = {tuple(report["battery"]) for report in reports.values()}
        self.assertEqual(len(schedules), len(SCENARIOS))
        self.assertEqual(len(energy_profiles), len(SCENARIOS))
        self.assertEqual(len(forecasts), len(SCENARIOS))

    def test_risk_classification_matches_mission_status(self):
        expected_risk = {"SAFE": "Low", "WATCH": "Moderate", "CRITICAL": "High"}
        for scenario in SCENARIOS:
            for target in (20, 40, 75, 80):
                with self.subTest(scenario=scenario, target=target):
                    report = calculate_mission(scenario, target, "Autonomous")
                    self.assertEqual(report["risk"], expected_risk[report["status"]])
                    if report["status"] == "SAFE":
                        self.assertEqual(report["violations"], [])
                    elif report["status"] == "WATCH":
                        self.assertLessEqual(
                            max(v["shortfall"] for v in report["violations"]), 5.0
                        )
                    else:
                        self.assertGreater(
                            max(v["shortfall"] for v in report["violations"]), 5.0
                        )

    def test_forecast_falls_when_diagnostic_mode_uses_more_energy(self):
        autonomous = calculate_mission("Debris Conjunction", 45, "Autonomous")
        manual = calculate_mission("Debris Conjunction", 45, "Manual")
        safe_hold = calculate_mission("Debris Conjunction", 45, "Safe Hold")
        self.assertLess(manual["minimum_reserve"], autonomous["minimum_reserve"])
        self.assertGreater(safe_hold["minimum_reserve"], autonomous["minimum_reserve"])

    def test_invalid_inputs_are_rejected(self):
        for args in (
            ("unknown", 45, "Autonomous"),
            ("Debris Conjunction", 81, "Autonomous"),
            ("Debris Conjunction", 45.5, "Autonomous"),
            ("Debris Conjunction", 45, "Unknown"),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_mission(*args)

    def test_all_builtin_calculations_complete_under_two_seconds(self):
        start = perf_counter()
        for scenario in SCENARIOS:
            calculate_mission(scenario, 75, "Autonomous")
        self.assertLess(perf_counter() - start, 2.0)


if __name__ == "__main__":
    unittest.main()
