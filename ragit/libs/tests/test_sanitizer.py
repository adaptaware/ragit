"""Tests the common mojule."""

import os
import ragit.libs.sanitizer as sanitizer
import re
import tempfile
import unittest

sanitize_filename = sanitizer._sanitize_filename
rename_file = sanitizer._rename_file_if_needed

VALID_PATHS = [
    ("/ada/ccc/xxx", "/ada/ccc/xxx"),
    ("/ada/ccc/xxx junk", "/ada/ccc/xxx_junk"),
    ("/ada/ccc/xxx junk.....", "/ada/ccc/xxx_junk"),
    ("/ada/ccc/xxx.yyy.junk.", "/ada/ccc/xxx.yyy.junk"),
    ("/home/user/file.txt", "/home/user/file.txt"),
    ("/documents/reports/summary.pdf", "/documents/reports/summary.pdf"),
    ("/projects/code/hello world.py", "/projects/code/hello_world.py"),
    ("/backup/2023/report v1.doc", "/backup/2023/report_v1.doc"),
    ("/music/album/song...mp3", "/music/album/song.mp3"),
    ("/work/draft' abc.doc", "/work/draft_abc.doc"),
    ("/work/draft'        abc.doc", "/work/draft_abc.doc"),
    ("/work/draft'%$#@abc.doc", "/work/draftabc.doc"),
    ("/ada/ccc/special%20", "/ada/ccc/special20"),
    ("xxx", "xxx"),
    ("/xxx", "/xxx"),
]

INVALID_PATHS = [
    "/temp/.temp_file.txt",
    "/bin/utils/.hiddenfile",
    "/work/#draft.doc",
    "/ada/ccc/#junk",
    "/ada/ccc/<>file.txt",
    "/ada/ccc/file/?abc.txt",
    "/ada /ccc/xxx",
    "/ada/ccc/@ada/mixed spaces ",
]


class TestSanitizeFile(unittest.TestCase):
    """Tests the sanitize_filename function."""

    def test_valid_paths(self):
        """Tests valid paths."""
        for path, expected in VALID_PATHS:
            retrieved = sanitize_filename(path)
            self.assertEqual(retrieved, expected)

    def test_invalid_paths(self):
        """Tests invalid paths."""
        for path in INVALID_PATHS:
            with self.assertRaises(ValueError):
                sanitize_filename(path)


class TestMakeUniqueFilename(unittest.TestCase):
    """Tests the make_unique_parameterset_ids function."""

    def test_new_sanitized_path(self):
        """Tests a new file that does not exists in the disk."""
        sanitized_path = "junk/junk.txt"
        retrieved = sanitizer._make_unique_filename(sanitized_path)
        self.assertEqual(retrieved, sanitized_path)

    def test_sanitizing_existing_path(self):
        """Tests sanitizing an existing path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "xyz-abc.txt")
            # Open the file in write mode and write "hello" to it
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write("hello")
            retrieved = sanitizer._make_unique_filename(temp_file_path)
            pattern = re.escape(temp_file_path[:-4]) + r"-[a-zA-Z0-9]{8}\.txt$"
            # Check if the random characters were added.
            is_a_match = re.match(pattern, retrieved) is not None
            self.assertTrue(is_a_match)


class TestRenameFile(unittest.TestCase):
    """Tests the rename file function."""

    def test_rename_non_existing_file(self):
        """Tests renaming a non existing file."""
        current_path = "/home/user/xzy"
        sanitized_path = "/home/user/xzy"

        with self.assertRaises(FileNotFoundError):
            retrieved = rename_file(current_path, sanitized_path)

    def test_passing_same_name(self):
        """Tests passing the same name as the file to rename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "xyz.txt")
            # Open the file in write mode and write "hello" to it
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write("hello")
            retrieved = rename_file(temp_file_path, temp_file_path)
            self.assertEqual(retrieved, temp_file_path)

    def test_renaming(self):
        """Tests a non-existing sanitized path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "xyz.txt")
            # Open the file in write mode and write "hello" to it
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write("hello")
            sanitized = os.path.join(temp_dir, "xyza.txt")
            retrieved = rename_file(temp_file_path, sanitized)

            # Verify that we received the sanitized filepath.
            self.assertEqual(retrieved, sanitized)

            # Verify that the sanitized file exists.
            self.assertTrue(os.path.exists(retrieved))

            # Verify that the original file was renamed.
            self.assertFalse(os.path.exists(temp_file_path))

    def test_create_new_sanitized_file(self):
        """Tests existing sanitized file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "xyz.txt")

            # Open the file in write mode and write "hello" to it
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write("hello")

            sanitized = os.path.join(temp_dir, "xyza.txt")

            # Create a pre-exising sanitized file to force a new name.
            with open(sanitized, 'w') as temp_file:
                temp_file.write("hello")

            retrieved = rename_file(temp_file_path, sanitized)

            # Verify that we received the sanitized filepath.
            self.assertNotEqual(retrieved, sanitized)

            # Verify that the sanitized file exists.
            self.assertTrue(os.path.exists(retrieved))

            # Verify that the original file was renamed.
            self.assertFalse(os.path.exists(temp_file_path))

    def test_ensure_sanitized(self):
        """Tests the ensure sanitized function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "xyz ' junk.txt")
            # Open the file in write mode and write "hello" to it
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write("hello")
            retrieved = sanitizer.ensure_sanitized(temp_file_path)
            expected = os.path.join(temp_dir, "xyz_junk.txt")
            self.assertEqual(retrieved, expected)
            self.assertTrue(os.path.exists(retrieved))
            self.assertFalse(os.path.exists(temp_file_path))


