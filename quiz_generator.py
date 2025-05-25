import json
import logging
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from config import CONFIG

logger = logging.getLogger(__name__)

class QuizGenerator:
    def __init__(self, retriever):
        self.llm = ChatOllama(
            model=CONFIG["MODELO_LLM"],
            temperature=0.7,
            format="json",
            timeout=60  # Aumentar timeout
        )
        self.retriever = retriever
        self.output_parser = StrOutputParser()
        
        # Plantilla optimizada para generación de cuestionarios
        self.prompt_template = """Eres un experto generador de cuestionarios educativos. 
Basándote EXCLUSIVAMENTE en el siguiente contexto:

{context}

Genera exactamente {num_preguntas} preguntas con esta distribución:
- {porcentaje_op_multiple}% preguntas de opción múltiple (4 opciones, 1 correcta)
- {porcentaje_vf}% preguntas de verdadero/falso
- {porcentaje_abiertas}% preguntas abiertas

Instrucciones:
1. Las preguntas deben ser claras y relevantes al contexto
2. Para opción múltiple, incluir 4 opciones (solo una correcta)
3. Proporcionar explicación para cada respuesta
4. Indicar nivel de dificultad (básico, intermedio, avanzado)

Formato de respuesta (SOLO JSON válido):
{{
  "cuestionario": [
    {{
      "tipo": "opcion_multiple|verdadero_falso|pregunta_abierta",
      "enunciado": "texto completo de la pregunta",
      "opciones": ["op1", "op2", "op3", "op4"],  // solo para opción múltiple
      "respuesta_correcta": "respuesta exacta",
      "explicacion": "explicación detallada",
      "dificultad": "básico|intermedio|avanzado"
    }}
  ],
  "metadata": {{
    "temas_cubiertos": ["tema1", "tema2"],
    "total_preguntas": {num_preguntas}
  }}
}}"""

        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
        
        # Cadena optimizada para evitar problemas de embedding
        self.chain = (
            {
                "context": lambda x: self._get_context(x["topic"]),
                "num_preguntas": RunnablePassthrough(),
                "porcentaje_op_multiple": RunnablePassthrough(),
                "porcentaje_vf": RunnablePassthrough(),
                "porcentaje_abiertas": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | self.output_parser
        )
    
    def _get_context(self, topic):
        """Obtiene contexto relevante manejando posibles errores"""
        try:
            docs = self.retriever.get_relevant_documents(topic)
            return "\n\n".join(doc.page_content for doc in docs)
        except Exception as e:
            logger.error(f"Error obteniendo contexto: {str(e)}")
            return f"Contexto sobre {topic} no disponible"
    
    def generate_quiz(self, topic, num_questions=5, percentages=(50, 30, 20)):
        """Genera un cuestionario educativo"""
        if num_questions > CONFIG["MAX_PREGUNTAS"]:
            num_questions = CONFIG["MAX_PREGUNTAS"]
            logger.warning(f"Número de preguntas reducido a {CONFIG['MAX_PREGUNTAS']}")
        
        try:
            # Preparar inputs como strings
            inputs = {
                "topic": str(topic),
                "num_preguntas": str(num_questions),
                "porcentaje_op_multiple": str(percentages[0]),
                "porcentaje_vf": str(percentages[1]),
                "porcentaje_abiertas": str(percentages[2])
            }
            
            logger.info("Generando cuestionario...")
            result = self.chain.invoke(inputs)
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"Error crítico generando cuestionario: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "detalle": "Falló la generación del cuestionario"
            }
    
    def _parse_result(self, raw_result):
        """Procesa y valida la respuesta del modelo"""
        try:
            # Limpieza del resultado
            cleaned = raw_result.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()
        
            # Parsear y validar
            data = json.loads(cleaned)
        
            if not isinstance(data, dict) or "cuestionario" not in data:
                raise ValueError("Formato de respuesta inválido")
            
            # Validación más flexible de preguntas
            for pregunta in data["cuestionario"]:
                required_fields = ["tipo", "enunciado", "respuesta_correcta"]
                if not all(key in pregunta for key in required_fields):
                    # Marcar pregunta incompleta pero no fallar todo
                    pregunta["incompleta"] = True
                    logger.warning(f"Pregunta incompleta: {pregunta.get('enunciado', 'sin texto')}")
        
            return data
        except json.JSONDecodeError as je:
            logger.error(f"Error decodificando JSON: {str(je)}")
            return {
                "error": "Respuesta no es JSON válido",
                "raw_response": raw_result
            }
        except Exception as e:
            logger.error(f"Error validando cuestionario: {str(e)}")
            return {
                "error": str(e),
                "raw_response": raw_result
            }