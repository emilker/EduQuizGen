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
            timeout=60
        )
        self.retriever = retriever
        self.output_parser = StrOutputParser()

        # Prompts dedicados
        self.prompt_mixto = ChatPromptTemplate.from_template("""
Eres un experto generador de cuestionarios educativos.
Basándote EXCLUSIVAMENTE en este contexto:

{context}
                                                             
Si el contexto está vacío o no contiene información sobre el tema solicitado, devuelve el siguiente JSON:
{{
  "cuestionario": [],
  "metadata": {{
    "temas_cubiertos": [],
    "total_preguntas": 0,
    "mensaje": "No se encontró información suficiente sobre el tema solicitado."
  }}
}}

De lo contrario, Genera exactamente {num_preguntas} preguntas con esta distribución:
- {porcentaje_op_multiple}% preguntas de opción múltiple (4 opciones, 1 correcta)
- {porcentaje_vf}% preguntas de verdadero/falso
- {porcentaje_abiertas}% preguntas abiertas

Si algún porcentaje es 0%, no generes preguntas de ese tipo.

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
""")

        self.prompt_opcion_multiple = ChatPromptTemplate.from_template("""
Eres un experto generador de cuestionarios educativos.
Basándote EXCLUSIVAMENTE en este contexto:

{context}

Si el contexto está vacío o no contiene información sobre el tema solicitado, devuelve el siguiente JSON:
{{
  "cuestionario": [],
  "metadata": {{
    "temas_cubiertos": [],
    "total_preguntas": 0,
    "mensaje": "No se encontró información suficiente sobre el tema solicitado."
  }}
}}

De lo contrario, Genera exactamente {num_preguntas} preguntas de opción múltiple.
Cada pregunta debe tener 4 opciones (solo una correcta), con explicación y dificultad.

Formato de respuesta (SOLO JSON válido):
{{
  "cuestionario": [
    {{
      "tipo": "opcion_multiple",
      "enunciado": "texto completo de la pregunta",
      "opciones": ["op1", "op2", "op3", "op4"], 
      "respuesta_correcta": "opción correcta",
      "explicacion": "explicación detallada",
      "dificultad": "básico|intermedio|avanzado"
    }}
  ],
  "metadata": {{
    "temas_cubiertos": ["tema1", "tema2"],
    "total_preguntas": {num_preguntas}
  }} }}
""")

        self.prompt_verdadero_falso = ChatPromptTemplate.from_template("""
Eres un experto generador de cuestionarios educativos.
Basándote EXCLUSIVAMENTE en este contexto:

{context}

Si el contexto está vacío o no contiene información sobre el tema solicitado, devuelve el siguiente JSON:
{{
  "cuestionario": [],
  "metadata": {{
    "temas_cubiertos": [],
    "total_preguntas": 0,
    "mensaje": "No se encontró información suficiente sobre el tema solicitado."
  }}
}}

De lo contrario, Genera exactamente {num_preguntas} preguntas de verdadero o falso.
Cada pregunta debe tener respuesta correcta, explicación y dificultad.

Formato de respuesta (SOLO JSON válido):
{{
  "cuestionario": [
    {{
      "tipo": "verdadero_falso",
      "enunciado": "texto completo de la afirmación",
      "respuesta_correcta": "Verdadero|Falso",
      "explicacion": "explicación detallada",
      "dificultad": "básico|intermedio|avanzado"
    }}
  ],
  "metadata": {{
    "temas_cubiertos": ["tema1", "tema2"],
    "total_preguntas": {num_preguntas}
  }} }}
""")

        self.prompt_abiertas = ChatPromptTemplate.from_template("""
Eres un experto generador de cuestionarios educativos.
Basándote EXCLUSIVAMENTE en este contexto:

{context}

Si el contexto está vacío o no contiene información sobre el tema solicitado, devuelve el siguiente JSON:
{{
  "cuestionario": [],
  "metadata": {{
    "temas_cubiertos": [],
    "total_preguntas": 0,
    "mensaje": "No se encontró información suficiente sobre el tema solicitado."
  }}
}}

De lo contrario, Genera exactamente {num_preguntas} preguntas abiertas.
Cada pregunta debe tener una respuesta modelo, explicación y dificultad.

Formato de respuesta (SOLO JSON válido):
{{
  "cuestionario": [
    {{
      "tipo": "pregunta_abierta",
      "enunciado": "texto completo de la pregunta abierta",
      "respuesta_correcta": "respuesta modelo esperada",
      "explicacion": "explicación detallada",
      "dificultad": "básico|intermedio|avanzado"
    }}
  ],
  "metadata": {{
    "temas_cubiertos": ["tema1", "tema2"],
    "total_preguntas": {num_preguntas}
  }} }}
""")

    def _get_context(self, topic):
        try:
            docs = self.retriever.invoke(topic)
            if not docs:
                return ""
            return "\n\n".join(doc.page_content for doc in docs)
        except Exception as e:
            logger.error(f"Error obteniendo contexto: {str(e)}")
            return ""

    def generate_quiz(self, topic, num_questions=5, percentages=(50, 30, 20)):
        if num_questions > CONFIG["MAX_PREGUNTAS"]:
            num_questions = CONFIG["MAX_PREGUNTAS"]
            logger.warning(f"Número de preguntas reducido a {CONFIG['MAX_PREGUNTAS']}")

        try:
            context = self._get_context(topic)
            p_op, p_vf, p_ab = percentages

            # Seleccionamos prompt según distribución
            if p_op == 100:
                prompt = self.prompt_opcion_multiple
                prompt_inputs = {
                    "context": context,
                    "num_preguntas": str(num_questions)
                }
            elif p_vf == 100:
                prompt = self.prompt_verdadero_falso
                prompt_inputs = {
                    "context": context,
                    "num_preguntas": str(num_questions)
                }
            elif p_ab == 100:
                prompt = self.prompt_abiertas
                prompt_inputs = {
                    "context": context,
                    "num_preguntas": str(num_questions)
                }
            else:
                # Mixto
                prompt = self.prompt_mixto
                prompt_inputs = {
                    "context": context,
                    "num_preguntas": str(num_questions),
                    "porcentaje_op_multiple": str(p_op),
                    "porcentaje_vf": str(p_vf),
                    "porcentaje_abiertas": str(p_ab)
                }

            logger.info("Generando cuestionario...")
            formatted_prompt = prompt.format(**prompt_inputs)
            result = self.llm.invoke(formatted_prompt)
            return self._parse_result(self.output_parser.invoke(result))

        except Exception as e:
            logger.error(f"Error generando cuestionario: {str(e)}", exc_info=True)
            return {"error": str(e), "detalle": "Falló la generación del cuestionario"}

    def _parse_result(self, raw_result):
        try:
            cleaned = raw_result.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3].strip()

            data = json.loads(cleaned)
            if not isinstance(data, dict) or "cuestionario" not in data:
                raise ValueError("Formato inválido")

            return data
        except json.JSONDecodeError as je:
            logger.error(f"Error JSON: {je}")
            return {"error": "JSON inválido", "raw_response": raw_result}
        except Exception as e:
            logger.error(f"Error validando cuestionario: {e}")
            return {"error": str(e), "raw_response": raw_result}