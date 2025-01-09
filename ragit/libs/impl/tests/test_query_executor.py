"""Tests the query executor module."""

import os

import unittest

import ragit.libs.impl.chunks_mgr as chunks_mgr
import ragit.libs.common as common
import ragit.libs.dbutil as dbutil
import ragit.libs.impl.query_executor as query_executor
import ragit.libs.impl.vdb_factory as vector_db

_CODE_TO_FORMAT = """
def get_x(sql_statement):
# Assuming dbutil is used to interact with the database
# Execute the SQL statement using dbutil and retrieve the rows
retrieved_rows = dbutil.execute(sql_statement)

return retrieved_rows
"""

_CONTEXT_TO_FORMAT = """
To create a Python function called `get_x` that receives a SQL statement as a
string and returns the retrieved rows from the database using `dbutil`, you can
follow the example code below:

```python
def get_x(sql_statement):
# Assuming dbutil is used to interact with the database
# Execute the SQL statement using dbutil and retrieve the rows
retrieved_rows = dbutil.execute(sql_statement)

return retrieved_rows
```

In this function:
- `sql_statement` is the SQL query string that will be executed against the
  database.
- `dbutil.execute(sql_statement)` is a placeholder function call that you
  should replace with the actual method or function provided by `dbutil` to
  execute SQL statements and retrieve data from the database.

Remember to replace `dbutil.execute(sql_statement)` with the correct method
from `dbutil` that suits your specific database interaction needs.

```python
def add(i, j):
x = i + j
return x
```
"""


class TestQueryExecutor(unittest.TestCase):
    """Tests the chunks_mgr module."""

    _DB_NAME = "testqueries"
    _SQL_CLEAR_CHUNKS = "DElETE FROM chunks"

    def setUp(self):
        """Creates the testing database."""
        dbutil.delete_db_if_exists(self._DB_NAME)
        dbutil.create_db_if_needed(self._DB_NAME, common.get_rag_db_schema())
        os.environ["VECTOR_DB_PROVIDER"] = "MILVUS"
        if os.environ.get("OPENAI_API_KEY"):
            del os.environ["OPENAI_API_KEY"]

    def tearDown(self):
        """Cleans up the environment upon finishing a test."""
        dbutil.SimpleSQL.register_connection_string(None)

    @classmethod
    def _initialize_env(cls):
        """Initialize the environment.

        :returns: A tuple consisting from the full path to the vector db
        and the collection name to use.
        :rtype: tuple[str, str]
        """
        common.init_settings()
        conn_str = common.make_local_connection_string(cls._DB_NAME)
        dbutil.SimpleSQL.register_connection_string(conn_str)
        folder_path = common.get_testing_output_dir(
            "dummy-testing-query", wipe_out=True
        )

        fullpath_to_db = os.path.join(folder_path, "dummy-vector.db")
        collection_name = "dummy"

        return fullpath_to_db, collection_name

    @classmethod
    def _create_vector_db(cls, fullpath_to_db, collection_name):
        """Creates the vector db for the testing data.

        :param str fullpath_to_db: The full path to the database file to create.
        :param str collection_name: The name of the collection to create.
        """
        with dbutil.SimpleSQL() as db:
            db.execute_non_query(cls._SQL_CLEAR_CHUNKS)
            directory = common.get_testing_data_directory()
            directory = os.path.join(directory, "nested_dir")
            chunks_mgr.insert_chunks_to_db(db, directory, verbose=False)
            chunks_mgr.insert_embeddings_to_db(db, verbose=False)

            vdb = vector_db.get_vector_db(fullpath_to_db, collection_name)
            chunks = []
            embeddings = []
            sources = []
            pages = []
            for chunk_id in chunks_mgr.find_chunks_with_embeddings(db):
                embeddings_info = chunks_mgr.load_embeddings(db, chunk_id)
                chunks.append(embeddings_info.get_chunk())
                embeddings.append(embeddings_info.get_embeddings())
                sources.append(embeddings_info.get_source())
                pages.append(embeddings_info.get_page())
            vdb.insert(chunks, embeddings, sources, pages)

    def test_query(self):
        """Tests the query."""
        common.init_settings()
        fullpath_to_db, collection_name = self._initialize_env()
        self._create_vector_db(fullpath_to_db, collection_name)
        query_executor.initialize(fullpath_to_db, collection_name)
        retrieved = query_executor.query("What is method chaining?")
        resp = retrieved.response
        self.assertIn("method chaining", resp.lower())

    def test_invalid_full_path_to_db(self):
        """Tests passing invalid path to db to initialize."""
        with self.assertRaises(common.MyGenAIException):
            query_executor.initialize("junk", "junk")

    def test_format_python_code(self):
        """Tests the format_python_code function. """
        common.init_settings()
        retrieved = query_executor._QueryExecutor._format_python_code(
            _CODE_TO_FORMAT
        )
        count = retrieved.count("```python")
        self.assertEqual(count, 1)

    def test_substitute_python_code(self):
        """Tests the _substitute_python_code function."""
        common.init_settings()
        retrieved = query_executor._QueryExecutor._substitute_python_code(
            _CONTEXT_TO_FORMAT
        )
        count = retrieved.count("```python")
        self.assertEqual(count, 2)
