-- Create database and user
CREATE DATABASE ragdb;
CREATE USER raguser WITH PASSWORD 'ragpass';
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;

-- Connect to the database
\c ragdb;

-- Create chunks table
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    paper_filename VARCHAR(255),
    section_title VARCHAR(500),
    chunk_text TEXT
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO raguser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO raguser;
