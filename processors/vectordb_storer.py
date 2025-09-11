import logging
from pymilvus import Collection
from sentence_transformers import SentenceTransformer

def vectordb_storer(
    milvus_collection: Collection, 
    chunk_ids: list[int], 
    chunk_texts: list[str], 
    model_name: str
):
    """
    Generates embeddings for text chunks and stores them in Milvus.
    """
    logging.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    logging.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
    embeddings = model.encode(chunk_texts, show_progress_bar=True)

    if len(chunk_ids) == len(embeddings):
        logging.info("Inserting embeddings into Milvus...")
        milvus_collection.insert([chunk_ids, embeddings])
        milvus_collection.flush()
        logging.info("Successfully inserted embeddings into Milvus.")
    else:
        logging.error("Mismatch between chunk IDs and embeddings count. Aborting Milvus insert.")

