"""Implements a function to sanitize a filename."""

import os
import re
import uuid


def ensure_sanitized(fullpath):
    """Returns the full path to the passed in file.

    If necessary the passed in file will be sanitized to make process easier
    and also it will rename the file in the disk.

    :param str fullpath: Can be either a filename or a path to a filename.

    :returns: The sanitized fullpath.
    :rtype: str

    :raises ValueError
    :raises FileNotFoundError
    :raises OSError
    """
    sanitized_path = _sanitize_filename(fullpath)
    return _rename_file_if_needed(fullpath, sanitized_path)


# What follows is private to this module (do not use from the outside).


def _rename_file_if_needed(current_path, sanitized_path):
    """Renames a file from current_path to a unique sanitized_path.

    If the current path does not exist then an exception is raised.

    If the sanitized_path already exists, appends an index to make it unique.

    :param str current_path: The current file path.
    :param str sanitized_path: The desired new file path.

    :returns: The sanitized path; note that in the case that the sanitized path
    already exists (in the case of multiple renames) then the sanitized file
    will be appended and index in the end of the file (right before the
    extension).

    :raises FileNotFoundError: If the current_path does not exist.
    :raises OSError: For other OS related errors.
    """
    if not os.path.exists(current_path):
        raise FileNotFoundError
    elif current_path == sanitized_path:
        # Nothing to do.
        pass
    elif os.path.exists(sanitized_path) is False:
        # If the sanitized_path does not already exist just rename and return.
        os.rename(current_path, sanitized_path)
    else:
        # Sanitized filename already exists, convert it to unique and rename.
        sanitized_path = _make_unique_filename(sanitized_path)
        os.rename(current_path, sanitized_path)
    return sanitized_path


def _sanitize_filename(fullpath):
    """Sanitizes a fullpath to a file for Linux filesystem compatibility.

    The name of a subdirectory cannot contain spaces of invalid characters; if
    any of them is encountered then a ValueError is raised. No changes at all
    are attempted to the path to the file but instead we are expecting it to be
    passed in the expected format.

    The filename must not be hidden (staring with a period). Spaces will be
    converted in underscores while invalid characters will be removed.

    :param str fullpath: Can be either a filename or a path to a filename.

    :returns: The sanitized fullpath.

    :raises: ValueError
    """
    assert fullpath, "Invalid fullpath"
    tokens = fullpath.split("/")
    filename = tokens[-1]
    if len(tokens) > 1:
        subdirs = tokens[:-1]
        for subdir in subdirs:
            _validate_subdirectory(subdir)

    filename = filename.replace(" ", "_")
    assert "/" not in filename, "Forward slash in filename not allowed."
    if filename.startswith("."):
        raise ValueError("Hidden files not supported.")

    if filename[0] in _SPECIAL_CHARACTERS:
        raise ValueError("Invalid name")

    # Remove characters that are not allowed in Linux filenames
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

    # Remove leading and trailing dots
    filename = filename.strip(".")

    # Convert multiple subsequent dots to a single one.
    filename = re.sub(r'\.{2,}', '.', filename)

    # Convert multiple underscores to a single one.
    filename = re.sub(r'\_{2,}', '_', filename)

    # Substiture the last token with the sanitized filename.
    tokens[-1] = filename

    # Returns the sanitized path.
    sanitized = "/".join(tokens)
    return sanitized


def _validate_subdirectory(subdir):
    """Validates the passed in subdir.

    :param str subdir: The subdir to validate.

    :raises: ValueError
    """
    if not subdir:
        return

    c = set(subdir)
    if not c.isdisjoint(_SPECIAL_CHARACTERS):
        raise ValueError


def _make_unique_filename(sanitized_path):
    """Generate a unique file path to avoid overwriting existing files.

    This function checks if the given `sanitized_path` corresponds to an
    existing file. If it does, the function appends a unique identifier to the
    filename (before the file extension) to ensure the new filename is unique.
    This is achieved by incorporating a short UUID segment.

    :param str sanitized_path: The file path to be evaluated and potentially
    modified to ensure uniqueness.

    :returns: A unique file path, either the same as `sanitized_path` if no
    file exists at that path, or a new path with a unique identifier integrated
    into the filename.

    :rtype: str
    """
    if not os.path.exists(sanitized_path):
        return sanitized_path

    # At this point, the sanitized path already exists on disk. To create a
    # unique filename and prevent overwriting the existing file, we append a
    # segment of a UUID after the original file's name but before its
    # extension. For example, if the original filename is 'xyz.abc' and it
    # exists, we'll generate something like 'xyz-abcdefgh.abc', where
    # 'abcdefgh' is derived from a UUID, providing a unique identifier.

    # Get the parent directory
    parent_directory = os.path.dirname(sanitized_path)

    # Get the filename
    filename = os.path.basename(sanitized_path)

    # Break it down to name and extension.
    name, extension = filename.split(".")

    index = str(uuid.uuid4())[:8]

    new_filename = f'{name}-{index}'
    if extension:
        new_filename += f".{extension}"

    new_sanitized_path = os.path.join(parent_directory, new_filename)

    return new_sanitized_path


_SPECIAL_CHARACTERS = {
    "#",  # pound
    "%",  # percent
    "&",  # ampersand
    "{",  # left curly bracket
    "}",  # right curly bracket
    "\\",  # back slash
    "<",  # left angle bracket
    ">",  # right angle bracket
    "*",  # asterisk
    "?",  # question mark
    "/",  # forward slash
    " ",  # blank space
    "$",  # dollar sign
    "!",  # exclamation point
    "'",  # single quotes
    '"',  # double quotes
    ":",  # colon
    "@",  # at sign
    "+",  # plus sign
    "`",  # backtick
    "|",  # pipe
    "=",  # equal sign
    "😀",  # grinning face emoji
    "🎉",  # party popper emoji
    "❤️",  # red heart emoji
    "\u00A9",  # © copyright sign
    "\u00AE",  # ® registered trademark
    "\u2022",  # • bullet
    "\u20AC",  # € euro sign
}
