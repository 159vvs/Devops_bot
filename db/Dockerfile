FROM postgres:15
COPY init.sql /docker-entrypoint-initdb.d/
USER postgres
RUN touch /var/log/postgresql/postgres.log