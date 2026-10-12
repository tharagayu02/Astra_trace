import json
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from simulation import SCENARIOS, calculate_mission


class DashboardDiagnosticTests(unittest.TestCase):
    def test_diagnostic_runs_only_on_click_for_every_scenario(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                app = AppTest.from_file(str(app_path)).run(timeout=20)
                self.assertEqual(len(app.exception), 0)
                self.assertIsNone(app.session_state.get("diagnostic_report"))

                app.selectbox[0].select(scenario)
                app.slider[0].set_value(75)
                app.run()
                self.assertIsNone(app.session_state.get("diagnostic_report"))
                report = calculate_mission(scenario, 75, "Autonomous")
                chart_spec = json.loads(app.get("plotly_chart")[0].proto.spec)
                self.assertEqual(chart_spec["data"][0]["y"], report["battery"])
                self.assertEqual(chart_spec["data"][1]["y"], [75.0] * 7)

                app.button[1].click().run(timeout=20)
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(
                    app.session_state["diagnostic_inputs"],
                    (scenario, 75, "Autonomous"),
                )
                self.assertEqual(
                    app.session_state["diagnostic_report"],
                    calculate_mission(scenario, 75, "Autonomous"),
                )


if __name__ == "__main__":
    unittest.main()
