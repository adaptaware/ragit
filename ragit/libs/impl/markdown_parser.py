"""Exposes the functionality to parse a markdown file."""

import abc
import enum


class SectionType(enum.IntEnum):
    """Defines the type of the section."""

    TEXT = 1
    TABLE = 2


class IMarkdownSection(abc.ABC):
    """Abstract class to represent a section container (Text or table)."""

    @abc.abstractmethod
    def get_headers(self):
        """Returns the headers path leading to this section.

        :return: The headers path.
        :rtype: str
        """

    @abc.abstractmethod
    def get_inner_text(self):
        """Returns the inner text of the section.

        :return: The inner text.
        :rtype: str
        """

    @abc.abstractmethod
    def get_section_type(self):
        """Returns the type of the section.

        :return: The type of the section.
        :rtype: SectionType.
        """


def iter_markdown(filename):
    """Iterates over markdown elements in the given file.

    This function reads a markdown file and yields nodes of type Text or Table.

    :param str filename: The path to the markdown file.
    :yield: IMarkdownSection instance of type Text or Table.
    :rtype: Generator[Union[Text, Table], None, None]
    """
    root = _Node(_Node.ROOT_NAME)
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            root.add(line)
    for node in root.get_nodes():
        if isinstance(node, (_Text, _Table)):
            yield node


# What follows is an implementation detail that is not meant to be used
# from client code.

class _Node:
    """Represents a generic node in the markdown document.

    A Node can be a header (H1, H2, H3), Text, or Table. Each node can
    have multiple children nodes.

    :param str caption: The caption or header text of the node.
    """

    ROOT_NAME = "__markdown__root__"

    def __init__(self, caption):
        """Initializes a Node with the given caption.

        :param str caption: The caption or header text of the node.
        :raise AssertionError: If caption is empty.
        """
        assert caption, "Header caption cannot be empty."
        self._children = []
        self._tail = self
        self._parent = None
        self._caption = caption

    def _is_root(self):
        """Checks if the node is the root node.

        :return: True if the node is the root node, False otherwise.
        :rtype: bool
        """
        return self._caption == _Node.ROOT_NAME

    def set_tail(self, new_tail):
        """Sets the tail node to the given new tail.

        :param _Node new_tail: The new tail node.
        """
        if self._is_root():
            self._tail = new_tail
        else:
            self._parent.set_tail(new_tail)

    def headers_path(self):
        """Returns the path of headers leading to this node.

        :return: The path of headers.
        :rtype: str
        """
        return ' => '.join(reversed(self.get_header_path()))

    def get_header_path(self):
        """Recursively collects the headers path.

        :return: List of headers leading to this node.
        :rtype: list
        """
        headers = []
        if not self._is_root():
            headers.append(self._caption)
        if self._parent:
            headers.extend(self._parent.get_header_path())
        return headers

    def __repr__(self):
        """Returns the string representation of the Node.

        :return: The string representation of the Node.
        :rtype: str
        """
        return f"{self.__class__.__name__}(caption={self._caption})"

    def get_nodes(self):
        """Generates all nodes in the subtree rooted at this node.

        :yield: Nodes in the subtree rooted at this node.
        :rtype: Generator[Node, None, None]
        """
        yield self
        for node in self._children:
            if isinstance(node, _Node):
                for n in node.get_nodes():
                    yield n
            else:
                yield node

    def add(self, line):
        """Adds a new node based on the given line to the current node.

        :param str line: The line of text to add.
        """
        new_node = self._make_node(line)
        self._add_node(new_node)

    @classmethod
    def _make_node(cls, line):
        """Returns the node type for the passed in line.

        :param str line: The line of text to get its node type.

        :return: The node type and the value of the line.
        :rtype: Tuple
        """
        stripped = line.strip()
        if stripped.startswith("# "):
            return _H1Node(stripped[2:])
        elif stripped.startswith("## "):
            return _H2Node(stripped[3:])
        elif stripped.startswith("### "):
            return _H3Node(stripped[4:])
        elif stripped.startswith("|") and stripped.endswith("|"):
            return _Table(stripped)
        else:
            return _Text(stripped)

    def _add_node(self, other):
        """Adds a new node to the current node's children.

        :param _Node |_Table | _Text other: The new node to add.
        """
        if self._tail.can_add(other):
            if isinstance(self._tail, _Table):
                self._tail.merge(other)
            elif isinstance(self._tail, _Text):
                self._tail.merge(other)
            else:
                self._tail._children.append(other)
                other._parent = self._tail
                self.set_tail(other)
        else:
            parent = self._tail._parent
            self.set_tail(parent)
            parent._add_node(other)

    def can_add(self, other):
        """Checks if the current node can add the given node.

        :param _Node other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, (_H1Node, _H2Node, _H3Node, _Table, _Text))


class _H1Node(_Node):
    """Represents a first-level header node (H1) in the markdown document."""

    def can_add(self, other):
        """Checks if the current H1Node can add the given node.

        :param _Node other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, (_H2Node, _H3Node, _Table, _Text))


class _H2Node(_Node):
    """Represents a second-level header node (H2) in the markdown document."""

    def can_add(self, other):
        """Checks if the current H2Node can add the given node.

        :param _Node other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, (_H3Node, _Table, _Text))


class _H3Node(_Node):
    """Represents a third-level header node (H3) in the markdown document."""

    def can_add(self, other):
        """Checks if the current H3Node can add the given node.

        :param _Node other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, (_Table, _Text))


class _LineContainer(IMarkdownSection):
    """Represents a container for lines of text in the markdown document."""

    def __init__(self, line):
        """Initializes a LineContainer with the given line.

        :param str line: The initial line of text.
        """
        self._lines = [line]
        self._parent = None

    def get_headers(self):
        """Returns the headers path leading to this line container.

        :return: The headers path.
        :rtype: str
        """
        if isinstance(self._parent, _Node):
            return self._parent.headers_path()
        else:
            return "path in not available."

    def merge(self, other):
        """Merges the given LineContainer with the current one.

        :param _LineContainer other: The LineContainer to merge with.
        :raise AssertionError: If the types of the containers do not match.
        """
        assert type(other) is type(self)
        self._lines.extend(other._lines)

    def get_inner_text(self):
        """Returns the inner text of the LineContainer.

        :return: The inner text.
        :rtype: str
        """
        return '\n'.join(self._lines)

    def __repr__(self):
        """Returns the string representation of the LineContainer.

        :return: The string representation of the LineContainer.
        :rtype: str
        """
        return f"{self.__class__.__name__}(lines={self._lines})"

    def __str__(self):
        """Returns the string representation of the LineContainer.

        :return: The string representation of the LineContainer.
        :rtype: str
        """
        return f"{self.__class__.__name__}(lines={self._lines})"


class _Table(_LineContainer):
    """Represents a table in the markdown document."""

    def can_add(self, other):
        """Checks if the current Table can add the given node.

        :param _LineContainer other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, _Table)

    def get_section_type(self):
        """Returns the type of the section.

        :return: The type of the section.
        :rtype: SectionType.
        """
        return SectionType.TABLE


class _Text(_LineContainer):
    """Represents a block of text in the markdown document."""

    def can_add(self, other):
        """Checks if the current Text can add the given node.

        :param _LineContainer other: The node to check.
        :return: True if the node can be added, False otherwise.
        :rtype: bool
        """
        return isinstance(other, _Text)

    def get_section_type(self):
        """Returns the type of the section.

        :return: The type of the section.
        :rtype: SectionType.
        """
        return SectionType.TEXT
