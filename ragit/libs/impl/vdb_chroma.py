"""Exports the Milvus vector db."""

import uuid

import chromadb

import ragit.libs.impl.vdb_abstract_base as abstract_vector_db
import ragit.libs.impl.embeddings_retriever as embeddings_retriever


class ChromaVectorDb(abstract_vector_db.AbstractVectorDb):
    """Encapsulates a vector database using chroma."""

    def __init__(self, fullpath, collection_name, dimension):
        """Initializer..

        :param str fullpath: The full path to the file holding the vector db.
        :param str collection_name: The name of the collection.
        :param int dimension: The length of the embeddings vector.
        """
        super().__init__(fullpath, collection_name, dimension)

        assert self.get_fullpath() == fullpath
        assert self.get_collection_name() == collection_name
        assert self.get_dimension() == dimension

        fullpath = self.get_fullpath()

        client_settings = chromadb.config.Settings(
            anonymized_telemetry=False
        )

        self._chroma_client = chromadb.PersistentClient(
            path=fullpath,
            settings=client_settings
        )

    def close(self):
        """Closes the milvus vector db."""
        print("close is not implemented..")

    def insert(self, chunks, embeddings, sources, pages):
        """Inserts a list of chunks and their embeddings into the db.

        Subsequent calls to this method append new chunks to and existing
        collection, effectively incrementally updating the database.

        :param list[str] chunks: The list of chunks to insert.
        :param list[ list[float]] embeddings: The list of the embeddings.
        :param list[str] sources: The full paths to the documents.
        :param list[int] pages: The pages holding the chunks.
        """
        assert self._chroma_client, "Chroma Vector Collection is not open."
        assert len(chunks) == len(embeddings)
        collection = self._chroma_client.get_or_create_collection(
            self.get_collection_name(),
            metadata={"hnsw:space": "cosine"}
        )
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        sources = [source or "n/a" for source in sources]
        pages = [page or 0 for page in pages]

        meta_data = [
            {"source": source, "page": page}
            for source, page in zip(sources, pages)
        ]

        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=meta_data
        )

    def get_number_of_records(self):
        """Returns the number of records in the collection.

        :return: The number of records in the collection.
        :rtype: int
        """
        assert self._chroma_client, "Chroma Vector Collection is not open."

        collection = self._chroma_client.get_or_create_collection(
            self.get_collection_name()
        )
        count = collection.count()
        return count

    def query(self, query, k=3):
        """Queries the vector database for matching chunks.

        :param str query: The string to find matching chunks.
        :param int k: The number of matches to return.
        """
        assert self._chroma_client, "Chroma Vector Collection is not open."

        query = query + " (do not consider upper lower case in the embeddings)"
        query_embedding = embeddings_retriever.get_embeddings(query)
        collection = self._chroma_client.get_or_create_collection(
            self.get_collection_name()
        )

        search_results = collection.query(
            query_embeddings=query_embedding,
            n_results=k
        )

        matches = []
        for txt, distance, meta in zip(search_results["documents"][0],
                                 search_results["distances"][0],
                                 search_results["metadatas"][0]
                                 ):
            source = meta.get("source")
            page = meta.get("page")
            matches.append((txt, 1. - distance, source, page))

        return matches
