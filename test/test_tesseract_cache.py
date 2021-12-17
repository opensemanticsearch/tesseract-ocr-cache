from unittest import TestCase
from unittest.mock import patch
import os
from dataclasses import dataclass

from tesseract_cache import tesseract_cache


def mock_get_cache_filename(filename,
                            lang,
                            options,  # pylint: disable=unused-argument
                            tesseract_configfilename='txt'):
    """Uses the filename itself instead of
    the contents to prevent os operations"""
    return f"{lang}-{filename}-OPTS.{tesseract_configfilename}"


def make_iglob_mock(langs):
    """Replacement for glob.iglob which "finds" predefined results
    according to `langs`"""
    def mock_iglob(expr: str):
        path, suffix = expr.split("*")
        return [os.path.join(path, lang+suffix) for lang in langs]
    return mock_iglob


class TestTesseractCache(TestCase):
    @patch("tesseract_cache.tesseract_cache.get_cache_filename",
           mock_get_cache_filename)
    def test_get_cache_filename_multilang(self):
        @dataclass
        class SubTest:
            """Encapsulates expected output for given input to
            get_cache_filename_multilang"""
            requested_lang: str
            cached_langs: list
            expected: str
        default_args = dict(
            filename="book.pdf",
            options="-l eng",
            cache_dir="/ocr_cache/"
        )

        # Test get_cache_filename_multilang for a sequence of
        # input/output test cases:
        for test_case in (
                SubTest(requested_lang="eng",
                        cached_langs=["eng", "eng+deu"],
                        expected="/ocr_cache/eng-book.pdf-OPTS.txt"
                        ),
                SubTest(requested_lang="deu",
                        cached_langs=["eng", "eng+deu+fra", "eng+deu"],
                        expected="/ocr_cache/eng+deu-book.pdf-OPTS.txt"
                        ),
                SubTest(requested_lang="deu",
                        cached_langs=[],
                        expected="/ocr_cache/deu-book.pdf-OPTS.txt"
                        ),
                SubTest(requested_lang="deu+eng",
                        cached_langs=["eng", "deu", "eng+deu", "deu+eng+fra"],
                        expected="/ocr_cache/eng+deu-book.pdf-OPTS.txt"
                        )

        ):
            with self.subTest(test_case=test_case), \
                    patch("tesseract_cache.tesseract_cache.glob.iglob",
                          make_iglob_mock(test_case.cached_langs)):
                self.assertEqual(tesseract_cache.get_cache_filename_multilang(
                    lang=test_case.requested_lang,
                    **default_args),
                    test_case.expected)
