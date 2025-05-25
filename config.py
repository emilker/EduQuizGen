import os
from datetime import datetime

# Configuración básica
CONFIG = {
    "MODELO_LLM": "llama3.2:latest",
    "MODELO_EMBEDDINGS": "nomic-embed-text",
    "CHUNK_SIZE": 1200,
    "CHUNK_OVERLAP": 300,
    "DB_DIR": "./vector_db",
    "MAX_PREGUNTAS": 20
}

# Configuración de prompts
PROMPTS = {
    "CUESTIONARIO": """Eres un generador de cuestionarios educativos profesionales. Basándote EXCLUSIVAMENTE en el siguiente contexto:
{context}

Genera un cuestionario con {num_preguntas} preguntas sobre el tema. Incluye:
- {porcentaje_op_multiple}% preguntas de opción múltiple (4 opciones, 1 correcta)
- {porcentaje_vf}% preguntas de verdadero/falso
- {porcentaje_abiertas}% preguntas abiertas

Para cada pregunta proporciona:
1. Tipo de pregunta
2. Enunciado claro
3. Opciones (si aplica)
4. Respuesta correcta
5. Explicación concisa
6. Nivel de dificultad (básico, intermedio, avanzado)

Formato de salida (JSON válido):
{{
  "cuestionario": [
    {{
      "tipo": "opcion_multiple|verdadero_falso|pregunta_abierta",
      "enunciado": "...",
      "opciones": ["...", "...", "...", "..."],
      "respuesta_correcta": "...",
      "explicacion": "...",
      "dificultad": "..."
    }}
  ],
  "metadata": {{
    "temas_principales": ["..."],
    "total_preguntas": "..."
  }}
}}"""
}