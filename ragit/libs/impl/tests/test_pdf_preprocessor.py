"""Tests the pdf_preprocessor module."""

import os
import pathlib
import shutil

import pytest

import ragit.libs.impl.pdf_preprocessor as pdf_preprocessor
import ragit.libs.common as common


def test_pdf_to_markdown():
    """Tests creating the markdowns for a pdf file.

    Splits a valid pdf to images and then for each image is calling the
    create_markdown_from_image function that has a side effect to create the
    markdown files fo each image to the directory called markdown one
    flight up from the directory where the images exist.
    """
    common.init_settings()
    pdf_path = "/home/vagrant/ragit-data/dummy/documents/patents.pdf"
    synthetic_dir = "/home/vagrant/ragit-data/dummy/synthetic"

    # Remove the synthetic directory if it exists.
    if os.path.isdir(synthetic_dir):
        shutil.rmtree(synthetic_dir)

    pdf_preprocessor.create_images_for_pdf(pdf_path)
    retrieved = pdf_preprocessor.create_markdowns_for_pdf(pdf_path)

    for filename in retrieved:
        assert os.path.isfile(filename)
        assert filename.endswith(".md")
        name = pathlib.Path(filename).stem
        assert name.startswith("patents")


def test_get_pdf_missing_images():
    """Tests the get_pdf_missing_images function."""
    # Remove the synthetic directory if it exists.
    synthetic_dir = "/home/vagrant/ragit-data/dummy/synthetic"
    if os.path.isdir(synthetic_dir):
        shutil.rmtree(synthetic_dir)

    # Verify how many pdf files are missing images.
    pdfs = list(pdf_preprocessor.get_pdf_missing_images("dummy"))
    assert len(pdfs) == 2

    # Build the images for one of the files.
    pdf_preprocessor.create_images_for_pdf(pdfs[0])
    assert len(list(pdf_preprocessor.get_pdf_missing_images("dummy"))) == 1

    # Build the images for the second file.
    pdf_preprocessor.create_images_for_pdf(pdfs[1])
    assert len(list(pdf_preprocessor.get_pdf_missing_images("dummy"))) == 0


def test_get_images_with_missing_markdowns():
    """Tests the get_images_with_missing_markdowns function."""
    common.init_settings()
    pdf_path = "/home/vagrant/ragit-data/dummy/documents/patents.pdf"
    synthetic_dir = "/home/vagrant/ragit-data/dummy/synthetic"
    if os.path.isdir(synthetic_dir):
        shutil.rmtree(synthetic_dir)
    pdf_preprocessor.create_images_for_pdf(pdf_path)
    imgs = list(pdf_preprocessor.get_images_with_missing_markdowns("dummy"))
    assert len(imgs) == 2

    for img in imgs:
        pdf_preprocessor.create_markdown_from_image(img)

    imgs = list(pdf_preprocessor.get_images_with_missing_markdowns("dummy"))
    assert len(imgs) == 0


def test_create_images_for_pdf():
    """Tests the create_images_for_pdf function."""
    pdf_path = "/home/vagrant/ragit-data/dummy/documents/patents.pdf"
    synthetic_dir = "/home/vagrant/ragit-data/dummy/synthetic"

    # Remove the synthetic directory if it exists.
    if os.path.isdir(synthetic_dir):
        shutil.rmtree(synthetic_dir)

    for _ in range(3):
        retrieved = pdf_preprocessor.create_images_for_pdf(pdf_path)

        # Verify that the synthetic dir was created.
        assert os.path.isdir(synthetic_dir)

        # Verify the retrieved image filenames.
        assert len(retrieved) == 2

        for filename in retrieved:
            assert os.path.isfile(filename)
            assert filename.endswith(".png")
            name = pathlib.Path(filename).stem
            assert name.startswith("patents")


def test_create_images_for_pdf_invalid_path():
    """Tests the create_images_for_pdf passing invalid path."""
    pdf_path = "/home/vagrant/ragit-data/dummy/documents/non-exisiting.pdf"
    with pytest.raises(FileNotFoundError):
        pdf_preprocessor.create_images_for_pdf(pdf_path)


def test_extract_markdown():
    """Tests the _extract_markdown function."""
    txt1 = "this is a test."""
    retrieved = pdf_preprocessor._extract_markdown(txt1)
    assert retrieved == txt1

    txt2 = f"""
'''markdown
{txt1}
'''
    """
    retrieved = pdf_preprocessor._extract_markdown(txt2)
    assert retrieved == txt2


def test_make_markdown_path_1():
    """Tests the _make_markdown_path function."""
    path = "/home/vagrant/ragit-data/dummy/synthetic/images/documents/patents/patents_2.png"
    expected = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/patents/patents_2.md"
    retrieved = pdf_preprocessor._make_markdown_path(path)
    assert expected == retrieved

