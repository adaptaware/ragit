"""Exposes a class to encapsulate the embedding data."""

import copy


class EmbeddingsInfo:
    """Helper class to encapsulate to embedding data."""

    def __init__(self, chunk, embeddings, source, page):
        """Initializer.

        :param str chunk: The text associated with the specified chunk ID.
        :param list[float] embeddings: The embeddings of the chunk.
        :param str source: The source from where the chunk was derived.
        :param int page: The page number associated with the chunk.
        """
        self.__chunk = chunk
        self.__embeddings = copy.deepcopy(embeddings)
        self.__source = source
        self.__page = page

    def get_chunk(self):
        """Returns the text associated with the specified chunk ID.

        :return: The chunk text.
        :rtype: str
        """
        return self.__chunk

    def get_embeddings(self):
        """Returns the embeddings of the chunk.

        :return: A list of floats representing the embeddings.
        :rtype: list[float]
        """
        return copy.deepcopy(self.__embeddings)

    def get_source(self):
        """Returns the source from where the chunk was derived.

        :return: The source as a string, or None if not available.
        :rtype: str | None
        """
        return self.__source

    def get_page(self):
        """Returns the page number associated with the chunk.

        :return: The page number as an integer, or None if not available.
        :rtype: int | None
        """
        return self.__page
