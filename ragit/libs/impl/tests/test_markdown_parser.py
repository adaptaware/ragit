"""Tests the markdown_parser module."""

import os

import pytest

import ragit.libs.impl.markdown_parser as markdown_parser

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_parsing_markdown():
    """Tests the parse function."""
    md_path = os.path.join(_CURRENT_DIR, "static", "sample.md")
    retrieved = markdown_parser.parse(md_path)
    print(retrieved.get_as_string())


def test_get_paragraphs():
    """Tests the get_paragraphs function."""
    md_path = os.path.join(_CURRENT_DIR, "static", "sample3.md")
    retrieved = markdown_parser.parse(md_path)
    for paragraph in retrieved.get_paragraphs():
        print(paragraph)
        print("*" * 100)


def test_text_line():
    txt = "this is a test"
    tl = markdown_parser.TextLine(txt)
    assert tl.get_value() == txt


def test_text_line_invalid_value():
    txt = "# this is a test"
    with pytest.raises(AssertionError):
        markdown_parser.TextLine(txt)


def test_table_line():
    txt = "|this is a test|"
    tl = markdown_parser.TableLine(txt)
    assert tl.get_value() == txt


def test_table_line_invalid_value():
    txt = "# this is a test"
    with pytest.raises(AssertionError):
        markdown_parser.TableLine(txt)


def test_setting_parent_to_root():
    root = markdown_parser.Root()
    h1 = markdown_parser.H1("# this is a test")
    with pytest.raises(NotImplementedError):
        root.set_parent(h1)


def test_is_acceptable_for_root():
    root = markdown_parser.Root()

    root1 = markdown_parser.Root()
    assert not root.is_acceptable(root1)
    assert not root.is_acceptable(root)

    h1 = markdown_parser.H1("# this is a test")
    assert root.is_acceptable(h1)

    h2 = markdown_parser.H2("## this is a test")
    assert root.is_acceptable(h2)

    h3 = markdown_parser.H3("### this is a test")
    assert root.is_acceptable(h3)

    text = markdown_parser.Text()
    assert root.is_acceptable(text)

    table = markdown_parser.Table()
    assert root.is_acceptable(table)

    line = markdown_parser.TextLine("junk")
    assert not root.is_acceptable(line)

    line = markdown_parser.TableLine("|junk|")
    assert not root.is_acceptable(line)

    assert not root.is_acceptable("xyz")
    assert not root.is_acceptable(123)
    assert not root.is_acceptable(None)


def test_get_parent_for_root():
    root = markdown_parser.Root()
    assert root.get_parent() is None


def test_is_acceptable_for_h1():
    h1 = markdown_parser.H1("# this is a test")

    h11 = markdown_parser.H1("# this is a test")
    assert not h1.is_acceptable(h11)
    assert not h1.is_acceptable(h1)

    root = markdown_parser.Root()
    assert not h1.is_acceptable(root)

    h2 = markdown_parser.H2("## this is a test")
    assert h1.is_acceptable(h2)

    h3 = markdown_parser.H3("### this is a test")
    assert h1.is_acceptable(h3)

    text = markdown_parser.Text()
    assert h1.is_acceptable(text)

    table = markdown_parser.Table()
    assert h1.is_acceptable(table)

    line = markdown_parser.TextLine("junk")
    assert not h1.is_acceptable(line)

    line = markdown_parser.TableLine("|junk|")
    assert not h1.is_acceptable(line)

    assert not h1.is_acceptable("xyz")
    assert not h1.is_acceptable(123)
    assert not h1.is_acceptable(None)


def test_is_acceptable_for_h2():
    h2 = markdown_parser.H2("## this is a test")

    h21 = markdown_parser.H2("## this is a test")
    assert not h2.is_acceptable(h21)
    assert not h2.is_acceptable(h2)

    root = markdown_parser.Root()
    assert not h2.is_acceptable(root)

    h1 = markdown_parser.H1("# this is a test")
    assert not h2.is_acceptable(h1)

    h3 = markdown_parser.H3("### this is a test")
    assert h2.is_acceptable(h3)

    text = markdown_parser.Text()
    assert h2.is_acceptable(text)

    table = markdown_parser.Table()
    assert h2.is_acceptable(table)

    line = markdown_parser.TextLine("junk")
    assert not h2.is_acceptable(line)

    line = markdown_parser.TableLine("|junk|")
    assert not h2.is_acceptable(line)

    assert not h2.is_acceptable("xyz")
    assert not h2.is_acceptable(123)
    assert not h2.is_acceptable(None)


