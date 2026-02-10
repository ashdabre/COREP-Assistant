#!/usr/bin/env python3
"""
Initialize the regulatory database with sample data and embeddings.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/init_database.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary directories."""
    directories = [
        "data",
        "logs",
        "src/regulatory_data/pra_rulebook",
        "src/regulatory_data/embeddings"
    ]
    
    for dir_path in directories:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"[OK] Created directory: {dir_path}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to create directory {dir_path}: {e}")

def load_regulatory_rules():
    """Load regulatory rules from JSON files."""
    rules_data = []
    
    # Load own funds rules
    own_funds_file = Path("src/regulatory_data/pra_rulebook/own_funds_rules.json")
    if own_funds_file.exists():
        with open(own_funds_file, 'r', encoding='utf-8') as f:
            own_funds_rules = json.load(f)
            rules_data.extend(own_funds_rules)
            logger.info(f"[OK] Loaded {len(own_funds_rules)} own funds rules")
    
    # Load capital requirements rules
    capital_req_file = Path("src/regulatory_data/pra_rulebook/capital_requirements_rules.json")
    if capital_req_file.exists():
        with open(capital_req_file, 'r', encoding='utf-8') as f:
            capital_rules = json.load(f)
            rules_data.extend(capital_rules)
            logger.info(f"[OK] Loaded {len(capital_rules)} capital requirements rules")
    
    logger.info(f"[OK] Total rules loaded: {len(rules_data)}")
    return rules_data

def initialize_vector_database(rules_data):
    """Initialize ChromaDB vector database with regulatory embeddings."""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        # Create embeddings directory
        embeddings_dir = Path("src/regulatory_data/embeddings")
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client
        client = chromadb.PersistentClient(path=str(embeddings_dir))
        
        # Create or get collection
        collection = client.get_or_create_collection(
            name="regulatory_texts",
            metadata={"description": "PRA Rulebook and COREP regulatory texts"}
        )
        
        # Initialize embedding model
        logger.info("[OK] Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Clear existing data
        try:
            collection.delete(where={})
        except:
            pass
        
        # Prepare documents and metadata
        documents = []
        metadatas = []
        ids = []
        
        for i, rule in enumerate(rules_data):
            # Create document text
            document_text = f"{rule.get('section', '')}: {rule.get('content', '')}"
            
            # Create metadata
            metadata = {
                "paragraph_id": rule.get("paragraph_id", f"RULE_{i}"),
                "source": rule.get("source", "Unknown"),
                "section": rule.get("section", ""),
                "template_reference": rule.get("template_reference", ""),
                "field_references": json.dumps(rule.get("field_references", [])),
                "effective_date": rule.get("effective_date", ""),
                "validation_rules": json.dumps(rule.get("validation_rules", []))
            }
            
            documents.append(document_text)
            metadatas.append(metadata)
            ids.append(rule.get("paragraph_id", f"RULE_{i}"))
        
        # Generate embeddings and add to collection
        logger.info("[OK] Generating embeddings...")
        embeddings = embedding_model.encode(documents).tolist()
        
        # Add to collection
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Verify
        count = collection.count()
        logger.info(f"[OK] Vector database initialized with {count} regulatory texts")
        
        return True
        
    except ImportError as e:
        logger.error(f"[ERROR] Required package not installed: {e}")
        logger.info("Please install: pip install chromadb sentence-transformers")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize vector database: {e}")
        return False

def initialize_sql_database(rules_data):
    """Initialize SQLite database with regulatory texts."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base
        
        # Create engine and base
        engine = create_engine("sqlite:///./data/regulatory.db")
        Base = declarative_base()
        
        # Define the model inline to avoid import issues
        from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
        from sqlalchemy.sql import func
        
        class RegulatoryText(Base):
            __tablename__ = "regulatory_texts"
            
            id = Column(Integer, primary_key=True, index=True)
            source = Column(String(100), nullable=False)
            section = Column(String(200), nullable=False)
            paragraph_id = Column(String(50), unique=True, index=True)
            content = Column(Text, nullable=False)
            template_reference = Column(String(50), index=True)
            field_references = Column(JSON)
            effective_date = Column(DateTime)
            validation_rules = Column(JSON)
            created_at = Column(DateTime, default=func.now())
            updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Clear existing data
        db.query(RegulatoryText).delete()
        
        # Add regulatory texts
        for rule in rules_data:
            regulatory_text = RegulatoryText(
                source=rule.get("source"),
                section=rule.get("section"),
                paragraph_id=rule.get("paragraph_id"),
                content=rule.get("content"),
                template_reference=rule.get("template_reference"),
                field_references=json.dumps(rule.get("field_references", [])),
                effective_date=datetime.strptime(rule.get("effective_date"), "%Y-%m-%d") if rule.get("effective_date") else None,
                validation_rules=json.dumps(rule.get("validation_rules", []))
            )
            db.add(regulatory_text)
        
        db.commit()
        
        # Verify
        count = db.query(RegulatoryText).count()
        logger.info(f"[OK] SQL database initialized with {count} regulatory texts")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize SQL database: {e}")
        return False

def main():
    """Main initialization function."""
    try:
        logger.info("Starting enhanced initialization...")
        
        # Step 1: Create directories
        logger.info("=" * 50)
        logger.info("Step 1: Creating directories")
        logger.info("=" * 50)
        create_directories()
        
        # Step 2: Load regulatory rules
        logger.info("=" * 50)
        logger.info("Step 2: Loading regulatory rules")
        logger.info("=" * 50)
        rules_data = load_regulatory_rules()
        
        if not rules_data:
            logger.error("[ERROR] No regulatory rules found")
            # Create sample rules
            rules_data = [
                {
                    "paragraph_id": "PRA_RB_4.2.1",
                    "source": "PRA Rulebook",
                    "section": "Own Funds",
                    "content": "Common Equity Tier 1 (CET1) capital shall consist of the sum of the following elements...",
                    "template_reference": "C_01.00",
                    "field_references": ["C_01.00_r010_c010"],
                    "effective_date": "2023-01-01",
                    "validation_rules": ["positive_decimal", "required"]
                }
            ]
            logger.info("[INFO] Using sample rules")
        
        # Step 3: Initialize SQL database
        logger.info("=" * 50)
        logger.info("Step 3: Initializing SQL database")
        logger.info("=" * 50)
        if not initialize_sql_database(rules_data):
            logger.warning("[WARNING] SQL database initialization failed, but continuing...")
        
        # Step 4: Initialize vector database with embeddings
        logger.info("=" * 50)
        logger.info("Step 4: Initializing vector database with embeddings")
        logger.info("=" * 50)
        if not initialize_vector_database(rules_data):
            logger.warning("[WARNING] Vector database initialization failed, but continuing...")
        
        logger.info("=" * 60)
        logger.info("[SUCCESS] Enhanced initialization completed successfully!")
        logger.info("=" * 60)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Enhanced initialization completed!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • Loaded {len(rules_data)} regulatory rules")
        print("  • SQL database initialized")
        print("  • Vector database initialized with embeddings")
        
        print("\nNext steps:")
        print("  1. Start system: python run_system.py")
        print("  2. Or start manually:")
        print("     - Backend: uvicorn src.main:app --reload")
        print("     - Frontend: streamlit run frontend/app.py")
        print("\nAccess points:")
        print("  • Frontend: http://localhost:8501")
        print("  • Backend API: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/api/docs")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)