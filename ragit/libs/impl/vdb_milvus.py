"""Exports the Milvus vector db."""

import pymilvus

import ragit.libs.impl.vdb_abstract_base as abstract_vector_db
import ragit.libs.impl.embeddings_retriever as embeddings_retriever


class MilvusVectorDb(abstract_vector_db.AbstractVectorDb):
    """Encapsulates a vector database using milvus."""

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

        uri = self.get_fullpath()
        self._milvus_client = pymilvus.MilvusClient(uri=uri)
        if not self._milvus_client.has_collection(self.get_collection_name()):
            self._milvus_client.create_collection(
                collection_name=self.get_collection_name(),
                dimension=self.get_dimension(),
                metric_type="IP",
                consistency_level="Strong",
            )

    def close(self):
        """Closes the milvus vector db."""
        if self._milvus_client:
            self._milvus_client.close()

    def insert(self, chunks, embeddings, sources, pages):
        """Inserts a list of chunks and their embeddings into the db.

        Subsequent calls to this method append new chunks to and existing
        collection, effectively incrementally updating the database.

        :param list[str] chunks: The list of chunks to insert.
        :param list[list[float]] embeddings: The list of the embeddings.
        :param list[str] sources: The full paths to the documents.
        :param list[int] pages: The pages holding the chunks.
        """
        assert self._milvus_client, "Milvus Vector Collection is not open."
        data = []
        count = 0
        for chunk, embedding, source, page in zip(chunks, embeddings,
                                                  sources, pages):
            data.append(
                {
                    "id": count,
                    "vector": embedding,
                    "text": chunk,
                    "source": source or "n/a",
                    "page": page or 0
                }
            )
            count += 1
        self._milvus_client.insert(
            collection_name=self.get_collection_name(),
            data=data
        )

    def get_number_of_records(self):
        """Returns the number of records in the collection.

        :return: The number of records in the collection.
        :rtype: int
        """
        assert self._milvus_client, "Milvus Vector Collection is not open."
        res = self._milvus_client.query(
            collection_name=self.get_collection_name(),
            output_fields=["count(*)"]
        )
        counter = res[0]["count(*)"]
        return counter

    def query(self, query, k=3):
        """Queries the vector database for matching chunks.

        :param str query: The string to find matching chunks.
        :param int k: The number of matches to return.
        """
        assert self._milvus_client, "Milvus Vector Collection is not open."
        query = query + " (do not consider upper lower case in the embeddings)"
        e = embeddings_retriever.get_embeddings(query)
        search_res = self._milvus_client.search(
            collection_name=self.get_collection_name(),
            data=[e],
            limit=k,
            search_params={"metric_type": "IP", "params": {}},
            output_fields=["text", "source", "page"],
        )

        matches = []

        for res in search_res[0]:
            matches.append(
                (
                    res["entity"]["text"],
                    res["distance"],
                    res["entity"]["source"],
                    res["entity"]["page"]
                )
            )

        return matches
