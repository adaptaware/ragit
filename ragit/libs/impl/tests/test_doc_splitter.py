"""Tests the doc_splitter module."""

import os
import unittest

import ragit.libs.common as common
import ragit.libs.impl.splitter as splitter


class TestSplittingToChunks(unittest.TestCase):
    """Tests the _split_to_chunks function."""

    def test_docx(self):
        """Tests the get_chunks method for docx."""
        full_path = os.path.join(
            common.get_testing_data_directory(),
            "hello-world.docx"
        )
        for txt, meta in splitter.split(full_path):
            self.assertIsInstance(txt, str)
            self.assertIsInstance(meta, dict)

    def test_markdown(self):
        """Tests the get_chunks method for markdown."""
        full_path = os.path.join(
            common.get_testing_data_directory(),
            "sql-alchemy-sucks.md"
        )
        for txt, meta in splitter.split(full_path):
            self.assertIsInstance(txt, str)
            self.assertIsInstance(meta, dict)

    def test_python_file(self):
        """Tests the get_chunks method for python code."""
        full_path = os.path.join(
            common.get_testing_data_directory(),
            "hello_world.py"
        )
        for txt, meta in splitter.split(full_path):
            self.assertIsInstance(txt, str)
            self.assertIsInstance(meta, dict)
