"""Tests the vector_db module."""

import os
import unittest

import ragit.libs.impl.chunks_mgr as chunks_mgr
import ragit.libs.common as common
import ragit.libs.dbutil as dbutil
import ragit.libs.impl.vdb_factory as vector_db


class TestVectorDb(unittest.TestCase):
    """Tests the VectorDb class."""
    _DB_NAME = "testingvectordb"
    _SQL_CLEAR_CHUNKS = "DElETE FROM chunks"

    @classmethod
    def setUpClass(cls):
        """Class - level setup."""
        common.init_settings()

    def setUp(self):
        """Creates the testing database."""
        dbutil.delete_db_if_exists(self._DB_NAME)
        dbutil.create_db_if_needed(self._DB_NAME, common.get_rag_db_schema())
        conn_str = common.make_local_connection_string(self._DB_NAME)
        dbutil.SimpleSQL.register_connection_string(conn_str)

    def tearDown(self):
        """Cleans up the environment upon finishing a test."""
        dbutil.SimpleSQL.register_connection_string(None)

    def _insert_chunks_to_db(self, db):
        """Inserts the chunks to the database."""
        db.execute_non_query(self._SQL_CLEAR_CHUNKS)
        directory = common.get_testing_data_directory()
        docs_to_chunk = chunks_mgr.find_documents_to_chunk(db, directory)
        for fullpath in docs_to_chunk:
            chunks_mgr.save_chunks_to_db(db, fullpath)

    def _create_and_query_vector_db(self, db_name):
        """Creates and queries a vector db."""
        parent_dir = common.get_testing_output_dir(
            "creating-vector-db",
            wipe_out=True
        )
        collection = "dummy"
        fullpath = os.path.join(parent_dir, db_name)
        vdb = vector_db.get_vector_db(fullpath, collection)
        with dbutil.SimpleSQL() as db:
            self._insert_chunks_to_db(db)
            count = 0
            for chunk_id in chunks_mgr.find_chunks_missing_embeddings(db):
                count += 1
                chunks_mgr.save_embeddings(db, chunk_id)
                if count > 10:
                    break

            chunks = []
            embeddings = []
            sources = []
            pages = []
            for chunk_id in chunks_mgr.find_chunks_with_embeddings(db):
                embedding_info = chunks_mgr.load_embeddings(db, chunk_id)
                chunks.append(embedding_info.get_chunk())
                sources.append(embedding_info.get_source())
                pages.append(embedding_info.get_page())
                embeddings.append(embedding_info.get_embeddings())

            count = vdb.get_number_of_records()
            self.assertEqual(count, 0)
            vdb.insert(chunks[:4], embeddings[:4], sources[:4], pages[:4])
            count = vdb.get_number_of_records()
            self.assertEqual(count, 4)
            vdb.insert(chunks[4:], embeddings[4:], sources[4:], pages[4:])
            count = vdb.get_number_of_records()
            self.assertEqual(count, len(embeddings))
            query = "Is SQL Alchemy good?"
            matches = vdb.query(query, 3)
            for match in matches:
                txt = match[0]
                dist = match[1]
                source = match[2]
                page = match[3]
                self.assertIsInstance(txt, str)
                self.assertIsInstance(dist, float)
                self.assertTrue(isinstance(source, str) or source is None)
                self.assertTrue(isinstance(page, int) or page == 'n/a')

    def test_creation_using_chroma(self):
        """Tests creating a VectorDb using chroma."""
        os.environ["VECTOR_DB_PROVIDER"] = "CHROMA"
        self._create_and_query_vector_db("chroma_vector.db")

    def test_creation_using_milvus(self):
        """Tests creating a VectorDb using milvus."""
        os.environ["VECTOR_DB_PROVIDER"] = "MILVUS"
        self._create_and_query_vector_db("milvus_vector.db")
