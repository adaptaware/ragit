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

    matches = vdb.query(query, 44)
    for match in matches:
        txt = match[0]
        dist = match[1]
        source = match[2]
        page = match[3]

        print(txt)
        print(dist)
        print(source)
        print('=' * 70)


if __name__ == '__main__':
    common.init_settings()
    # query_vector_db("What is calc action? (do not consider upper lower case in the embeddings)")
    # query_vector_db("What is calc action?")

    #q = "can you write a flow using the calc action?"
#     q = "can you write a calc action?"
#     query_vector_db(q)
#
#     print("+" * 80)
#     q = "can you write a flow using the  calc action?"

    q = "what is the Geneva service?"
    query_vector_db(q)