def test_make_markdown_path_2():
    """Tests the _make_markdown_path function."""
    path ='/home/vagrant/ragit-data/dummy/synthetic/images/documents/nested_dir/nested_2/sample1/sample1_2.png'
    expected ='/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/nested_dir/nested_2/sample1/sample1_2.md'
    retrieved = pdf_preprocessor._make_markdown_path(path)
    assert expected == retrieved

def test_make_markdown_invalid_path():
    """Tests the _make_markdown_path function passing invalid path."""
    path = "/nested_dir/dummy/synthetic/junk/documents/patents/patents_2.png"
    with pytest.raises(ValueError):
        pdf_preprocessor._make_markdown_path(path)


def test_not_image_file():
    """Tests passing a non image."""
    path = "/nested_2/images/file-6/file-6_2.md"
    with pytest.raises(ValueError):
        pdf_preprocessor._make_markdown_path(path)


def test_not_image_directory():
    """Tests passing a non image directory."""
    path = "/nested_2/xyz/file-6/file-6_2.md"
    with pytest.raises(ValueError):
        pdf_preprocessor._make_markdown_path(path)


def test_get_images_dir():
    """Tests the _get_images_dir function."""
    expected = "/home/vagrant/ragit-data/dummy/synthetic/images/documents/patents"
    fullpath = "/home/vagrant/ragit-data/dummy/documents/patents.pdf"
    retrieved = pdf_preprocessor._get_images_dir(fullpath)
    assert retrieved == expected


def test_get_images_dir_invalid_path_1():
    """Tests the _get_images_dir function passing invalid path."""
    with pytest.raises(TypeError):
        pdf_preprocessor._get_images_dir(None)


def test_get_images_dir_invalid_path_2():
    """Tests the _get_images_dir function passing invalid path."""
    with pytest.raises(FileNotFoundError):
        pdf_preprocessor._get_images_dir("junk.txt")


def test_get_images_dir_invalid_path_3():
    """Tests the _get_images_dir function passing invalid path."""
    with pytest.raises(FileNotFoundError):
        pdf_preprocessor._get_images_dir("/xyz/junk.pdf")


def test_get_markdowns_dir():
    """Tests the _get_markdowns_dir function."""
    expected = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/patents"
    fullpath = "/home/vagrant/ragit-data/dummy/documents/patents.pdf"
    retrieved = pdf_preprocessor._get_markdowns_dir(fullpath)
    assert retrieved == expected


def test_get_markdowns_dir_invalid_path_1():
    """Tests the _get_markdowns_dir function passing invalid path."""
    with pytest.raises(TypeError):
        pdf_preprocessor._get_markdowns_dir(None)


def test_get_markdowns_dir_invalid_path_2():
    """Tests the _get_markdowns_dir function passing invalid path."""
    with pytest.raises(FileNotFoundError):
        pdf_preprocessor._get_markdowns_dir("junk.txt")


def test_get_markdowns_dir_invalid_path_3():
    """Tests the _get_markdowns_dir function passing invalid path."""
    with pytest.raises(FileNotFoundError):
        pdf_preprocessor._get_markdowns_dir("/xyz/junk.pdf")


def test_get_pdf_from_markdown_invalid_path_1():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        pdf_preprocessor.get_pdf_from_markdown(None)


def test_get_pdf_from_markdown_invalid_path_2():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        pdf_preprocessor.get_pdf_from_markdown("junk.txt")


def test_get_pdf_from_markdown_invalid_path_3():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        pdf_preprocessor.get_pdf_from_markdown("/xyz/junk.pdf")


def test_get_pdf_from_markdown_invalid_path_4():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(IndexError):
        markdown = "/home/vagrant/ragit-data/dummy_6.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_6():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_7():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/junk_9.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_9():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/xyz/junk_11.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_10():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/junk_13.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_11():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/xyz/junk_15.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_12():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/junk_17.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_13():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/xyz/junk_19.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_14():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/patents/patents_a.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_15():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/xyz/patents_22.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_16():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/dummy/synthetic/markdowns/documents/xyz/patents_22.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_17():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/junk/markdowns/documents/xyz/xyz_22.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_18():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/xyz/xyz_22.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown_invalid_path_19():
    """Tests the get_pdf_from_markdown function passing invalid path."""
    with pytest.raises(ValueError):
        markdown = "/home/vagrant/ragit-data/dummy/synthetic/junk/xyz/xyz_22.md"
        pdf_preprocessor.get_pdf_from_markdown(markdown)


def test_get_pdf_from_markdown():
    """Tests getting the pdf from a markdown file."""
    markdown = "/home/vagrant/ragit-data/dummy/synthetic/markdowns/documents/patents/patents_1.md"
    expected = "/home/vagrant/ragit-data/dummy/documents/patents.pdf", 1

    retrieved = pdf_preprocessor.get_pdf_from_markdown(markdown)
    assert expected == retrieved
