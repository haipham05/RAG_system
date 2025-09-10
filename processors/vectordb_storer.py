import logging
from pymilvus import Collection
from sentence_transformers import SentenceTransformer

def populate_vectordb(
    milvus_collection: Collection, 
    chunk_ids: list[int], 
    chunk_texts: list[str], 
    model_name: str
):
    """
    Generates embeddings for text chunks and stores them in Milvus.
    """
    # 1. Load the embedding model
    logging.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # 2. Generate embeddings
    logging.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
    embeddings = model.encode(chunk_texts, show_progress_bar=True)

    # 3. Prepare and insert data into Milvus
    if len(chunk_ids) == len(embeddings):
        logging.info("Inserting embeddings into Milvus...")
        milvus_collection.insert([chunk_ids, embeddings])
        milvus_collection.flush()
        logging.info("Successfully inserted embeddings into Milvus.")
    else:
        logging.error("Mismatch between chunk IDs and embeddings count. Aborting Milvus insert.")

