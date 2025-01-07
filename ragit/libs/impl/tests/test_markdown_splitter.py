"""Tests the markdown_splitter module."""

import os

import pytest

import ragit.libs.common as common
import ragit.libs.impl.markdown_splitter as ms

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_split_single_chunk():
    """Tests a single chunk."""
    common.init_settings()
    filepath = os.path.join(_CURRENT_DIR, "static", "single_chunk.txt")
    with open(filepath) as fin:
        text = fin.read()
    retrieved = ms.get_chunks(text, chunk_size=500)
    for chunk in retrieved:
        print(chunk)
        print("_____________________________________________")


def test_split_single_chunk_no_periods():
    """Tests a single chunk with no periods"""
    common.init_settings()
    filepath = os.path.join(_CURRENT_DIR, "static",
                            "single_chunk_no_periods.txt")
    with open(filepath) as fin:
        text = fin.read()
    retrieved = ms.get_chunks(text, chunk_size=500)
    for chunk in retrieved:
        print(chunk)
        print("_____________________________________________")
