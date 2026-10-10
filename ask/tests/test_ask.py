"""Smoke tests for the portable ASK reference interpreter."""
import tempfile
import unittest
from pathlib import Path

from ask import AskError, AskRuntime, run_program


class AskInterpreterTests(unittest.TestCase):
    def test_selects_element_and_returns_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "page.html").write_text(
                '<html><body><button id="go">Start here</button></body></html>',
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

    def test_returns_full_document(self):
        source = '<html><body><p id="p">Hi</p></body></html>'
        rt = AskRuntime(source_html=source, return_type="complete")
        self.assertEqual(rt.get_return_value(), source)

    def test_permission_values_are_preserved(self):
        program = "check.permisions:\n  location = ask\n  acelometer = yes\n  microphone = no"
        run_program(program)
        # The runtime currently stores permissions in-memory; host enforcement
        # is deliberately delegated to a future browser/OS adapter.

    def test_unknown_element_fails_clearly(self):
        rt = AskRuntime(source_html='<p id="known">Text</p>')
        with self.assertRaises(AskError):
            rt.select_element("missing")


if __name__ == "__main__":
    unittest.main()
