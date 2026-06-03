import importlib.util
import os
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_PYSIDE6 = importlib.util.find_spec("PySide6") is not None


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is not installed")
class EvolutionDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def make_options(self):
        from cognition.fallback_engine import FallbackHypothesis, FallbackOptions

        return FallbackOptions(
            task_id="task_ui",
            source_status="blocked_fallback",
            ui_state="evolutionary_doubt",
            hypotheses=(
                FallbackHypothesis(
                    id="opt_1",
                    action_type="ask_human",
                    label="Pedir aclaracion",
                    description="Solicitar mas contexto al usuario.",
                ),
                FallbackHypothesis(
                    id="opt_2",
                    action_type="sandbox_code",
                    label="Generar script seguro",
                    description="Preparar codigo en sandbox antes de ejecutar.",
                ),
                FallbackHypothesis(
                    id="opt_3",
                    action_type="abort",
                    label="Descartar tarea",
                    description="Cerrar el flujo sin cambios persistentes.",
                ),
            ),
        )

    def test_renders_one_button_per_hypothesis(self):
        from PySide6.QtWidgets import QPushButton
        from ui.evolution_dialog import EvolutionDialog

        dialog = EvolutionDialog(self.make_options())
        buttons = dialog.findChildren(QPushButton)

        self.assertEqual(len(buttons), 3)
        self.assertIn("Pedir aclaracion", buttons[0].text())
        self.assertIn("Generar script seguro", buttons[1].text())
        self.assertIn("Descartar tarea", buttons[2].text())
        dialog.deleteLater()

    def test_emits_action_type_and_hides_on_click(self):
        from PySide6.QtWidgets import QPushButton
        from ui.evolution_dialog import EvolutionDialog

        dialog = EvolutionDialog(self.make_options())
        selected = []
        dialog.actionSelected.connect(selected.append)

        buttons = dialog.findChildren(QPushButton)
        buttons[1].click()
        self.app.processEvents()

        self.assertEqual(selected, ["sandbox_code"])
        self.assertFalse(dialog.isVisible())


if __name__ == "__main__":
    unittest.main()
