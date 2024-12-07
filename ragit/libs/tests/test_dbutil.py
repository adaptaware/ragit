"""Tests the dbutil module."""

import unittest

import ragit.libs.dbutil as dbutil
import ragit.libs.common as common

_SQL_CREATE_SCHEMA = """
    CREATE TABLE person
    (
        name      VARCHAR(255)
    );
"""

_SQL_INSERT_PERSON = """
Insert into person (name) values ('{person_name}');
"""


class TestDbUtil(unittest.TestCase):
    """Tests the DbUtil."""

    def test_accessing_db(self):
        """Tests accessing the db."""
        # Create the db.
        dbname = "junk123"
        conn_str = common.make_local_connection_string("postgres")
        dbutil.SimpleSQL.register_connection_string(conn_str)
        with dbutil.SimpleSQL() as db:
            db.execute_non_query(f"drop database if exists {dbname}")
            db.execute_non_query(f"create database {dbname}")

        conn_str = common.make_local_connection_string(dbname)
        dbutil.SimpleSQL.register_connection_string(conn_str)
        names = ["Alice", "Bob", "Charlie", "David", "Emily", "Frank"]

        # Insert some names.
        with dbutil.SimpleSQL() as db:
            db.execute_non_query(_SQL_CREATE_SCHEMA)
            for name in names:
                db.execute_non_query(
                    _SQL_INSERT_PERSON.format(
                        person_name=name
                    )
                )

        # Retrieve and compare the names from the db.
        retrieved_names = []
        with dbutil.SimpleSQL() as db:
            for row in db.execute_query("Select name from person"):
                retrieved_names.append(row[0])

        self.assertListEqual(retrieved_names, names)




