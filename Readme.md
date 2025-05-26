📚 Generador Automático de Cuestionarios Educativos
Sistema para crear evaluaciones académicas automáticamente a partir de documentos PDF

🌟 Características Principales
🎯 Generación automática de preguntas (opción múltiple, verdadero/falso, abiertas)

📄 Procesamiento inteligente de documentos académicos en PDF

🧠 Uso de modelos LLM (Ollama) para comprensión semántica

📊 Personalización de tipos y cantidad de preguntas

📁 Exportación a PDF listo para imprimir

## 📦 Requisitos del Sistema

- **Python 3.10+**
- **Ollama instalado localmente**
- **Modelo LLM descargado** (recomendado: `llama3.2:8b`)

---

## 📑 Dependencias

### 🔧 Core del Generador
```bash
langchain-community==0.2.1
langchain-core==0.2.2
langchain-ollama==0.1.4
ollama==0.1.11

📄 Procesamiento de PDF
unstructured[pdf]==0.13.4
pikepdf==8.15.0
pdfminer.six==20221105

📊 Base de Datos Vectorial
chromadb==0.4.24
sentence-transformers==2.7.0

🖥️ Interfaz Web
streamlit==1.33.0

📝 Generación de PDF
reportlab==4.2.0

📦 Requisitos Adicionales

Python 3.10+

Ollama instalado localmente

Modelo LLM descargado (recomendado: llama3.2:latest)

🚀 Instalación

1️⃣ Clona el repositorio:

git clone https://github.com/emilker/EduQuizGen.git

2️⃣ Crea y activa un entorno virtual:

python -m venv venv
venv\Scripts\activate

3️⃣ Instala las dependencias:

pip install -r requirements.txt

4️⃣ Descarga el modelo de Ollama:

ollama pull llama3.2:8b

🖥️ Uso

Interfaz Web (Recomendado)
streamlit run app.py y listo

O Línea de Comandos

python main.py documento.pdf --num_preguntas 10 --tema "Biología Celular"

🏗️ Estructura del Proyecto

generador-cuestionarios/
├── app.py                # Interfaz web principal
├── main.py               # Versión CLI
├── config.py             # Configuración global
├── document_processor.py # Procesamiento de PDFs
├── quiz_generator.py     # Generación de preguntas
├── vector_db.py          # Almacenamiento vectorial
├── requirements.txt      # Dependencias
└── README.md             # Este archivo

⚙️ Configuración
Edita config.py para personalizar:

CONFIG = {
    "MODELO_LLM": "llama3.2:8b",       # Modelo a usar
    "CHUNK_SIZE": 1200,                # Tamaño de fragmentos de texto
    "CHUNK_OVERLAP": 300,              # Solapamiento entre fragmentos
    "MAX_PREGUNTAS": 20,               # Máximo de preguntas por cuestionario
    "DB_DIR": "./vector_db"            # Carpeta para bases vectoriales
}


