"""Implements the pdf splitter."""

import base64
import datetime
import enum
import os
import pathlib
import re
import shutil
import pdf2image
import requests

import ragit.libs.common as common
import ragit.libs.sanitizer as sanitizer


def get_pdf_missing_images(collection_name):
    """Returns the Pdf that are missing images.

    :param str collection_name: The RAG collection name.

    :yields: The pdf files missing images.
    """
    directory = os.path.join(common.get_shared_directory(), collection_name)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".pdf"):
                fullpath = os.path.join(root, file)
                images_dir = _get_images_dir(fullpath)
                if not os.path.isdir(images_dir):
                    yield fullpath


def get_images_with_missing_markdowns(collection_name):
    """Returns the images that are missing markdowns (but have images).

    :param str collection_name: The RAG collection name.

    :yields: The images files missing markdowns.
    """
    images_directory = os.path.join(
        common.get_shared_directory(),
        collection_name, "synthetic", "images"
    )

    if os.path.isdir(images_directory):
        for root, _, files in os.walk(images_directory):
            for file in files:
                if file.endswith(".png"):
                    image_path = os.path.join(root, file)
                    markdown_path = _make_markdown_path(image_path)
                    if not os.path.isfile(markdown_path):
                        yield image_path


def create_images_for_pdf(pdf_path):
    """Creates an image per each page of the passed in pdf file.

    For each page in the pdf an image will be created under the destination
    directory; each image file goes by the standard name + page index.

    If there is a leftover dirctory holding the images for the passed in pdf
    then it is deleted and recreated; the same applies for the markdowns
    directory as well to keep the orthogonality of the code.

    :param str pdf_path: The path to the pdf file to create the images for.
    for.

    :returns: A list with the paths to all the images that were created.
    :rtype: list

    :raises: ValueError
    :raises: FileNotFoundError
    :raises: OSError
    """
    pdf_path = sanitizer.ensure_sanitized(pdf_path)
    images_dir = _get_images_dir(pdf_path)

    # Remove leftovers if needed.
    if os.path.isdir(images_dir):
        shutil.rmtree(images_dir)

    # Create the images directory.
    pathlib.Path(images_dir).mkdir(parents=True, exist_ok=False)

    # For each page create the corresponding image.
    name = pathlib.Path(pdf_path).stem
    images = pdf2image.convert_from_path(pdf_path)
    image_files = []
    for image_number, img in enumerate(images):
        filepath = os.path.join(images_dir, f"{name}_{image_number+1}.png")
        img.save(filepath)
        image_files.append(filepath)

    return image_files


