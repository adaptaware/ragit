
"""Tests the pdf_preprocessor module."""

import os
import shutil

import pytest

import ragit.libs.impl.pdf_preprocessor as pp
import ragit.libs.common as common

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_create_markdowns_from_pdf_file_not_found():
    """Tests passing not exising file as pdf."""
    d = common.get_testing_data_directory()
    not_existing_path = os.path.join(d, "junk-junk")
    with pytest.raises(ValueError):
        pp.create_markdowns_from_pdf(not_existing_path)


def test_create_markdowns_from_pdf():
    """Tests passing valid file as pdf.

    - Copy a pdf file to the testing data directory (under the root) so we are
      not poluting the namespace of the project.

    - Assuming a pdf named xyz.pdf we expect the markdown files to be created
      under a dictory named xyz_md so if this directory already exists (as a
      leftover from a previous run for example) delete it.

    - Call the create_markdowns_for_pdf and verify that the expected markdowns
      are created successfully.
    """
    common.init_settings()
    filename_no_ext = "ai_hype"
    filename = f"{filename_no_ext}.pdf"
    src_path = os.path.join(_CURRENT_DIR, "static", filename)
    home_dir = common.get_home_dir()
    pdf_path = os.path.join(home_dir, "testing_output", filename)

    if os.path.isdir(pdf_path):
        os.remove(pdf_path)

    markdown_dir = pp.get_markdown_directory_name(pdf_path)
    if os.path.isdir(markdown_dir):
        shutil.rmtree(markdown_dir)

    assert pp.needs_to_create_markdowns(pdf_path) == True

    shutil.copyfile(src_path, pdf_path)
    pp.create_markdowns_from_pdf(pdf_path)

    assert pp.needs_to_create_markdowns(pdf_path) == False
