import os
import hashlib
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

# Configuration
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "sql-knowledge")
DB_PATH = os.path.join(DATA_DIR, "ingestion_metadata.db")

# Postgres Connection
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sqlrag")
COLLECTION_NAME = "sql_documents"

MODEL_NAME = "nomic-embed-text" 
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DATA_DIR, "ingestion.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IngestionManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()
        self.embeddings = OllamaEmbeddings(model=MODEL_NAME)
        
    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    file_hash TEXT,
                    processed_at TIMESTAMP
                )
            """)

    def get_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def is_file_processed(self, filename: str, current_hash: str) -> bool:
        """Check if file has been processed with the same content."""
        cursor = self.conn.execute(
            "SELECT file_hash FROM processed_files WHERE filename = ?", (filename,)
        )
        row = cursor.fetchone()
        if row:
            return row[0] == current_hash
        return False

    def mark_file_processed(self, filename: str, current_hash: str):
        """Update or insert processed file record."""
        with self.conn:
            self.conn.execute("""
                INSERT INTO processed_files (filename, file_hash, processed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    file_hash = excluded.file_hash,
                    processed_at = excluded.processed_at
            """, (filename, current_hash, datetime.now()))

    def load_documents(self) -> List[Document]:
        """Load and split documents involved in ingestion."""
        documents = []
        
        # Ensure knowledge dir exists
        if not os.path.exists(KNOWLEDGE_DIR):
            logger.warning(f"Knowledge directory not found: {KNOWLEDGE_DIR}")
            return []

        text_files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".txt")]
        
        if not text_files:
            logger.warning("No .txt files found in %s", KNOWLEDGE_DIR)
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )

        for filename in text_files:
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            try:
                current_hash = self.get_file_hash(filepath)
                
                if self.is_file_processed(filename, current_hash):
                    logger.info(f"Skipping {filename} (already processed)")
                    continue

                logger.info(f"Processing {filename}...")
                loader = TextLoader(filepath, encoding='utf-8')
                docs = loader.load()
                splits = splitter.split_documents(docs)
                
                # Add metadata
                for split in splits:
                    split.metadata["source"] = filename
                    split.metadata["file_hash"] = current_hash
                
                documents.extend(splits)
                self.mark_file_processed(filename, current_hash)
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

        return documents

    def run(self):
        logger.info("Starting ingestion process...")
        
        # 1. Load new documents
        new_docs = self.load_documents()
        
        if not new_docs:
            logger.info("No new documents to ingest.")
            return

        logger.info(f"Loaded {len(new_docs)} new document chunks.")

        # 2. Update Vector Store (Postgres)
        try:
            vectorstore = PGVector(
                embeddings=self.embeddings,
                collection_name=COLLECTION_NAME,
                connection=DB_CONNECTION,
                use_jsonb=True,
            )
            # PGVector automatically creates table if not exist
            vectorstore.add_documents(new_docs)
            logger.info("Updated Postgres vector store.")
        except Exception as e:
            logger.error(f"Failed to update vector store: {e}")
            # If running locally without docker DB up, this will fail. 
            # In production, we run this inside the container or when DB is up.
        
        logger.info("Ingestion complete.")

if __name__ == "__main__":
    manager = IngestionManager()
    manager.run()
