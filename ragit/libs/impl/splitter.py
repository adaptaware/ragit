"""Exposes a function to allow splitting a document in chunks."""

import os

import langchain.text_splitter as text_splitter_lib
import langchain_community.document_loaders as doc_loaders

from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)

import ragit.libs.impl.markdown_splitter as markdown_splitter
import ragit.libs.impl.markdown_parser as markdown_parser

def get_supported_doc_extensions():
    """Returns the list of supported document extensions.

    :return: The list of supported document extensions.
    :rtype: list
    """
    return _SUPPORTED_DOCS.copy()


def split(fullpath, chunk_size=500, chunk_overlap=40):
    """Breaks down the passed in document to chunks.

    :param str fullpath: The fullpath to the document.
    :param int chunk_size: The chunk size to use.
    :param int chunk_overlap: The chunk overlap The overlap to use.

    :yields: A tuple of the text and the metadata for each chunk.
    """
    fullpath = fullpath.strip()
    if fullpath.endswith("docx"):
        doc = _DocxDocument(fullpath, chunk_size, chunk_overlap)
    elif fullpath.endswith("md"):
        doc = _MDDocument(fullpath, chunk_size, chunk_overlap)
    elif fullpath.endswith("py"):
        doc = _PythonDocument(fullpath, chunk_size, chunk_overlap)
    else:
        raise NotImplementedError

    return doc.get_chunks()


# Whatever follows this line is private to the module and should not be
# used from the outside.

_SUPPORTED_DOCS = ["docx", "md", "py"]


class _DocxDocument:
    """Holds the information of a PDF document.

    :ivar str _fullpath: The full path to the PDF file.
    :ivar _chunks: The text chunks from the document split.
    """

    _fullpath = None
    _chunks = None

    def __init__(self, fullpath, chunk_size, chunk_overlap):
        """Initializes a new instance.

        :param str fullpath: The full path to the PDF document
        """
        assert fullpath.endswith("docx"), "not a docx file"
        assert os.path.isfile(fullpath), f'{fullpath} does not exist'
        self._fullpath = fullpath

        text_splitter = text_splitter_lib.RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        docx = doc_loaders.Docx2txtLoader(self._fullpath)
        pages = docx.load()
        self._chunks = text_splitter.split_documents(pages)

    def get_chunks(self):
        """Iterates through the available chunks.

        :yields: The chunks as strings.
        """
        for chunk in self._chunks:
            yield chunk.page_content, chunk.metadata


class _MDDocument:
    """Holds the information of a markdown document.

    :ivar str _fullpath: The full path to the PDF file.
    :ivar _chunks: The text chunks from the document split.
    """

    _fullpath = None
    _chunk_contents = None
    _chunk_metadata = None

    def __init__(self, fullpath, chunk_size, chunk_overlap):
        """Initializes a new instance.

        :param str fullpath: The full path to the PDF document
        """
        assert fullpath.endswith("md"), "not a md file"
        assert os.path.isfile(fullpath), f'{fullpath} does not exist'
        self._fullpath = fullpath

        self._chunk_contents = []
        self._chunk_metadata = []

        for node in markdown_parser.iter_markdown(fullpath):
            headers = node.get_headers()
            txt = node.get_inner_text()
            node_type = node.get_section_type()
            metadata = {"fullpath": self._fullpath, "page": 'n/a'}

            if node_type == markdown_parser.SectionType.TABLE:
                self._chunk_contents.append(txt)
                self._chunk_metadata.append(metadata)
            else:
                for chunk in markdown_splitter.get_chunks(txt, chunk_size=500):
                    self._chunk_contents.append(headers + chunk)
                    metadata = {"fullpath": self._fullpath, "page": 'n/a'}
                    self._chunk_metadata.append(metadata)

    def get_chunks(self):
        """Iterates through the available chunks.

        :yields: The chunks as strings.
        """
        for chunk, meta in zip(self._chunk_contents, self._chunk_metadata):
            yield chunk, meta


class _PythonDocument:
    """Holds the information of a python source file.

    :ivar str _fullpath: The full path to the python file.
    :ivar _chunks: The text chunks from the document split.
    """

    _fullpath = None
    _chunks = None

    def __init__(self, fullpath, chunk_size, chunk_overlap):
        """Initializes a new instance.

        :param str fullpath: The full path to the python document
        """
        assert fullpath.endswith("py"), "not a python file"
        assert os.path.isfile(fullpath), f'{fullpath} does not exist'
        self._fullpath = fullpath

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        with open(fullpath) as fin:
            python_code = fin.read()

        python_splits = python_splitter.create_documents([python_code])

        self._chunks = python_splits

    def get_chunks(self):
        """Iterates through the available chunks.

        :yields: The chunks as strings.
        """
        for chunk in self._chunks:
            yield chunk.page_content, chunk.metadata
