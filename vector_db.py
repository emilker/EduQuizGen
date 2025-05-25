from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import logging
from config import CONFIG
import os

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=CONFIG["MODELO_EMBEDDINGS"]
            # Eliminado: cache_dir=CONFIG["CACHE_DIR"]
        )
        
    def create_db(self, documents, db_name="default"):
        """Crea una nueva base de datos vectorial"""
        db_path = os.path.join(CONFIG["DB_DIR"], db_name)
        
        try:
            db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=db_path
            )
            logger.info(f"Base de datos vectorial creada en {db_path}")
            return db
        except Exception as e:
            logger.error(f"Error creando DB: {str(e)}")
            return None
    
    def load_db(self, db_name="default"):
        """Carga una base de datos existente"""
        db_path = os.path.join(CONFIG["DB_DIR"], db_name)
        
        if not os.path.exists(db_path):
            logger.error(f"Base de datos no encontrada: {db_path}")
            return None
            
        try:
            db = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings
            )
            logger.info(f"Base de datos cargada desde {db_path}")
            return db
        except Exception as e:
            logger.error(f"Error cargando DB: {str(e)}")
            return None