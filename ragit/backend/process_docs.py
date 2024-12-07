"""Updates the chunks, embeddings and vector db for a RAG collection.

Arguments

-n <collection-name>`: Name of the RAG collection to update.
-p: Processes the documents for the passed in collection.
-l: Prints the list of all the available RAG collections.
-h: Prints the user help.
------------------------------------------------------------------------------
Assumptions

- Documents for the RAG collection are stored in the directory:
  `~/ragit-data/<collection-name>/documents`. Users need to create this
  directory beforehand and add the documents they want to use.

- A PostgreSQL database named `<collection-name>` is required. Use the script
  `ragit/db/create-db.sh <collection-name>` to create it.

------------------------------------------------------------------------------
Functionality

- Processes documents from the specified directory.

- Generates chunks, embeddings, and updates the vector database.

- Can be run repeatedly with the same collection name for updates if new
  documents are added.

------------------------------------------------------------------------------
Notes

- This script assumes a specific directory structure (`~/ragit-data`) for
  storing data. Adjust the paths if needed.

- The script relies on an external script `ragit/db/create-db.sh` for
  database creation (implementation not shown).
"""

import argparse
import dataclasses

import ragit.libs.common as common
import ragit.libs.dbutil as dbutil
import ragit.libs.rag_mgr as rag_mgr

_DESC = "Updates the chunks, embeddings, and vector" \
        " database for a RAG collection."


def parse_args():
    """Returns the command line arguments."""
    parser = argparse.ArgumentParser(description=_DESC)
    parser.add_argument(
        '-n',
        '--name',
        help='The name of the RAG collection.'
    )
    parser.add_argument(
        '-p',
        '--process_it',
        action='store_true',
        help='Insert missing embeddings and insert into vector db.'
    )
    parser.add_argument(
        '-l',
        '--list',
        action='store_true',
        help='lists the available RAG collections.'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_false',
        help='If true will print information about its progress.'
    )
    parsed_args = parser.parse_args()
    return parsed_args


def main():
    """Updates the vector db for any given directory."""
    common.init_settings()
    args = parse_args()
    if args.list and args.name:
        print("Cannot pass list and collection name simultaneously")
        exit(-1)
    elif args.list:
        rag_collections = rag_mgr.RagManager.get_all_rag_collections()
        for collection in rag_collections:
            print(collection)
    elif args.name:
        # Create the database for the collection name if it is not available.
        dbutil.create_db_if_needed(args.name, common.get_rag_db_schema())

        conn_str = common.make_local_connection_string(args.name)
        dbutil.SimpleSQL.register_connection_string(conn_str)
        ragger = rag_mgr.RagManager(args.name)
        verbose = args.verbose
        with dbutil.SimpleSQL() as db:
            if args.process_it:
                count = ragger.insert_chunks_to_db(db, verbose=verbose)
                if verbose:
                    print(f"Inserted {count} chunks.")
                count = ragger.insert_embeddings_to_db(db, verbose=verbose)
                if verbose:
                    print(f"Inserted {count} embeddings.")
                count = ragger.update_vector_db(db, verbose=verbose)
                if verbose:
                    print(f"Inserted {count} chunks to the vector db.")
            else:
                stats = ragger.get_metrics(db)
                for field in dataclasses.fields(stats):
                    field_name = field.name
                    field_value = getattr(stats, field_name)
                    name = f"{field_name.replace('_', ' ').ljust(25, '.')}"
                    print(f"{name}: {field_value}")


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print(ex)
