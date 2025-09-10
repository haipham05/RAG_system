import logging
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, connections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_milvus_collection():
    """Create the chunks collection in Milvus"""
    try:
        # Connect to Milvus
        connections.connect("default", host="milvus", port="19530")
        logger.info("Connected to Milvus")
        
        # Define collection schema
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)  # all-MiniLM-L6-v2 dimension
        ]
        
        schema = CollectionSchema(fields, "Chunks collection for RAG system")
        
        # Create collection
        collection_name = "chunks"
        if collection_name in connections.get_connection("default").list_collections():
            logger.info(f"Collection {collection_name} already exists")
            return Collection(collection_name)
        
        collection = Collection(collection_name, schema)
        logger.info(f"Created collection: {collection_name}")
        
        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index("embedding", index_params)
        logger.info("Created index on embedding field")
        
        return collection
        
    except Exception as e:
        logger.error(f"Error setting up Milvus: {e}")
        raise

if __name__ == "__main__":
    setup_milvus_collection()
