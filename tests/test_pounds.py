import importlib.util
import sys
import types
import unittest
from pathlib import Path

sys.modules.setdefault("torch", types.ModuleType("torch"))
if "tokenizers" not in sys.modules:
    tokenizers = types.ModuleType("tokenizers")
    tokenizers.Tokenizer = type("Tokenizer", (), {})
    sys.modules["tokenizers"] = tokenizers


def _english_cleaners():
    path = Path(__file__).resolve().parents[1] / "tortoise" / "utils" / "tokenizer.py"
    spec = importlib.util.spec_from_file_location("tortoise_tokenizer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.english_cleaners


english_cleaners = _english_cleaners()


class PoundsCleanerTest(unittest.TestCase):
    def test_pounds_are_spoken_as_pounds(self):
        self.assertEqual(english_cleaners("£1.50"), "one pound, fifty pence")
        self.assertEqual(english_cleaners("£1"), "one pound")
        self.assertEqual(english_cleaners("£2"), "two pounds")
        self.assertEqual(english_cleaners("£10.05"), "ten pounds, five pence")
        self.assertEqual(english_cleaners("£1.5"), "one pound, fifty pence")
        self.assertEqual(english_cleaners("£1,000"), "one thousand pounds")

    def test_dollars_stay_the_same(self):
        self.assertEqual(english_cleaners("$1.50"), "one dollar, fifty cents")
        self.assertEqual(english_cleaners("Hello."), "hello.")


if __name__ == "__main__":
    unittest.main()
