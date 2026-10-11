"""Smoke tests for the portable ASK reference interpreter."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
from ask import AskError, AskRuntime, run_program


class AskInterpreterTests(unittest.TestCase):
    def test_selects_element_and_returns_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "page.html").write_text(
                '<html><body><button id="go">Start <span>here</span></button></body></html>',
                encoding="utf-8",
            )
            output = run_program(
                'html=[page].html\nel={go}\nreturn.type=text\nreturn',
                Path(tmp),
            )
            self.assertEqual(output, "Start here")

    def test_missing_text_returns_none(self):
        rt = AskRuntime(source_html='<input id="field">')
        rt.select_element("field")
        rt.return_type = "text"
        self.assertEqual(rt.get_return_value(), "NONE")

    def test_void_element_markup_is_returned(self):
        rt = AskRuntime(source_html='<input id="field">')
        rt.select_element("field")
        rt.return_type = "all"
        self.assertEqual(rt.get_return_value(), '<input id="field">')

    def test_returns_full_document(self):
        source = '<html><body><p id="p">Hi</p></body></html>'
        rt = AskRuntime(source_html=source, return_type="complete")
        self.assertEqual(rt.get_return_value(), source)

    def test_permission_syntax_is_accepted(self):
        program = """check.permisions:
  location = ask
  acelometer = yes
  microphone = no"""
        run_program(program)

    def test_unknown_element_fails_clearly(self):
        rt = AskRuntime(source_html='<p id="known">Text</p>')
        with self.assertRaises(AskError):
            rt.select_element("missing")


if __name__ == "__main__":
    unittest.main()
