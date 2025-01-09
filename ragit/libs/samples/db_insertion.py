"""Creates a trivial RAG collection for testing purposes."""

import os

import ragit.libs.dbutil as dbutil
import ragit.libs.common as common
import ragit.libs.rag_mgr as rag_mgr

RagManager = rag_mgr.RagManager

_RAG_COLLECTION = "fb1"
_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def initialize():
    """Initialize the environment."""
    cmd = os.path.join(_CURRENT_DIR, f"rag_cleanup.sh {_RAG_COLLECTION}")
    os.system(cmd)
    common.init_settings()
    dbutil.create_db_if_needed(
        _RAG_COLLECTION, common.get_rag_db_schema()
    )
    conn_str = common.make_local_connection_string(_RAG_COLLECTION)
    dbutil.SimpleSQL.register_connection_string(conn_str)


def create_rag_collection():
    """Populates the trivial RAG collection."""
    ragger = rag_mgr.RagManager(_RAG_COLLECTION)

    with dbutil.SimpleSQL() as db:
        count = ragger.insert_chunks_to_db(db, verbose=True)
        print(f"Inserted {count} chunks.")
        count = ragger.insert_embeddings_to_db(db, verbose=True)
        print(f"Inserted {count} embeddings.")
        count = ragger.update_vector_db(db, verbose=True)
        print(f"Inserted {count} chunks to the vector db.")


if __name__ == '__main__':
    initialize()
    create_rag_collection()
