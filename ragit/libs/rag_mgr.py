"""RagManager is a wrapper for the data handling for RAG creation and update."""

import dataclasses
import datetime
import logging
import os

import ragit.libs.common as common
import ragit.libs.impl.chunks_mgr as chunks_mgr
import ragit.libs.impl.metrics as metrics
import ragit.libs.impl.pdf_preprocessor as pp
import ragit.libs.impl.query_executor as query_executor
import ragit.libs.impl.vdb_factory as vector_db

# Aliases.
logger = logging.getLogger(__name__)


class RagManager:
    """Encapsulates the lower level details for the creation of RAG.

    Exposes the functionality to:

    - Insert chunks of texts into the database.
    - To save the embeddings for each chunk and store them in the database.
    - To update the vector database for each chunk and its embedding.
    - Query the LLM for a question.

    The data for each RAG collection should be placed under a subdirectory
    inside the shared directory following the same structure outlined above.

    Under a development/ local machine this directory is mapped from
    the host to the Vagrant guest while when running the service directly
    on the host machine the shared directory must be under the home directory
    and called ragit-data.

    Each RAG collection is managed by a specific directory under the ragit-data
    directory with the same name as the RAG collection having the following
    structure:

    - **documents**: Source files (PDF, DOCX, MD, etc.) for RAG creation.

    - **vectordb: Stores the vector database.

    This class should be used as the high-level abstraction of all the
    lower level details that are implemented under the impl directory which
    can be changed at any time without having any dependencies to other
    clients except this class.

    :ivar str _rag_name: The name of the RAG collection.

    :ivar str _base_dir: The root directory holding the data for the collection.

    :ivar str _documents_dir: The root directory holding the documents for
    the collection.

    :ivar str _vectordb_fullpath: The full path to the vectordb database file.

    :cvar str _SHARED_DIR: The shared directory for documents.

    :cvar str _VECTOR_COLLECTION_NAME: The name of the collection inside the
    vector database.
    """
    _SHARED_DIR = "ragit-data"
    _VECTOR_COLLECTION_NAME = "chunk_embeddings"

    _rag_name = None
    _base_dir = None
    _documents_dir = None
    _vectordb_fullpath = None

    def __init__(self, rag_name):
        """Initializer.

        :param str rag_name: The name of the RAG collection.

        :raises: NotADirectoryError, ValueError
        """
        self._rag_name = rag_name
        self._base_dir = os.path.join(
            common.get_home_dir(),
            self._SHARED_DIR,
            self._rag_name
        )
        if not os.path.isdir(self._base_dir):
            logger.error("There is no RAG collection directory: %s",
                         self._base_dir)
            raise NotADirectoryError(f"Not a directory {self._base_dir}")

        common.create_directory_if_not_exists(self._base_dir)

        homedir = common.get_home_dir()

        # Assign the documents directory.
        directory = os.path.join(homedir, self._base_dir, "documents")
        common.create_directory_if_not_exists(directory)
        self._documents_dir = directory

        # Assign the vectordb directory.
        directory = os.path.join(homedir, self._base_dir, "vectordb")
        common.create_directory_if_not_exists(directory)

        vector_db_provider = common.get_vector_db_provider()

        if vector_db_provider == common.VectorDbProviderEnum.MILVUS:
            self._vectordb_fullpath = os.path.join(
                directory, f"{rag_name}-milvus-vector.db"
            )
        elif vector_db_provider == common.VectorDbProviderEnum.CHROMA:
            self._vectordb_fullpath = os.path.join(
                directory, f"{rag_name}-chroma-vector.db"
            )
        else:
            raise ValueError("Unsupported vector-db provider.")

        query_executor.initialize(
            self._vectordb_fullpath,
            self._VECTOR_COLLECTION_NAME
        )

    def close(self):
        """Closes all open connections."""
        query_executor.close()
        self._rag_name = None
        self._base_dir = None
        self._documents_dir = None
        self._vectordb_fullpath = None

    def get_rag_collection_name(self):
        """Returns the collection name.

        :returns: The collection name.
        :rtype: str
        """
        return self._rag_name

    def query(self, question, k=None, temperature=None, max_tokens=None):
        """Uses the RAG collection to enhance the LLM to answer the question.

        :param str question: The question to answer.
        :param int k: The number of vector matches to use.
        :param float temperature: The temperature to use for the query.
        :param float max_tokens: The max_tokens to use for the query.

        :return: The LLM generated answer as an instance of the QueryResponse.
        :rtype: QueryResponse

        :raises MyGenAIException
        """
        return query_executor.query(question, k, temperature, max_tokens)

    def get_base_dir(self):
        """Returns the base directory for the RAG collection.

        :return: The base directory for the RAG collection.
        :rtype: str
        """
        return self._base_dir

    def get_documents_dir(self):
        """Returns the directory containing the documents to use for RAG.

        :return: The directory containing the documents to use for RAG.
        :rtype: str
        """
        return self._documents_dir

    def get_vector_db_fullpath(self):
        """Returns the full path to the vector database for the given RAG.

        :return: The full path to the vector database for the given RAG.
        :rtype: str
        """
        return self._vectordb_fullpath

    @classmethod
    def get_all_rag_collections(cls):
        """Returns a list with all the available RAG collection names.

        Be design all the collection must be located under the share directory
        and contain a subdirectory called documents holding the corresponding
        documents that can be in any nested directory. This function returns
        all the available collection names.

        :return: A list with the names of all the available collection names.
        :rtype: list [str]
        """
        base_dir = os.path.join(common.get_home_dir(), cls._SHARED_DIR)
        rag_collections = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                rag_collections.append(item)
        return rag_collections

    def get_metrics(self, db):
        """Finds the metrics for the collection.

        :returns: The metrics for collection.
        :rtype: RagMetrics
        """
        name = self._rag_name
        full_path = self._documents_dir
        total_documents = metrics.get_total_documents(self._documents_dir)
        total_documents_in_db = metrics.get_total_documents_in_db(db)
        total_chunks = metrics.get_total_chunks(db)
        with_embeddings = metrics.get_chunks_with_embeddings(db)
        without_embeddings = metrics.get_chunks_without_embeddings(db)
        inserted_to_vectordb = metrics.get_chunks_inserted_in_vectordb(db)
        to_insert_to_vector_db = metrics.get_chunks_to_insert_to_vector_db(db)
        total_pdf_files = metrics.get_total_pdf_files(name)
        pdf_missing_markdowns = len(
            metrics.get_pdf_files_missing_markdowns(name)
        )

        return RagMetrics(
            name=name,
            full_path=full_path,
            total_documents=total_documents,
            total_documents_in_db=total_documents_in_db,
            total_chunks=total_chunks,
            with_embeddings=with_embeddings,
            without_embeddings=without_embeddings,
            inserted_to_vectordb=inserted_to_vectordb,
            to_insert_to_vector_db=to_insert_to_vector_db,
            total_pdf_files=total_pdf_files,
            pdf_missing_markdowns=pdf_missing_markdowns
        )

    def create_missing_markdowns(self):
        """Creates the missing markdowns.

        Applies to images that correspond to pdf(s) but still do not have been
        converted to markdowns.
        """
        paths = metrics.get_pdf_files_missing_markdowns(self._rag_name)
        total = len(paths)

        for count, pdf_path in enumerate(paths,start=1):
            print(f"{count}/{total}: Processing {pdf_path}")
            t1 = datetime.datetime.now()
            pp.create_markdowns_from_pdf(pdf_path)
            t2 = datetime.datetime.now()
            duration = (t2 - t1).total_seconds()
            print(f" {count}/{total}  {pdf_path} took {duration:.2f} seconds")

    def insert_chunks_to_db(self, db, max_count=None, verbose=False):
        """Inserts the chunks to the database.

        :param dbutil.SimpleSQL db: The database wrapper to use.
        :param int max_count: The maximum number of chunks to save; by
        default None will save all the available chunks.
        :param bool verbose: If true it will print out messages.

        :returns: The number of chunks saved to the database.
        :rtype: int

        :raises MyGenAIException
        """
        count = chunks_mgr.insert_chunks_to_db(
            db=db,
            directory=self.get_documents_dir(),
            max_count=max_count,
            verbose=verbose
        )

        return count

    def insert_embeddings_to_db(self, db, max_count=None, verbose=False):
        """Insert embeddings to the database.

        :param dbutil.SimpleSQL db: The database wrapper to use.
        :param int max_count: The maximum number of embeddings to save; by
        default None will save all the available embeddings.
        :param bool verbose: If true it will print out messages.

        :return: The number of embeddings inserted.
        :rtype: int

        :raises MyGenAIException
        """
        count = chunks_mgr.insert_embeddings_to_db(db, max_count, verbose)
        return count

    def update_vector_db(
            self, db, max_count=None,
            dimension=1536, batch_size=2000, verbose=False):
        """Updates the vector db.

        :param dbutil.SimpleSQL db: The database wrapper to use.

        :param int | None max_count: The maximum number of embeddings to
        save; if None then all the un-inserted chunks will be inserted.

        :param int dimension: The dimensions of the embeddings array.

        :param int batch_size: The size of the batch that is stored to
        the vector db each time (to avoid consuming the whole memory).

        :param bool verbose: If True then informative messages will be printed.

        :returns: The number of chunks that were inserted to the vector db.
        :rtype: int

        :raises MyGenAIException
        """
        if verbose:
            print("updating the vector db.")
        vdb = vector_db.get_vector_db(
            fullpath=self.get_vector_db_fullpath(),
            collection_name=self._VECTOR_COLLECTION_NAME,
            dimension=dimension
        )

        total_inserted_counter = 0
        chunks = []
        embeddings = []
        sources = []
        pages = []
        vectorized_chunk_ids = []

        for chunk_id in chunks_mgr.get_chunk_ids_to_insert_to_vector_db(db):
            if verbose:
                print(chunk_id, len(embeddings))
            embeddings_info = chunks_mgr.load_embeddings(db, chunk_id)
            chunks.append(embeddings_info.get_chunk())
            embeddings.append(embeddings_info.get_embeddings())
            sources.append(embeddings_info.get_source())
            pages.append(embeddings_info.get_page())
            vectorized_chunk_ids.append(chunk_id)
            if max_count is not None and len(embeddings) >= max_count:
                break
            if len(embeddings) > batch_size:
                vdb.insert(chunks, embeddings, sources, pages)
                total_inserted_counter += len(embeddings)
                chunks_mgr.set_vectorized(db, vectorized_chunk_ids)
                sources = []
                chunks = []
                embeddings = []
                vectorized_chunk_ids = []

        # Insert leftovers if needed.
        if len(embeddings):
            vdb.insert(chunks, embeddings, sources, pages)
            total_inserted_counter += len(embeddings)
            chunks_mgr.set_vectorized(db, vectorized_chunk_ids)

        if verbose:
            print(f"Totally inserted records: {total_inserted_counter}")

        return total_inserted_counter


@dataclasses.dataclass(frozen=True)
class RagMetrics:
    """Represents the metrics of a collection of documents.

    str name: The name of the collection.
    str full_path: The full path to the collection.
    int total_documents: The total number of available documents.
    int total_documents_in_db: The total number of available documents in db.
    int total_chunks: The total number of existing chunks.
    int with_embeddings: The number of chunks with embeddings.
    int without_embeddings: The number of chunks without embeddings.
    int inserted_to_vectordb: The number of chunks in the vector db.
    int to_insert_to_vector_db: The chunks to insert into the vector db.
    """

    name: str
    full_path: str
    total_documents: int
    total_documents_in_db: int
    total_chunks: int
    with_embeddings: int
    without_embeddings: int
    inserted_to_vectordb: int
    to_insert_to_vector_db: int
    total_pdf_files: int
    pdf_missing_markdowns: int
