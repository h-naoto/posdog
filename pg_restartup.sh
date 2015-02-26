#!/bin/bash
rm -rf /mnt/postgres/pg_data/postmaster.pid
su -c "/usr/local/pgsql/bin/pg_ctl start -D /mnt/postgres/pg_data  -w" postgres