"""Exposes function to gather the metrics of a collection."""

import os

import ragit.libs.common as common
import ragit.libs.impl.chunks_mgr as chunks_mgr
import ragit.libs.impl.pdf_preprocessor as pdf_processor


@common.handle_exceptions
def get_total_pdf_files(collection_name):
    """Counts the total number of PDF files in a given collection directory.

    :param str collection_name: Name of the collection to search within.

    :returns: Total number of PDF files found.
    :rtype: int
    """
    directory = os.path.join(common.get_shared_directory(), collection_name)
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".pdf"):
                fullpath = os.path.join(root, file)
                pdf_files.append(fullpath)
    return len(pdf_files)


@common.handle_exceptions
def get_pdf_files_missing_markdowns(collection_name):
    """Discovers the pdf with missing markdowns.

    :param str collection_name: The name of the collection to check for PDFs
    missing images.

    :returns: The PDF files without markdowns.
    :rtype: list[str]
    """
    directory = os.path.join(common.get_shared_directory(), collection_name)
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".pdf"):
                fullpath = os.path.join(root, file)
                if pdf_processor.needs_to_create_markdowns(fullpath):
                    pdf_files.append(fullpath)
    return pdf_files


@common.handle_exceptions
def get_total_documents(directory):
    """Returns the total number of available documents in the filesystem.

    :param str directory: The directory containing the documents.

    :return: The total number of available documents in the filesystem.
    :rtype: int

    :raises MyGenAIException
    """
    all_docs = list(chunks_mgr.find_all_documents(directory))
    return len(all_docs)


@common.handle_exceptions
def get_total_documents_in_db(db):
    """Returns the total number of available documents in the db.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of available documents in the db.
    :rtype: int

    :raises MyGenAIException
    """
    docs = list(chunks_mgr.get_already_chunked_files(db))
    return len(docs)


@common.handle_exceptions
def get_total_chunks(db):
    """Returns the total number of available chunks in the db.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of available chunks in the db.
    :rtype: int

    :raises MyGenAIException
    """
    for row in db.execute_query(_SQL_COUNT_CHUNKS):
        return row[0]


@common.handle_exceptions
def get_chunks_with_embeddings(db):
    """Returns the total number of chunks in the db with embeddings.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of chunks in the db with embeddings.
    :rtype: int

    :raises MyGenAIException
    """
    chunk_ids = list(chunks_mgr.find_chunks_with_embeddings(db))
    return len(chunk_ids)


@common.handle_exceptions
def get_chunks_without_embeddings(db):
    """Returns the total number of chunks in the db without embeddings.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of chunks in the db without embeddings.
    :rtype: int

    :raises MyGenAIException
    """
    chunk_ids = list(chunks_mgr.find_chunks_missing_embeddings(db))
    return len(chunk_ids)


@common.handle_exceptions
def get_chunks_inserted_in_vectordb(db):
    """Returns the total number of chunks in the vectordb.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of  chunks in the vectordb.
    :rtype: int

    :raises MyGenAIException
    """
    for row in db.execute_query(_SQL_COUNT_CHUNKS_IN_VECTOR_DB):
        return row[0]


@common.handle_exceptions
def get_chunks_to_insert_to_vector_db(db):
    """Returns the total number of chunks to insert to the vectordb.

    :param dbutil.SimpleSQL db: The database wrapper to use.

    :returns: The total number of  chunks  to insert to the vectordb.
    :rtype: int

    :raises MyGenAIException
    """
    chunk_ids = list(chunks_mgr.get_chunk_ids_to_insert_to_vector_db(db))
    return len(chunk_ids)


# Whatever follows this line is private to the module and should not be
# used from the outside.

_SQL_COUNT_CHUNKS = """SELECT count(*) FROM chunks"""

_SQL_COUNT_CHUNKS_IN_VECTOR_DB = """
SELECT count(*) from chunks where stored_in_vdb=1
"""
