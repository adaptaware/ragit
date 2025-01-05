"""Exposes the functionality to parse a markdown file."""


def iter_markdown(filename):
    root = Node(Node.ROOT_NAME)
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            root.add(line)
    for node in root.get_nodes():
        if isinstance(node, (Text, Table)):
            yield node


class Node:
    ROOT_NAME = "__markdown__root__"

    def __init__(self, caption):
        assert caption, "Header caption cannot be empty."
        self._children = []
        self._tail = self
        self._parent = None
        self._caption = caption

    def _is_root(self):
        return self._caption == Node.ROOT_NAME

    def set_tail(self, new_tail):
        if self._is_root():
            self._tail = new_tail
        else:
            self._parent.set_tail(new_tail)

    def headers_path(self):
        return ' => '.join(reversed(self._get_header_path()))

    def _get_header_path(self):
        headers = []
        if not self._is_root():
            headers.append(self._caption)
        if self._parent:
            headers.extend(self._parent._get_header_path())
        return headers

    def __repr__(self):
        return f"{self.__class__.__name__}(caption={self._caption})"

    def get_nodes(self):
        yield self
        for node in self._children:
            if isinstance(node, Node):
                for n in node.get_nodes():
                    yield n
            else:
                yield node

    def add(self, line):
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
            return H1Node(stripped[2:])
        elif stripped.startswith("## "):
            return H2Node(stripped[3:])
        elif stripped.startswith("### "):
            return H3Node(stripped[4:])
        elif stripped.startswith("|") and stripped.endswith("|"):
            return Table(stripped)
        else:
            return Text(stripped)

    def _add_node(self, other):
        if self._tail.can_add(other):
            if isinstance(self._tail, Table):
                self._tail.merge(other)
            elif isinstance(self._tail, Text):
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
        return isinstance(other, (H1Node, H2Node, H3Node, Table, Text))


class H1Node(Node):
    def can_add(self, other):
        return isinstance(other, (H2Node, H3Node, Table, Text))


class H2Node(Node):
    def can_add(self, other):
        return isinstance(other, (H3Node, Table, Text))


class H3Node(Node):
    def can_add(self, other):
        return isinstance(other, (Table, Text))


class LineContainer:
    def __init__(self, line):
        self._lines = [line]
        self._parent = None

    def get_headers(self):
        if isinstance(self._parent, Node):
            return self._parent.headers_path()
        else:
            return "path in not available."

    def merge(self, other):
        assert type(other) is type(self)
        self._lines.extend(other._lines)

    def get_inner_text(self):
        return '\n'.join(self._lines)

    def __repr__(self):
        return f"{self.__class__.__name__}(lines={self._lines})"

    def __str__(self):
        return f"{self.__class__.__name__}(lines={self._lines})"


class Table(LineContainer):
    def can_add(self, other):
        return isinstance(other, Table)


class Text(LineContainer):
    def can_add(self, other):
        return isinstance(other, Text)