def create_markdowns_for_pdf(pdf_path):
    """Creates the markdowns for the passed in pdf.

    Requires the images for the passed in pdf to be available if not an
    exception will be raised.

    If the markdowns already exist then an exception will be raised.

    :param str pdf_path: The path to the pdf file to create the markdowns.

    :returns: A list with the paths to all the markdowns that were created.
    :rtype: list

    :raises: ValueError
    :raises: FileNotFoundError
    :raises: OSError
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"{pdf_path} do not exist.")
    pdf_path = sanitizer.ensure_sanitized(pdf_path)
    img_dir = _get_images_dir(pdf_path)
    if not os.path.isdir(img_dir):
        raise FileNotFoundError(f"Images for {pdf_path} do not exist.")

    markdowns_dir = _get_markdowns_dir(pdf_path)
    if os.path.isdir(markdowns_dir):
        raise ValueError(f"Markdowns already exist for {pdf_path}.")

    markdown_paths = []
    for root, _, files in os.walk(img_dir):
        for file in files:
            if file.endswith(".png"):
                image_path = os.path.join(root, file)
                t1 = datetime.datetime.now()
                markdown_path = create_markdown_from_image(image_path)
                t2 = datetime.datetime.now()
                duration = (t2 - t1).total_seconds()
                markdown_paths.append(markdown_path)
                print(f"Converting {image_path} to markdown "
                      f"took {duration} seconds.")
    return markdown_paths


def create_markdown_from_image(img_path):
    """Converts the passed in image to a markdown.

    :param str img_path: The img_path to the image to create markdown for.

    :returns: The path of the markdown that was generated.
    :rtype: str
    """
    with open(img_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    api_key = os.environ.get("OPENAI_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers, json=payload, timeout=60
    )
    x = response.json()
    response = x["choices"][0]["message"]["content"]
    response = _extract_markdown(response)
    markdown_path = _make_markdown_path(img_path)
    path, _ = os.path.split(markdown_path)
    if not os.path.isdir(path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=False)  # here
    with open(markdown_path, 'w') as fout:
        fout.write(response)
    return markdown_path

def get_pdf_from_markdown(markdown_path):
    """Returns the fullpath to the pdf file that corresponds to the markdown.

    :param str markdown_path: The full path to the markdown.

    :returns: The fullpath to the pdf for the markdown.
    :rtype: str

    :raises: ValueError
    :raise: TypeError
    :raise: IndexError
    """
    if not isinstance(markdown_path, str):
        raise ValueError("Invalid type for markdown_path.")

    if not markdown_path.endswith(".md"):
        raise ValueError(f"{markdown_path} is not a markdown file. ")

    base_dir = common.get_shared_directory()
    if not markdown_path.startswith(base_dir):
        raise ValueError(f"{markdown_path} must be under {base_dir}")

    d = markdown_path[len(base_dir):]
    if d.startswith("/"):
        d = d[1:]
    tokens = d.split("/")
    md_file = tokens.pop()
    assert md_file.endswith(".md")
    md_file = md_file[:-3]
    assert '_' in md_file
    try:
        page_number = int(md_file.split("_")[-1])
    except Exception as ex:
        raise ValueError(
            f"invalid markdown path: {markdown_path} "
            f"invalid page number {str(ex)}."
        )

    # Check is the parent dir of the markdown matches the same name.
    x = tokens[-1]
    y = md_file.split("_")[0]
    if x != y:
        raise ValueError(
            f"invalid markdown path: {markdown_path} filename mismatch."
        )

    subpath = []
    rag_collection = tokens.pop(0)
    subpath.append(rag_collection)

    if not tokens or tokens.pop(0) != "synthetic":
        raise ValueError(
            f"invalid markdown path: {markdown_path} synthetic is missing."
        )

    if not tokens or tokens.pop(0) != "markdowns":
        raise ValueError(
            f"invalid markdown path: {markdown_path} markdowns is missing."
        )

    if not tokens or tokens[0] != "documents":
        raise ValueError(
            f"invalid markdown path: {markdown_path} documents is missing."
        )
    subpath.append(tokens.pop(0))
    assert tokens
    tokens[-1] += ".pdf"
    subpath.extend(tokens)
    pdf_path = os.path.join(base_dir, *subpath)
    return pdf_path, page_number
# What follows is private to this module and is not meant to be used from the
# outside (except the related unit tests).


_PROMPT = """
Please analyze the content of the uploaded image and convert it into a
well-structured Markdown document. The Markdown should include the following:

