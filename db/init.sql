CREATE ROLE repl_user REPLICATION LOGIN PASSWORD 'kali';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 scram-sha-256');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();

\connect db_bot;

CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(25) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

INSERT INTO phones (phone_number) VALUES ('+7234567890');
INSERT INTO emails (email) VALUES ('example1@example.com');


