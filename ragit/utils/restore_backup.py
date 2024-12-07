"""Restores a backed up RAG Collection.

To recreate the database if needed you can manually run the following:

dropdb -U postgres $COLLECTION_NAME
createdb -U postgres $COLLECTION_NAME
psql -U postgres -d $COLLECTION_NAME -f "$COLLECTION_NAME.sql"
"""

import os
import sys


def restore_backup(backup_file):
    """Restores the RAG collection from the passed in backup_file.

    :param str backup_file: The name of the backup file to use.
    """
    ragit_data_dir = "/home/vagrant/ragit-data"
    assert os.path.isdir(ragit_data_dir), f"Invalid Ragit dir {ragit_data_dir}"
    assert os.path.isfile(backup_file), f"{backup_file} does not exist."
    assert backup_file.endswith(".tar.gz"), f"{backup_file} not a tar.gz file."
    result = os.system(f"tar -xzvf {backup_file} -C {ragit_data_dir}")
    assert result == 0, "Extraction failed."


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            "Invalid use. You must pass the backup file"
            " as the only command line argument."
        )
        sys.exit(-1)
    restore_backup(sys.argv[1])
