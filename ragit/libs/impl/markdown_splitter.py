"""Defines the markdown splitter functionality."""

import bisect
import re


def get_chunks(txt, chunk_size=800):
    """Splits a text into chunks based on punctuation or size.

    :param str txt: The text to be split into chunks.

    :param int chunk_size: The maximum size of each chunk in characters.

    :returns: Yields chunks of the text.
    :rtype: generator.
    """

    txt = txt.strip()
    if not txt:
        return

    txt = re.sub(r'\n+', '\n', txt)
    separator_indexes = []

    for index, c in enumerate(txt):
        if c in ('.',):
            separator_indexes.append(index)

    if not separator_indexes:
        # There are no periods.
        chunk = txt[:chunk_size]
        yield chunk
        for chunk in get_chunks(txt[chunk_size:], chunk_size):
            yield chunk
    else:
        ci = _find_closest_index(separator_indexes, chunk_size)
        cutoff = separator_indexes[ci] + 1
        yield txt[:cutoff]

        for c in get_chunks(txt[cutoff:], chunk_size):
            yield c


# The following are private implementation details.

def _find_closest_index(sorted_list, target):
    """Finds the closest index in a sorted list for a given target.

    :param List sorted_list: The list within which to find the closest index.

    :param int target: The target value to find the closest index for.

    :returns: The index of the closest element.
    :rtype: int.
    """
    insert_point = bisect.bisect_left(sorted_list, target)

    if insert_point == 0:
        return 0
    if insert_point == len(sorted_list):
        return len(sorted_list) - 1

    if abs(sorted_list[insert_point] - target) < abs(
            sorted_list[insert_point - 1] - target):
        return insert_point
    else:
        return insert_point - 1
