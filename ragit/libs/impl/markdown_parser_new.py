"""Exposes the functionality to parse a markdown file."""

import abc
import enum


def node_factory(line):
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
    assert False, f"Invalid line: {line}"


class Node:
    def __init__(self, caption):
        assert caption, "Header caption cannot be empty."
        self._children = []
        self._tail = self
        self._parent = None
        self._caption = caption

    def set_tail(self, new_tail):
        if self._caption == "root":
            self._tail = new_tail
        else:
            self._parent.set_tail(new_tail)

    def __repr__(self):
        return self._caption

    def to_str(self):
        lines = self.to_lines()
        return '\n'.join(lines)

    def to_lines(self, depth=0):
        lines = []
        lines.append('---- ' * depth + self._caption)
        for c in self._children:
            for l in c.to_lines(depth + 1):
                lines.append(l)
        return lines

    def add(self, line):
        new_node = node_factory(line)
        self._add_node(new_node)

    def _add_node(self, other):
        if self._tail.can_add(other):
            if isinstance(self._tail, Table):
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
        return isinstance(other, (H1Node, H2Node, H3Node, Table))


class H1Node(Node):
    def can_add(self, other):
        return isinstance(other, (H2Node, H3Node, Table))


class H2Node(Node):
    def can_add(self, other):
        return isinstance(other, (H3Node, Table))


class H3Node(Node):
    def can_add(self, other):
        return isinstance(other, (Table,))


class LineContainer:
    def __init__(self, line):
        self._lines = [line]
        self._parent = None

    def merge(self, other):
        assert type(other) is type(self)
        self._lines.extend(other._lines)

    def to_str(self):
        return '\n'.join(self._lines)

    def to_lines(self, depth=0):
        lines = []
        prefix = '---- ' * depth
        lines.append(prefix + "Table")
        for l in self._lines:
            lines.append(prefix + l)
        return lines

class Table(LineContainer):
    def __repr__(self):
        return '\n'.join(self._lines)

    def can_add(self, other):
        if isinstance(other, Table):
            return True
        elif isinstance(other, str):
            other = other.strip()
            return other.startswith("|") and other.endswith("|")
        return False
