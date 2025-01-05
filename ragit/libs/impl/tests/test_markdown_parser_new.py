"""Tests the markdown_parser module."""

import os

import pytest

import ragit.libs.impl.markdown_parser_new as mp

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_document_invalid_caption():
    with pytest.raises(AssertionError):
        doc = mp.Node("")


def test_node_1():
    caption = "root"
    doc = mp.Node(caption)
    retrieved = doc.to_str()
    assert retrieved == caption


def test_node_2():
    captions = [
        "# Header 1",
        "# Header 2",
    ]
    root = mp.Node("root")

    for c in captions:
        root.add(c)

    retrieved = root.to_str()
    expected = """root
---- Header 1
---- Header 2 
    """
    assert retrieved.strip() == expected.strip()


def test_node_3():
    captions = [
        "# # Header 1",
        "## ## Header 2",
        "### ### Header 3",
        "## ## Header 4",
        "### ### Header 5",
        "### ### Header 5.1",
        "### ### Header 5.2",
        "## ## Header 6",
        "### ### Header 6",
        "### ### Header 6.1",
        "### ### Header 6.2",
        "# # Header 7",
    ]
    root = mp.Node("root")

    for c in captions:
        root.add(c)

    retrieved = root.to_str()
    expected = """root
---- # Header 1
---- ---- ## Header 2
---- ---- ---- ### Header 3
---- ---- ## Header 4
---- ---- ---- ### Header 5
---- ---- ---- ### Header 5.1
---- ---- ---- ### Header 5.2
---- ---- ## Header 6
---- ---- ---- ### Header 6
---- ---- ---- ### Header 6.1
---- ---- ---- ### Header 6.2
---- # Header 7
    """
    assert retrieved.strip() == expected.strip()


def test_node_4():
    lines = [
        "# Header 1",
        "|name|age|",
        "|x|1|",
        "|y|2|",
        "## Header 1.1",
        "|a|1|",
        "|b|2|",
        "## Header 2",
        "# Header 3",
    ]
    root = mp.Node("root")

    for c in lines:
        root.add(c)

    retrieved = root.to_str()
    expected = """root
---- Header 1
---- ---- Table
---- ---- |name|age|
---- ---- |x|1|
---- ---- |y|2|
---- ---- Header 1.1
---- ---- ---- Table
---- ---- ---- |a|1|
---- ---- ---- |b|2|
---- ---- Header 2
---- Header 3
    """
    assert retrieved.strip() == expected.strip()

def test_node_5():
    lines = [
        "# Header 1",
        "|name|age|",
        "|x|1|",
        "|y|2|",
        "## Header 1.1",
        "this is text",
        "fields and lines",
        "|name|age|",
        "|x|1|",
        "|y|2|",
        "# Header 2",
        "this is text about",
        "some topic ",
    ]
    root = mp.Node("root")

    for c in lines:
        root.add(c)

    retrieved = root.to_str()
    expected = """root
---- Header 1
---- ---- Table
---- ---- |name|age|
---- ---- |x|1|
---- ---- |y|2|
---- ---- Header 1.1
---- ---- ---- Text
---- ---- ---- this is text
---- ---- ---- fields and lines
---- ---- ---- Table
---- ---- ---- |name|age|
---- ---- ---- |x|1|
---- ---- ---- |y|2|
---- Header 2
---- ---- Text
---- ---- this is text about
---- ---- some topic
    """
    assert retrieved.strip() == expected.strip()
