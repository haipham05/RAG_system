import os
import logging
from psycopg2.extensions import connection
from psycopg2.extras import execute_batch
from extract_chunk import extract, chunk

def rdb_storer(pg_conn: connection, pdf_path: list[str]) -> tuple[list[int] | None, list[str] | None]:
    """
    Process PDFs to extract, chunk then store in RDB.
    """
    if not pdf_path:
        logging.warning("No PDF provided. Nothing processed.")
        return None, None
    
    pdf_name = [os.path.basename(p) for p in pdf_path]

    logging.info(f"Processing {len(pdf_name)} PDFs")
    extracted_text = extract(pdf_path)

    chunk_to_embedd = []
    chunk_to_rdb = []
    chunk_ids = []
    counter = 1

    for i, text in enumerate(extracted_text):
        filename = pdf_name[i]
        logging.info(f"Processing {filename}")
        paper_chunks = chunk(text)
        for chunk in paper_chunks:
            chunk_to_embedd.append(chunk['content'])
            chunk_to_rdb.append((counter, filename, chunk['title'], chunk['content']))
            chunk_ids.append(counter)
            counter += 1

        if not chunk_to_rdb:
            logging.warning(f"No chunks found for {filename}")
            return None, None

    logging.info(f"Inserting {len(chunk_to_rdb)} chunks into PostgreSQL...")
    with pg_conn.cursor() as cur:
        execute_batch(
            cur, 
            "INSERT INTO chunks (id, paper_filename, section_title, chunk_text) VALUES (%s, %s, %s, %s)", 
            chunk_to_rdb
        )
        pg_conn.commit()

    return chunk_ids, chunk_to_embedd