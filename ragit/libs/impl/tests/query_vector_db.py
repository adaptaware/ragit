"""Queries the vector_db."""

import os
import ragit.libs.common as common

import ragit.libs.impl.vdb_factory as vector_db

os.environ["VECTOR_DB_PROVIDER"] = "CHROMA"
VECTOR_DB_PATH = "/home/vagrant/ragit-data/mw/vectordb/mw-chroma-vector.db"
VECTOR_COLLECTION_NAME = "chunk_embeddings"


def query_vector_db(query):
    """Creates and queries a vector db."""
    vdb = vector_db.get_vector_db(VECTOR_DB_PATH, VECTOR_COLLECTION_NAME)

    matches = vdb.query(query, 3)
    for match in matches:
        txt = match[0]
        dist = match[1]
        source = match[2]
        page = match[3]

        print(txt)


if __name__ == '__main__':
    common.init_settings()
    query_vector_db("What is CALC ACTION?")
