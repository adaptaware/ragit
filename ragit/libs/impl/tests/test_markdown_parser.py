"""Tests the markdown_parser module."""

import os

import pytest

import ragit.libs.impl.markdown_parser as mp

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_document_invalid_caption():
    with pytest.raises(AssertionError):
        doc = mp.Node("")

def test_iter_markdown():
    """Tests the get_paragraphs function."""
    md_path = os.path.join(_CURRENT_DIR, "static", "sample4.md")
    for node in mp.iter_markdown(md_path):
        print(node)
        print(node.get_headers())
        print(node.get_inner_text())
        print("================================")