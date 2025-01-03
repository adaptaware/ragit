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


def make_node(line):
    node_type = NodeType.get_node_type(line)
    if node_type == NodeType.HEADING_1:
        return H1(line)
    elif node_type == NodeType.HEADING_2:
        return H2(line)
    elif node_type == NodeType.HEADING_3:
        return H3(line)
    elif node_type == NodeType.TEXT:
        return TextLine(line)
    elif node_type == NodeType.TABLE:
        return TableLine(line)
    assert False, "Unknown node type"


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

    def get_path(self):
        if self._parent:
            if isinstance(self, Header):
                return self._parent.get_path() + " - " + self.get_header().strip()
            else:
                return self._parent.get_path().strip()
        else:
            return "ROOT"



    def is_acceptable(self, component):
        return type(component) in self._acceptable

    def set_parent(self, parent):
        self._parent = parent

    def get_parent(self):
        return self._parent

    def add_child(self, child):
        assert isinstance(child, Composite)
        self._children.append(child)

    def get_nodes(self):
        for n in self._children:
            yield n
            if isinstance(n, (H1, H2, H3)):
                for n1 in n.get_nodes():
                    yield n.get_path() + "\n" + str(n1) if isinstance(n1, (Text, Table)) else n1


class Root(Composite):
    def __init__(self):
        super().__init__(H1, H2, H3, Text, Table)
        self._tail = self

    def set_parent(self, parent):
        raise NotImplementedError

    def add_line(self, line):
        n = make_node(line)
        self._add_child_node(n)

    def _add_child_node(self, n):
        if self._tail.is_acceptable(n):
            self._tail.add_child(n)
            n.set_parent(self._tail)
            if isinstance(n, (H1, H2, H3, Text, Table)):
                self._tail = n
        elif type(n) is TextLine:
            t = Text()
            t.add_child(n)
            self._add_child_node(t)
        elif type(n) is TableLine:
            t = Table()
            t.add_child(n)
            self._add_child_node(t)
        else:
            self._tail = self._tail.get_parent()
            self._add_child_node(n)


class Header(Composite):
    _header = None

    def __init__(self, header, *acceptable):
        super().__init__(*acceptable)
        self._header = header

    def get_header(self):
        return self._header

    def __str__(self):
        return f'{self._header}'


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

    def __str__(self):
        return '\n'.join([c.get_value() for c in self._children])

    def __repr__(self):
        return '\n'.join([c.get_value() for c in self._children])


class Table(Composite):
    def __init__(self):
        super().__init__(TableLine)

    def add_child(self, child):
        assert isinstance(child, TableLine)
        self._children.append(child)

    def __str__(self):
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
