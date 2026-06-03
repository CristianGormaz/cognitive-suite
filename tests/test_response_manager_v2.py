import unittest
from core.response_manager import ResponseManager

class TestResponseManagerV2(unittest.TestCase):
    def setUp(self):
        self.manager = ResponseManager()

    def test_exact_matches(self):
        self.assertEqual(self.manager.generate_response("chat", "hola"), "Hola, soy Greys-v3. Estoy operativo en modo texto.")
        self.assertIn("desarrollo", self.manager.generate_response("chat", "¿quién eres?"))

    def test_keyword_matches(self):
        # Escuchas
        self.assertIn("te leo", self.manager.generate_response("chat", "hola, ¿me escuchas?"))
        self.assertIn("te leo", self.manager.generate_response("chat", "me lees?"))
        
        # Capacidades
        self.assertIn("clasificar", self.manager.generate_response("chat", "¿qué puedes hacer?"))
        self.assertIn("fase de prueba", self.manager.generate_response("chat", "cuáles son tus capacidades?"))
        
        # Ayuda
        self.assertIn("conversar", self.manager.generate_response("chat", "necesito ayuda"))
        
        # Estado
        self.assertIn("metabólico", self.manager.generate_response("chat", "cuál es tu estado?"))
        self.assertIn("metabólico", self.manager.generate_response("chat", "vitals"))

    def test_fallback(self):
        self.assertEqual(self.manager.generate_response("chat", "patatas"), "Entendí tu mensaje, pero aún estoy en modo respuesta básica.")

if __name__ == "__main__":
    unittest.main()