def test_is_acceptable_for_h3():
    h3 = markdown_parser.H3("## this is a test")

    h31 = markdown_parser.H3("## this is a test")
    assert not h3.is_acceptable(h31)
    assert not h3.is_acceptable(h3)

    root = markdown_parser.Root()
    assert not h3.is_acceptable(root)

    h1 = markdown_parser.H1("# this is a test")
    assert not h3.is_acceptable(h1)

    h2 = markdown_parser.H2("### this is a test")
    assert not h3.is_acceptable(h2)

    text = markdown_parser.Text()
    assert h3.is_acceptable(text)

    table = markdown_parser.Table()
    assert h3.is_acceptable(table)

    line = markdown_parser.TextLine("junk")
    assert not h3.is_acceptable(line)

    line = markdown_parser.TableLine("|junk|")
    assert not h3.is_acceptable(line)

    assert not h3.is_acceptable("xyz")
    assert not h3.is_acceptable(123)
    assert not h3.is_acceptable(None)


def test_is_acceptable_for_text():
    text = markdown_parser.Text()

    text1 = markdown_parser.Text()

    assert not text.is_acceptable(text1)
    assert not text.is_acceptable(text)

    root = markdown_parser.Root()
    assert not text.is_acceptable(root)

    h1 = markdown_parser.H1("# this is a test")
    assert not text.is_acceptable(h1)

    h2 = markdown_parser.H2("### this is a test")
    assert not text.is_acceptable(h2)

    h3 = markdown_parser.H3("### this is a test")
    assert not text.is_acceptable(h3)

    text = markdown_parser.Text()
    assert not text.is_acceptable(text)

    line = markdown_parser.TableLine("|junk|")
    assert not text.is_acceptable(line)

    line = markdown_parser.TextLine("junk")
    assert text.is_acceptable(line)

    assert not text.is_acceptable("xyz")
    assert not text.is_acceptable(123)
    assert not text.is_acceptable(None)


def test_is_acceptable_for_table():
    table = markdown_parser.Table()

    table1 = markdown_parser.Table()

    assert not table.is_acceptable(table1)
    assert not table.is_acceptable(table)

    root = markdown_parser.Root()
    assert not table.is_acceptable(root)

    h1 = markdown_parser.H1("# this is a test")
    assert not table.is_acceptable(h1)

    h2 = markdown_parser.H2("### this is a test")
    assert not table.is_acceptable(h2)

    h3 = markdown_parser.H3("### this is a test")
    assert not table.is_acceptable(h3)

    text = markdown_parser.Text()
    assert not table.is_acceptable(text)

    line = markdown_parser.TextLine("junk")
    assert not table.is_acceptable(line)

    line = markdown_parser.TableLine("|junk|")
    assert table.is_acceptable(line)

    assert not table.is_acceptable("|xyz|")
    assert not table.is_acceptable(123)
    assert not table.is_acceptable(None)


def test_adding_lines_to_text():
    t = markdown_parser.Text()

    lines = [
        "this is",
        "a test"
    ]
    for line in lines:
        t.add_child(markdown_parser.TextLine(line))
    retrieved_text = t.get_text()
    retrieved_lines = retrieved_text.split("\n")
    assert retrieved_lines == lines


def test_adding_lines_to_table():
    t = markdown_parser.Table()

    lines = [
        "|this is|",
        "|a test|"
    ]
    for line in lines:
        t.add_child(markdown_parser.TableLine(line))
    retrieved_text = t.get_table()
    retrieved_lines = retrieved_text.split("\n")
    assert retrieved_lines == lines
