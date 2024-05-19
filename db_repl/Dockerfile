FROM postgres:15

CMD ["bin/bash", "-c", "rm -rf /var/lib/postgresql/data/* && until pg_basebackup --pgdata=/var/lib/postgresql/data -R --slot=replication_slot --host=db --port=5432; do echo 'Waiting for primary to connect...'; sleep 1s; done; echo 'Backup done, starting replica...'; chown -R postgres:postgres /var/lib/postgresql/data; chmod 700 /var/lib/postgresql/data; su - postgres -c 'exec /usr/lib/postgresql/15/bin/postgres -D /var/lib/postgresql/data';"]
