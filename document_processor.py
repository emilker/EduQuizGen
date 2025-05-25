import os
from datetime import datetime
import logging
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from config import CONFIG

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["CHUNK_SIZE"],
            chunk_overlap=CONFIG["CHUNK_OVERLAP"]
        )

    def load_and_split(self, file_path):
        """Carga y divide un documento PDF"""
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None

        try:
            loader = UnstructuredPDFLoader(file_path, mode="elements", strategy="fast")
            docs = loader.load()
            
            # Filtrar metadatos complejos
            filtered_docs = filter_complex_metadata(docs)
            
            # Añadir metadatos simples
            for doc in filtered_docs:
                doc.metadata.update({
                    "procesado_el": datetime.now().isoformat(),
                    "origen": file_path
                })
            
            chunks = self.text_splitter.split_documents(filtered_docs)
            logger.info(f"Documento dividido en {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            return None