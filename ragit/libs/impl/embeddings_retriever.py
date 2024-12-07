"""Exposes a function to retrieve embeddings for a passed in text."""

import openai


def get_embeddings(txt):
    """Returns the embeddings for the passed in txt.

    :param str txt: The text to create the embeddings for.

    :return: The embeddings for the passed in text.
    :rtype: list [float]
    """
    assert isinstance(txt, str), "get_embeddings expects a string."
    return _LLMWrapper.get_embeddings(txt)


# Whatever follows this line is private to the module and should not be
# used from the outside.

class _LLMWrapper:
    """Wraps the functionality to retrieve embeddings.

    :cvar _client: Holds the OpenAI instance.
    """

    _client = None
    _MODEL_NAME = "text-embedding-ada-002"

    @classmethod
    def get_embeddings(cls, txt):
        """Returns the embeddings for the passed in txt.

        :param str txt: The text to create the embeddings for.

        :return: The embeddings for the passed in text.
        :rtype: list [float]
        """
        if not cls._client:
            cls._client = openai.OpenAI()

        response = cls._client.embeddings.create(
            input=txt,
            model=cls._MODEL_NAME
        )
        embeddings = [r.embedding for r in response.data]
        return embeddings[0]
