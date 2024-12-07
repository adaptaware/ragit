#!/bin/bash

################################################################
# Installs the postgresql and adds the myuser which is meant
# to be used from insider the vagrant box for testing purposes
# only.
#
# This script is not to be use in a deployed environment since
# it trusts all the local users.
################################################################

sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
sudo sed -i 's/md5/trust/g' /etc/postgresql/14/main/pg_hba.conf
sudo sed -i 's/peer/trust/g' /etc/postgresql/14/main/pg_hba.conf
sudo systemctl restart postgresql 

PSQL_USER_NAME="myuser"
PSQL_PASSWORD="password"
PSQL_ENCRYPTED_PASSWORD="password"

cd /vagrant
sudo -u postgres bash -c "psql -c \"CREATE USER $PSQL_USER_NAME WITH PASSWORD '$PSQL_PASSWORD';\""
sudo -u postgres bash -c "psql -c \"ALTER ROLE $PSQL_USER_NAME  WITH CREATEDB;\""
sudo -u postgres bash -c "psql -c \"alter user $PSQL_USER_NAME with encrypted password '$PSQL_ENCRYPTED_PASSWORD';\""
sudo -u postgres bash -c "psql -c \"ALTER user $PSQL_USER_NAME WITH SUPERUSER;\""
cd /home/vagrant

