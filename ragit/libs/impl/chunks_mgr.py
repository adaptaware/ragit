"""Document Manager (Manages the document storage)."""

import datetime
import json
import os
import re

import ragit.libs.common as common
import ragit.libs.sanitizer as sanitizer
import ragit.libs.dbutil as dbutil
import ragit.libs.impl.embeddings_retriever as embeddings_retriever
import ragit.libs.impl.splitter as splitter
import ragit.libs.impl.embeddings_info as embeddings_info


@common.handle_exceptions
def insert_chunks_to_db(db, directory, max_count=None, verbose=False):
    """Inserts the chunks to the database.

    :param dbutil.SimpleSQL db: The database wrapper to use.
    :param directory: The directory where the files exist.
    :param int max_count: The maximum number of chunks to save; by
    default None will save all the available chunks.
    :param bool verbose: If true it will print out messages.

    :returns: The number of chunks saved to the database.
    """
    if verbose:
        if max_count is None:
            print("Will insert all available chunks to the database.")
        else:
            print(f"Insert at max {max_count} chunks to the database.")
    counter = 0
    for fullpath in find_documents_to_chunk(db, directory):
        fullpath = sanitizer.ensure_sanitized(fullpath)
        try:
            counter += save_chunks_to_db(db, fullpath)
        except Exception as ex:
            print(ex)
            continue
        if verbose:
            print(datetime.datetime.now(), counter, fullpath)
        if max_count and counter >= max_count:
            break
    return counter


@common.handle_exceptions
def insert_embeddings_to_db(db, max_count=None, verbose=False):
    """Insert embeddings to the database.

    :param dbutil.SimpleSQL db: The database wrapper to use.
    :param int max_count: The maximum number of embeddings to save; by
    default None will save all the available embeddings.
    :param bool verbose: If true it will print out messages.

    :return: The number of embeddings inserted.
    :rtype: int
    """
    if verbose:
        if max_count is None:
            print("Will insert all available embeddings to the database.")
        else:
            print(f"Insert at max {max_count} embeddings to the database.")
    counter = 0
    for chunk_id in find_chunks_missing_embeddings(db):
        counter += 1
        if max_count is not None and counter > max_count:
            break
        save_embeddings(db, chunk_id)
        if verbose:
            print(f"Embeddings count: {counter}")
    return counter


@common.handle_exceptions
def get_already_chunked_files(db):
    """Returns a list with the files that are already chunked and stored in db.

    :return: A list with the files that are already chunked.
    :rtype: list[str]
    """
    fullpaths = []
    for row in db.execute_query(_SQL_SELECT_FULLPATHS):
        fullpaths.append(row[0])
    return fullpaths


@common.handle_exceptions
def save_embeddings(db, chunk_id):
    """Retrieves and saves the embeddings for a given chunk.

    The chunk must already exist in the database with the given id.

    :param SimpleSQL db: The database wrapper to use.
    :param int chunk_id: The id of the chunk to save its embeddings.
    """
    # Get the chunk from the database.
    sql = _SQL_SELECT_CHUNK.format(chunk_id=chunk_id)
    chunk = None
    for row in db.execute_query(sql):
        chunk = row[0]
    assert chunk is not None
    # Retrieve the embeddings and store them in the database.
    embeddings = embeddings_retriever.get_embeddings(chunk)
    sql = _SQL_UPDATE_EMBEDDINGS.format(
        embeddings=json.dumps(embeddings),
        chunk_id=chunk_id
    )
    db.execute_non_query(sql)


@common.handle_exceptions
def find_chunks_missing_embeddings(db):
    """Finds the chunks that are missing embeddings.

    Since the embeddings can be calculated any time, it is quite possible
    that we will have chunks in the database that will have NULL as
    embeddings just because they were not calculated yet.

    This function is finding these chunks and yields their chunk_id(s).

    :param SimpleSQL db: The database wrapper to use.

    :yield: The chunk_id of the chunks that are missing embeddings.
    """
    for row in db.execute_query(_SQL_FIND_MISSING_EMBEDDINGS):
        yield row[0]


@common.handle_exceptions
def find_chunks_with_embeddings(db):
    """Finds the chunks with embeddings.

    :param SimpleSQL db: The database wrapper to use.

    :yield: The chunk_id of the chunks with embeddings.
    """
    for row in db.execute_query(_SQL_FIND_ASSIGNED_EMBEDDINGS):
        yield row[0]


@common.handle_exceptions
def get_chunk_ids_to_insert_to_vector_db(db):
    """Finds the chunks with embeddings that are not in the vector db yet.

    Yields the chunk_id(s) that are ready to be inserted into the
    vector database, meaning that they have stored their embeddings but
    were not stored in the vector db yet.

    :param SimpleSQL db: The database wrapper to use.

    :yield: The chunk_id of the chunks with embeddings.
    """
    for row in db.execute_query(_SQL_FIND_ASSIGNED_EMBEDDINGS_NOT_IN_VECTOR_DB):
        yield row[0]


def set_vectorized(db, chunk_ids):
    """Updates the psql database setting the stored_in_vdb flag.

    Once this function will be called all the passed in chunk_ids will
    be marked as already been part of the vector db and they will not
    be reconsidered in a subsequent call of vector update.

    :param SimpleSQL db: The database wrapper to use.

    :param list [int] chunk_ids: The list of the chunk ids to update.
    """
    ids = ', '.join([str(chunk_id) for chunk_id in chunk_ids])
    sql = _SQL_UPDATE_STORED_IN_VDB.format(chunk_ids=ids)
    db.execute_non_query(sql)


