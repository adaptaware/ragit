"""A REPL tool for managing RAG collections."""

import cmd
import dataclasses
import functools


import nest_asyncio

import ragit.libs.common as common
import ragit.libs.dbutil as dbutil
import ragit.libs.rag_mgr as rag_mgr

_HELP = """
l (list): List all available collections.
s (stats) <name>: Print its stats for the pass in collection.
p (process): Process the data the passed in collection.
m (create_markdowns): Creates missing markdowns.
h (help): Prints this help message.
e (exit): Exit.
"""


def catch_exceptions(func):
    """Catches and prints any exceptions raised by func.

    :param callable func: The function to decorate.
    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        """Catches and prints any exception raised by the decorable."""
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            print("error")
            print(ex)

    return inner


class RAGCollectionTracker(cmd.Cmd):
    """A utility class to interact with RAGit back end.

    :cvar str intro: Used from parent class.
    :cvar str prompt: Used from parent class.

    :ivar str _collection_name: The name of the active collection.
    """

    intro = "Welcome to the RAG Collection Tracker. " \
            "Type help or ? to list commands.\n"
    prompt = "(RAGit) "

    @catch_exceptions
    def do_stats(self, collection_name):
        """Shows the statistics for the passed in collection name.

        :param str collection_name: The collection name to use.
        """
        dbutil.create_db_if_needed(
            collection_name, common.get_rag_db_schema()
        )

        conn_str = common.make_local_connection_string(collection_name)
        dbutil.SimpleSQL.register_connection_string(conn_str)
        ragger = rag_mgr.RagManager(collection_name)

        with dbutil.SimpleSQL() as db:
            stats = ragger.get_metrics(db)
            for field in dataclasses.fields(stats):
                field_name = field.name
                field_value = getattr(stats, field_name)
                name = f"{field_name.replace('_', ' ').ljust(25, '.')}"
                print(f"{name}: {field_value}")

    def do_s(self, arg):
        """Alias to the collection stats command.

        :param str arg: The collection name to use.
        """
        self.do_stats(arg)

    @catch_exceptions
    def do_process(self, collection_name):
        """Processes all the un-processed documents for the active collection.

        :param str collection_name: The collection name to use.

        """
        dbutil.create_db_if_needed(
            collection_name, common.get_rag_db_schema()
        )

        conn_str = common.make_local_connection_string(collection_name)
        dbutil.SimpleSQL.register_connection_string(conn_str)
        ragger = rag_mgr.RagManager(collection_name)

        with dbutil.SimpleSQL() as db:
            count = ragger.insert_chunks_to_db(db, verbose=True)
            print(f"Inserted {count} chunks.")
            count = ragger.insert_embeddings_to_db(db, verbose=True)
            print(f"Inserted {count} embeddings.")
            count = ragger.update_vector_db(db, verbose=True)
            print(f"Inserted {count} chunks to the vector db.")

    @catch_exceptions
    def do_create_markdowns(self, collection_name):
        """Creates the missing markdowns.

        :param str collection_name: The collection name to use.
        """
        ragger = rag_mgr.RagManager(collection_name)
        ragger.create_missing_markdowns()

    def do_m(self, arg):
        """Alias to the create images command.."""
        self.do_create_markdowns(arg)

    def do_p(self, collection_name):
        """Alias to the process command.

        :param str collection_name: The collection name to use.
        """
        self.do_process(collection_name)

    @catch_exceptions
    def do_list(self, arg):
        """List all available RAG collections.

        :param str arg: Unused.
        """
        rag_collections = rag_mgr.RagManager.get_all_rag_collections()
        for collection in rag_collections:
            print(collection)

    def do_l(self, arg):
        """Alias to the list command.

        :param str arg: Unused.
        """
        self.do_list(arg)

    def do_help(self, arg):
        """Prints user help.

        :param str arg: Unused.
        """
        print(_HELP)

    def do_h(self, arg):
        """Alias to the help command.

        :param str arg: Unused.
        """
        self.do_help(arg)

    def default(self, arg):
        """Called for unrecognized command.

        :param str arg: Unused.
        """
        print(f"Unrecognized command: {arg}")
        print(_HELP)

    def do_exit(self, arg):
        """Exits the command loop.

        :param str arg: Unused.
        """
        print('Exiting...')
        return True

    def do_e(self, arg):
        """Alias to the exit command.

        :param str arg: Unused.
        """
        self.do_exit(arg)


if __name__ == '__main__':
    nest_asyncio.apply()  # Needed for llama_parse
    common.init_settings()
    RAGCollectionTracker().cmdloop()
