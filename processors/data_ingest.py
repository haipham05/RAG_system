import glob, psycopg2
from pymilvus import connections, Collection
from rdb_storer import rdb_storer
from vectordb_storer import vectordb_storer

pdf_paths = glob.glob("data/pdfs/*.pdf")
if not pdf_paths: raise SystemExit("No PDFs in data/pdfs")

pg = psycopg2.connect(host="postgres", database="ragdb", user="raguser", password="ragpass")
chunk_ids, chunk_texts = rdb_storer(pg, pdf_paths)
if not chunk_ids: raise SystemExit("No chunks stored in Postgres")

connections.connect(host="milvus", port="19530")
col = Collection("chunks"); col.load()
vectordb_storer(col, chunk_ids, chunk_texts, model_name="all-MiniLM-L6-v2")
print("Ingestion complete:", len(chunk_ids))