1. *Headings*: Identify and mark any titles or headings in the image using
Markdown syntax (e.g., #, ## for different levels).

2. *Text Content*: Extract and format any paragraphs, lists, or notable text as
Markdown, preserving any hierarchical or ordered structure.

3. *Images or Graphics*: If the image contains embedded graphics or additional
images, describe these elements in plain text and suggest where they might be
included as Markdown image links (e.g., ![Alt Text](URL)).

4. *Tables*: If there are any tables, reformat them into Markdown table syntax.

5. *Links*: If there are hyperlinks, format them appropriately in Markdown
[Link Text](URL).

6. *Code Blocks*: Use Markdown code block syntax (e.g., ```code```) for any
code snippets.

7. *Other Formatting*: Capture any other formatting elements such as bold,
italics, or blockquotes.

Ensure accuracy and maintain the logical structure of the original content to
facilitate effective retrieval by the RAG model.

Your response must ONLY CONTAIN the markdown insider the triple single quotes
without any other text. A valid example of response might be the following:

    ```markdown
    # sample
    test

    ```
"""


def _get_images_dir(pdf_path):
    """Returns the images directory for the passed in type and pdf.

    :param str pdf_path: The full path to the pdf to use.

    :returns: The fullpath to the images directory.
    :rtype: str

    :raises: ValueError
    :raises: FileNotFoundError
    :raises: TypeError
    """
    return _get_synthetic_dir(pdf_path, _SyntheticDir.IMAGES)


def _get_markdowns_dir(pdf_path):
    """Returns the markdown directory for the passed in type and pdf.

    :param str pdf_path: The full path to the pdf to use.

    :returns: The fullpath to the markdown directory.
    :rtype: str

    :raises: ValueError
    """
    return _get_synthetic_dir(pdf_path, _SyntheticDir.MARKDOWN)



def _extract_markdown(txt):
    """Extracts the markdown from an LLM response.

    :param str txt: The response from an LLM; should contain the markdown
    enclosed in triple quotes as follows:

    ```markdown
    # sample
    test

    ```
    :returns: The enclosed markdown; if there txt does not contain the expected
    tags then it returns the full text.
    :rtype: str
    """
    pattern = r"```markdown\s*(.*?)\s*```"
    match = re.search(pattern, txt, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return txt


def _make_markdown_path(image_fullpath):
    """Returns the directory where the markdowns for the passed image.

    :param str image_fullpath: The path to a png image file.

    :returns: The corresponding markdown fullpath for the passed in image.
    :rtype: str

    :raises: ValueError
    """
    if not image_fullpath.endswith(".png"):
        raise ValueError("not a png file")

    image_fullpath = image_fullpath[:-4]
    image_fullpath += ".md"

    if not image_fullpath.startswith(common.get_shared_directory()):
        raise ValueError("invalid image filepath.")

    subpath = image_fullpath[1 + len(common.get_shared_directory()):]
    tokens = subpath.split("/")
    if tokens[2] != "images":
        raise ValueError("invalid image filepath.")
    tokens[2] = "markdowns"
    markdown_path = os.path.join(common.get_shared_directory(),*tokens)
    return markdown_path


class _SyntheticDir(enum.Enum):
    """Designates the type of the synthetic directory."""

    IMAGES = 1
    MARKDOWN = 2


def _get_synthetic_dir(pdf_path, synthetic_dir_type):
    """Returns the synthetic directory for the passed in type and pdf.

    :param str pdf_path: The full path to the pdf to use.
    :_SyntheticDir synthetic_dir_type: The type of the directory.

    :returns: The fullpath to the synthetic directory.
    :rtype: str

    :raises: ValueError
    :raises: FileNotFoundError
    :raises: TypeError
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError

    if not isinstance(pdf_path, str):
        raise ValueError("Invalid type for pdf_path.")

    if not pdf_path.endswith(".pdf"):
        raise ValueError(f"{pdf_path} is not a pdf file. ")

    base_dir = common.get_shared_directory()
    if not pdf_path.startswith(base_dir):
        raise ValueError(f"{pdf_path} must be under {base_dir}")

    pdf_path = pdf_path[:-4]
    naked = pdf_path[len(base_dir):]

    if naked.startswith("/"):
        naked = naked[1:]

    tokens = naked.split("/")
    collection_name = tokens.pop(0)
    subdir = '/'.join(tokens)

    holding_dir = None

    if synthetic_dir_type == _SyntheticDir.IMAGES:
        holding_dir = "images"
    elif synthetic_dir_type == _SyntheticDir.MARKDOWN:
        holding_dir = "markdowns"

    assert holding_dir

    img_dir = os.path.join(
        base_dir, collection_name,
        "synthetic", holding_dir, subdir
    )

    return img_dir
