CREATE DATABASE  DB_DATABASE;

CREATE ROLE DB_REPL_USER REPLICATION LOGIN PASSWORD 'DB_REPL_PASSWORD';
SELECT pg_create_physical_replication_slot('replication_slot');


CREATE USER DB_USER WITH REPLICATION LOGIN PASSWORD 'DB_PASSWORD';
ALTER ROLE DB_USER PASSWORD 'DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE DB_DATABASE TO DB_USER;

\connect DB_DATABASE

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
