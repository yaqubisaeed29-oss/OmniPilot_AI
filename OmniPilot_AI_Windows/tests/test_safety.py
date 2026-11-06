import tempfile
import unittest
from pathlib import Path
from omnipilot.computer import Computer, ActionError
from omnipilot.ollama_client import OllamaClient, OllamaError

class SafetyTests(unittest.TestCase):
    def test_workspace_accepts_relative_and_dot(self):
        with tempfile.TemporaryDirectory() as root:
            c=Computer(root)
            self.assertEqual(c._path("notes/a.txt"),Path(root).resolve()/"notes/a.txt")
            self.assertEqual(c._path("."),Path(root).resolve())
    def test_workspace_rejects_absolute_and_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            c=Computer(root)
            for value in ("../outside.txt", str(Path(root).parent/"outside.txt"), "a/../../outside"):
                with self.subTest(value=value), self.assertRaises(ActionError): c._path(value)
    def test_json_parser_accepts_fenced_json_and_object(self):
        self.assertEqual(OllamaClient.parse_json('```json\n{"type":"done"}\n```'),{"type":"done"})
        self.assertEqual(OllamaClient.parse_json('Result: {"steps":["open app"]}'),{"steps":["open app"]})
    def test_json_parser_rejects_malformed(self):
        with self.assertRaises(OllamaError): OllamaClient.parse_json("not json")
    def test_create_and_read_workspace_file(self):
        with tempfile.TemporaryDirectory() as root:
            c=Computer(root)
            result=c.perform({"type":"create_file","path":"folder/test.txt","content":"hello"})
            self.assertIn("Created",result)
            self.assertIn("hello",c.perform({"type":"read_file","path":"folder/test.txt"}))
            with self.assertRaises(ActionError): c.perform({"type":"create_file","path":"folder/test.txt","content":"overwrite"})

if __name__=="__main__": unittest.main()
