"""Defines the abstract base class for a vectordb."""

import abc


class AbstractVectorDb(abc.ABC):
    """The abstract class for a vector db.

    Serves as the abstract base class for different implementations of
    vector databases that use different third party providers.

    :ivar str __fullpath: The full path to the file holding the vector db.
    :ivar str __collection_name: The name of the collection.
    :ivar int __dimension: The length of the embeddings vector.
    """

    def __init__(self, fullpath, collection_name, dimension=1536):
        """Initializes the instance.

        :param str fullpath: The full path to the file holding the vector db.
        :param str collection_name: The name of the collection.
        :param int dimension: The length of the embeddings vector.
        """
        self.__fullpath = f'{fullpath}'
        self.__collection_name = collection_name
        self.__dimension = dimension

    def __repr__(self):
        """Returns a string representation of this instance.

        :return: A string representation of this instance.
        :rtype: str
        """
        return f"{self.get_fullpath()}, " \
               f"{self.get_collection_name()}: " \
               f"{self.get_dimension()}"

    def get_fullpath(self):
        """Returns the full path to the file that holds the vectordb.

        :returns: The full path to the file that holds the vectordb.
        :rtype: str
        """
        return self.__fullpath

    def get_collection_name(self):
        """Returns the collection name used in the vectordb.

        :returns: The collection name used in the vectordb.
        :rtype: str
        """
        return self.__collection_name

    def get_dimension(self):
        """Returns the dimension of the embeddings stored in the vectordb.

        :returns: The dimension of the embeddings stored in the vectordb.
        :rtype: int
        """
        return self.__dimension

    @abc.abstractmethod
    def insert(self, chunks, embeddings, sources, pages):
        """Inserts a list of chunks and their embeddings into the db.

        Subsequent calls to this method append new chunks to and existing
        collection, effectively incrementally updating the database.

        :param list[str] chunks: The list of chunks to insert.
        :param list[ list[float]] embeddings: The list of the embeddings.
        :param list[str] sources: The full paths to the documents.
        :param list[int] pages: The pages holding the chunks.
        """

    @abc.abstractmethod
    def get_number_of_records(self):
        """Returns the number of records in the collection.

        :return: The number of records in the collection.
        :rtype: int
        """

    @abc.abstractmethod
    def query(self, query, k=3):
        """Queries the vector database for matching chunks.

        :param str query: The string to find matching chunks.
        :param int k: The number of matches to return.
        """

    @abc.abstractmethod
    def close(self):
        """Closes the milvus vector db."""
