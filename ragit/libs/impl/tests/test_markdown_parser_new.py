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
    print("******")
    print(retrieved)

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
        "# # Header 7",
    ]
    root = mp.Node("root")

    for c in captions:
        root.add(c)

    retrieved = root.to_str()
    print("******")
    print(retrieved)

def test_document2():
    txt = """
    # Header1
    this is a test
    multi-line
    ## Header 1.2
    Belongs to header 1.2..
    ### Header 1.3
    Belongs to header 1.3..
    |name|age|
    |x|1|
    # Header2
    Belongs to header 2
    # Header3
    # Header4
    |name|age|
    |x|1|
    """
    root = markdown_parser.Root()
    for line in txt.split("\n"):
        root.add_line(line)

    for n in root.get_nodes():
        print(n)
