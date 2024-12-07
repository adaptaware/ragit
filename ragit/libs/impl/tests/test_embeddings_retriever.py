"""Tests the llm module."""

import unittest

import ragit.libs.impl.embeddings_retriever as embeddings_retriever
import ragit.libs.common as common


class TestLLMWrapper(unittest.TestCase):
    """Tests the LLMWrapper class."""

    @classmethod
    def setUpClass(cls):
        """Initializes the environment."""
        common.init_settings()

    def test_get_embeddings(self):
        """Tests the get_embeddings function."""
        txt = "hello world."
        retrieved = embeddings_retriever.get_embeddings(txt)
        expected_len = 1536
        self.assertEqual(len(retrieved), expected_len)

