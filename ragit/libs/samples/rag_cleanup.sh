#!/bin/bash

##############################################################################
#
# For the passed in collection name:
#
# - Removes the corresponding registry database.
# - Removes the backup directory.
# - Removes the corresponding psql database.
# - Removes the corresponding vectordb database.
#
##############################################################################

# echo -n "Do you want to clean up the RAG collection $1 (y/n)"
#
# read -r user_selection
#
# if [ "$user_selection" != "y" ]; then
#     exit 1
# fi

set -x
dropdb -U postgres $1
rm -rf $HOME/ragit-data/$1/vectordb
