#!/bin/bash
mkdir /mnt/postgres/pg_data
chown postgres:postgres /mnt/postgres/pg_data
su -c "/usr/local/pgsql/bin/initdb -D /mnt/postgres/pg_data  --no-locale" postgres
sed -i -e "64i port = 5432" ./pg_data/postgresql.conf
sed -i -e "63i listen_addresses = '*'" ./pg_data/postgresql.conf
sed -i -e "82i host all all 0.0.0.0/0 trust" ./pg_data/pg_hba.conf
su -c "/usr/local/pgsql/bin/pg_ctl start -D /mnt/postgres/pg_data  -w" postgres
exit