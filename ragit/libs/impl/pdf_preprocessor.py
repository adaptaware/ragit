"""Implements the pdf splitter."""

import datetime
import os
import pathlib
import shutil

from llama_parse import LlamaParse

import ragit.libs.sanitizer as sanitizer

def needs_to_create_markdowns(pdf_path):
    """Checks if the markdowns for the pdf need to be created.

    :param str pdf_path: The pdf file to check if needs to create markdowns.

    :returns: True if it needs to create markddown files.
    :rtype: bool
    """
    markdown_path = get_markdown_directory_name(pdf_path)
    markdowns_exist = os.path.exists(markdown_path)
    return markdowns_exist is False


def get_markdown_directory_name(pdf_path):
    """Gets the directory name to contain the markdowns (without creating it).

    The path markdown directory is the same as for the passed in pdf
    but substituting the extension .pdf with the extension .markdown.

    No Side effects.

    :param str pdf_path: The path to create the markdown directory.

    :returns: The full path to the directory that will contain the
    markdown files for the passed in pdf.
    :rtype: str

    :raises: ValueError
    """
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"Invalid file: {pdf_path}")
    else:
        return pdf_path[:-4] + '_markdown_'


def create_markdowns_from_pdf(pdf_path):
    """Creates the markdown files that correspond to the passed in pdf file.

    For each page included in the passed in pdf file a new markdown file is
    created. For each pdf a new directory is created (with the name of the pdf
    file without its extension) and the markdowns are copied there.

     Side effects
     ------------
    - Sanitizes (in place) the passed in path.
    - Creates the directory for the markdown files.
    - Creates the markdown files inside the above directory.

    :param str pdf_path: The path to the pdf to break it down.

    :raises: ValueError
    """
    if not os.path.isfile(pdf_path) or not pdf_path.endswith("pdf"):
        raise ValueError(f"Invalid file: {pdf_path}")
    pdf_path = sanitizer.ensure_sanitized(pdf_path)
    output_dir = get_markdown_directory_name(pdf_path)
    if os.path.isdir(output_dir):
        # Already exist, do not recreate.
        return
    temp_output_dir = f"{output_dir}_temp"

    # Delete leftover dir if there is a leftover.
    if os.path.isdir(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir)

    parser = LlamaParse(
        result_type="markdown",
        auto_mode=True,
        auto_mode_trigger_on_image_in_page=True,
        auto_mode_trigger_on_table_in_page=True,
    )

    t1 = datetime.datetime.now()
    documents = parser.load_data(pdf_path)
    filename_no_ext = pathlib.Path(pdf_path).stem
    for index, doc in enumerate(documents, start=1):
        output_file = os.path.join(temp_output_dir, f"{filename_no_ext}-{index}.md")
        print(f"creating {output_file}")
        with open(output_file, 'w') as fout:
            fout.write(doc.text)

    # The full pdf was processed, rename the temp directory.
    os.rename(temp_output_dir, output_dir)
    t2 = datetime.datetime.now()
    print(pdf_path, " Duration:", (t2-t1).total_seconds())