@common.handle_exceptions
def load_embeddings(db, chunk_id):
    """Returns the embeddings for the passed in chunk_id.

    This function retrieves the embeddings for a given chunk identifier from
    the database.  It also extracts additional metadata including the source
    and page number associated with the chunk.

    :param SimpleSQL db: The database wrapper to use.
    :param int chunk_id: The chunk id to fetch.

    :return: An instance of the EmbeddingsInfo class holding the following:

    - chunk (str): The text associated with the specified chunk ID.
    - embeddings (list [float]): The embeddings of the chunk.
    - source (str or None): The source from where the chunk was derived.
    - page (int or None): The page number associated with the chunk.

    :rtype: EmbeddingsInfo
    """
    sql = _SQL_SELECT_EMBEDDINGS.format(chunk_id=chunk_id)
    for row in db.execute_query(sql):
        chunk = row[0]
        embeddings = row[1]
        metadata = row[2]
        source = metadata.get("source")
        page = metadata.get("page")
        return embeddings_info.EmbeddingsInfo(chunk, embeddings, source, page)


@common.handle_exceptions
def save_chunks_to_db(db, fullpath, chunk_size=500, chunk_overlap=40):
    """Splits the passed in document and saves the chunks into the database.

    :param SimpleSQL db: The database wrapper to use.
    :param str fullpath: The fullpath to the document.
    :param int chunk_size: The chunk size to use.
    :param int chunk_overlap: The chunk overlap The overlap to use.

    :returns: The number of chunks saved.
    :rtype: int
    """
    assert os.path.isfile(fullpath)
    chunk_index = 0
    for chunk, metadata in splitter.split(fullpath, chunk_size, chunk_overlap):
        try:
            chunk = chunk.replace('"', "'")
            chunk = chunk.replace("'", "''")
            chunk = re.sub(
                r'[^\w\s\d\-_`*#+~\[\]\(\)\|\.\:\!\?\$\%\^\&\*\-\+\=]', '',
                chunk)
            chunk_index += 1

            # Adds metadata.
            if isinstance(metadata, dict):
                if "source" not in metadata:
                    metadata["source"] = fullpath

                if "chunk_index" not in metadata:
                    metadata["chunk_index"] = chunk_index

                if "chunk_size" not in metadata:
                    metadata["chunk_size"] = chunk_size

                if "chunk_overlap" not in metadata:
                    metadata["chunk_overlap"] = chunk_overlap

            meta = json.dumps(metadata)
            sql = _SQL_INSERT_CHUNK.format(
                filepath=fullpath,
                chunk_index=chunk_index,
                txt=chunk,
                meta=meta
            )
            db.execute_non_query(sql)
        except Exception as ex:
            print(ex)
    return chunk_index


@common.handle_exceptions
def find_all_documents(directory):
    """Discovers all the documents under the given directory.

    :param str directory: The directory containing the documents.

    :return: A list of strings holding the full paths of the documents.
    :rtype: list[str]
    """
    extensions = splitter.get_supported_doc_extensions()
    matches = []
    for root, _, files in os.walk(directory):
        for file in files:
            for extension in extensions:
                if file.endswith(extension):
                    matches.append(os.path.join(root, file))
    return matches


@common.handle_exceptions
def find_documents_to_chunk(db, directory):
    """Discovers all the documents under the given directory to be chunked.

    Discovers all the files that can be chunked and returns only those that
    are not already in the database.

    :param SimpleSQL db: The database wrapper to use.
    :param str directory: The directory containing the documents.

    :return: Only documents that are not already chunked will be returned.
    :rtype: list[str]
    """
    all_filepaths = set(find_all_documents(directory))
    already_chunked = set(get_already_chunked_files(db))
    diff = all_filepaths - already_chunked
    return list(diff)


# Whatever follows this line is private to the module and should not be
# used from the outside.

_SQL_SELECT_FULLPATHS = """
sELECT fullpath FROM chunks GROUP BY fullpath
"""

_SQL_INSERT_CHUNK = """
INSERT INTO chunks (fullpath, chunk_index, chunk, metadata)
VALUES ('{filepath}', {chunk_index}, '{txt}', '{meta}')
"""

_SQL_SELECT_CHUNK = """
SELECT chunk FROM chunks WHERE chunk_id={chunk_id}
"""

_SQL_SELECT_EMBEDDINGS = """
SELECT chunk, embeddings, metadata FROM chunks WHERE chunk_id={chunk_id}
"""

_SQL_UPDATE_EMBEDDINGS = """
UPDATE chunks SET embeddings='{embeddings}' WHERE chunk_id={chunk_id}
"""

_SQL_FIND_MISSING_EMBEDDINGS = """
SELECT chunk_id FROM chunks WHERE embeddings IS NULL
"""

_SQL_FIND_ASSIGNED_EMBEDDINGS = """
SELECT chunk_id FROM chunks WHERE embeddings IS NOT NULL
"""

_SQL_FIND_ASSIGNED_EMBEDDINGS_NOT_IN_VECTOR_DB = """
SELECT chunk_id FROM chunks WHERE embeddings IS NOT NULL and stored_in_vdb=0
"""

_SQL_UPDATE_STORED_IN_VDB = """
UPDATE chunks
SET stored_in_vdb = 1
WHERE chunk_id IN ( {chunk_ids} );
"""
