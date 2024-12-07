#!/bin/bash

########################################################
#
#  Backup all the collection data. The collection name must be passed in
#  the command line as the only argument for this program.
#
########################################################
pushd .

COLLECTION_NAME=$1
echo "Backing up RAG Collection: $COLLECTION_NAME"

COLLECTION_DIR=/home/vagrant/ragit-data/$COLLECTION_NAME

if [ ! -d "$COLLECTION_DIR" ]; then
    echo "Error: Directory '$COLLECTION_DIR' does not exist." >&2
    exit -1
fi

cd $COLLECTION_DIR
pg_dump -U postgres $COLLECTION_NAME > "$COLLECTION_NAME.sql"
cd ..

tar -czvf "$COLLECTION_NAME".tar.gz "$COLLECTION_NAME"

rm ./"$COLLECTION_NAME/$COLLECTION_NAME.sql"

popd
