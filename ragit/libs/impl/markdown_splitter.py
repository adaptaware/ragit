"""Defines the markdown splitter functionality."""

import openai


def invoke(markdown_txt):
    prompt = _PROMPT.format(markdown_text=markdown_txt)
    return _QueryExecutor.invoke(prompt)


class _QueryExecutor:
    """Manages the LLM session to get a RAG response.

    :cvar vector_db.AbstractVectorDb _vdb: The vector database.
    :cvar OpenAI _openai_client: The OpenAI client to use.
    :cvar str _model_name: The name of the model to use.
    """

    _openai_client = None
    _model_name = "gpt-4o"

    @classmethod
    def invoke(cls, markdown_text,
               temperature=0.2, max_tokens=16000):
        """Executes a query getting a RAG response.

        :param str question: The question to ask.
        :param int k: The number of matches to return.
        :param float temperature: The temperature to use for the query.
        :param float max_tokens: The max_tokens to use for the query.

        :return: An instance of the QueryResponse.
        :rtype: QueryResponse

        :raises ValueError
        """
        if not cls._openai_client:
            cls._openai_client = openai.OpenAI()

        prompt = _PROMPT.format(markdown_text=markdown_text)

        print('-------')
        print(prompt)
        print('**************************************')

        response = cls._openai_client.chat.completions.create(
            model=cls._model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        response_content = response.choices[0].message.content
        return response_content

    @classmethod
    def close(cls):
        """Closes the vector db and clears the openai client."""
        cls._openai_client = None


_PROMPT = """
summarize the following markdown text also add a small summary before each
chunk and also for each chunk add 2 to 3 questions that can be answered by it
if you encounter a markdown table you should ingnore it all together. also you 
need to print the headers chain for each chunk:

{markdown_text}
"""
