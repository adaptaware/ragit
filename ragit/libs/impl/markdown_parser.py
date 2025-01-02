"""Exposes the functionality to parse a markdown file."""

import abc
import enum


class NodeType(enum.IntEnum):
    """Represents the type of single line (based on its first char.)"""

    ROOT = 0
    HEADING_1 = 1  # Corresponds to "#"
    HEADING_2 = 2  # Corresponds to "##"
    HEADING_3 = 3  # Corresponds to "###"
    TEXT = 7  # Typical text paragraph
    CODE_BLOCK = 8  # Corresponds to code fences ```
    HORIZONTAL_RULE = 9  # Corresponds to "---" or "***" or "___"
    TABLE = 10  # Markdown tables (start / end with |)

    @classmethod
    def get_node_type(cls, line):
        """Returns the node type for the passed in line.

        :param str line: The line of text to get its node type.

        :return: The node type for the passed in line.
        :rtype: NodeType.
        """
        stripped = line.strip()
        if stripped.startswith("# "):
            return NodeType.HEADING_1
        elif stripped.startswith("## "):
            return NodeType.HEADING_2
        elif stripped.startswith("### "):
            return NodeType.HEADING_3
        elif stripped.startswith("|") and stripped.endswith("|"):
            return NodeType.TABLE
        elif stripped[:3] in ("---", "***", "___"):
            return NodeType.HORIZONTAL_RULE
        else:
            return NodeType.TEXT


class Component:
    _parent = None

    def set_parent(self, parent):
        self._parent = parent


class Leaf(Component):
    _value = None

    def get_value(self):
        return self._value


class TextLine(Leaf):
    def __init__(self, value):
        assert NodeType.get_node_type(value) == NodeType.TEXT
        self._value = value


class TableLine(Leaf):
    def __init__(self, value):
        assert NodeType.get_node_type(value) == NodeType.TABLE
        self._value = value


class Composite(Component):
    _children = None
    _acceptable = None
    _parent = None

    def __init__(self, *acceptable):
        self._acceptable = set(acceptable[:])
        self._children = []

    def is_acceptable(self, component):
        return type(component) in self._acceptable

    def set_parent(self, parent):
        self._parent = parent

    def get_parent(self):
        return self._parent

    def add_child(self, child):
        assert isinstance(child, Composite)
        self._children.append(child)


class Root(Composite):
    def __init__(self):
        super().__init__(H1, H2, H3, Text, Table)

    def set_parent(self, parent):
        raise NotImplementedError


class Header(Composite):
    _header = None

    def __init__(self, header, *acceptable):
        super().__init__(*acceptable)
        self._header = header


class H1(Header):
    def __init__(self, header):
        super().__init__(header, H2, H3, Text, Table)


class H2(Header):
    def __init__(self, header):
        super().__init__(header, H3, Text, Table)


class H3(Header):
    def __init__(self, header):
        super().__init__(header, Text, Table)


class Text(Composite):
    def __init__(self):
        super().__init__(TextLine)

    def add_child(self, child):
        assert isinstance(child, TextLine)
        self._children.append(child)

    def get_text(self):
        return '\n'.join([c.get_value() for c in self._children])


class Table(Composite):
    def __init__(self):
        super().__init__(TableLine)

    def add_child(self, child):
        assert isinstance(child, TableLine)
        self._children.append(child)

    def get_table(self):
        return '\n'.join([c.get_value() for c in self._children])


def parse(markdown_path):
    """Parses the passed in markdown file.

    :returns: The root MarkdownContainer for the passed in markdown file.
    :rtype MarkdownNode.
    """
    root = ContainerNode()
    with open(markdown_path) as fin:
        for line in fin.readlines():
            root.process_line(line)
    return root
