import streamlit as st
from document_processor import DocumentProcessor
from vector_db import VectorDatabase
from quiz_generator import QuizGenerator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import time

# Configuración Streamlit
st.set_page_config(
    page_title="Generador de Cuestionarios",
    page_icon="📚",
    layout="wide"
)

st.title("📝 Generador Automático de Cuestionarios")

# Función para generar PDF desde cuestionario
def generar_pdf(quiz, filename="cuestionario.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Cuestionario generado automáticamente")
    y -= 40

    for i, pregunta in enumerate(quiz["cuestionario"], 1):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{i}. {pregunta.get('enunciado', '')}")
        y -= 20

        if pregunta.get("tipo") == "opcion_multiple":
            c.setFont("Helvetica", 11)
            for j, opcion in enumerate(pregunta.get("opciones", [])):
                c.drawString(70, y, f"{chr(65+j)}. {opcion}")
                y -= 15

        c.setFont("Helvetica-Oblique", 11)
        c.drawString(70, y, f"Respuesta: {pregunta.get('respuesta_correcta', '')}")
        y -= 15

        explicacion = pregunta.get("explicacion", "")
        if explicacion:
            c.setFont("Helvetica", 10)
            c.drawString(70, y, f"Explicación: {explicacion}")
            y -= 30
        else:
            y -= 20

        if y < 100:
            c.showPage()
            y = height - 50

    c.save()

# Función principal
def main():
    with st.sidebar:
        st.header("⚙️ Configuración")
        num_preguntas = st.slider("Número de preguntas", 3, 20, 5)
        tipo_preguntas = st.radio(
            "Distribución de preguntas",
            ["Mixto", "Opción múltiple", "Verdadero/Falso"]
        )

    uploaded_file = st.file_uploader(
        "Sube tu documento académico (PDF)",
        type="pdf"
    )

    if uploaded_file:
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        try:
            with st.spinner("Procesando documento..."):
                processor = DocumentProcessor()
                chunks = processor.load_and_split(temp_path)

                if chunks:
                    with st.spinner("Creando base de conocimiento..."):
                        db = VectorDatabase()
                        vector_db = db.create_db(chunks, "quiz_temp")

                        if vector_db:
                            with st.spinner("Generando cuestionario..."):
                                generator = QuizGenerator(vector_db.as_retriever())

                                if tipo_preguntas == "Opción múltiple":
                                    percentages = (80, 10, 10)
                                elif tipo_preguntas == "Verdadero/Falso":
                                    percentages = (10, 80, 10)
                                else:
                                    percentages = (40, 40, 20)

                                quiz = generator.generate_quiz(
                                    topic="contenido del documento",
                                    num_questions=num_preguntas,
                                    percentages=percentages
                                )

                                if quiz and "cuestionario" in quiz:
                                    st.success("✅ Cuestionario generado con éxito!")
                                    st.divider()

                                    for i, pregunta in enumerate(quiz["cuestionario"], 1):
                                        with st.expander(f"Pregunta {i} - {pregunta.get('tipo', '')}"):
                                            st.markdown(f"**{pregunta.get('enunciado', '')}**")

                                            if pregunta.get("tipo") == "opcion_multiple":
                                                st.markdown("**Opciones:**")
                                                for j, opcion in enumerate(pregunta.get("opciones", [])):
                                                    st.markdown(f"{chr(65+j)}. {opcion}")

                                            st.markdown(f"**Respuesta:** {pregunta.get('respuesta_correcta', '')}")
                                            st.markdown(f"**Explicación:** {pregunta.get('explicacion', '')}")

                                    # Generar PDF
                                    generar_pdf(quiz)

                                    with open("cuestionario.pdf", "rb") as pdf_file:
                                        st.download_button(
                                            label="📥 Descargar cuestionario (PDF)",
                                            data=pdf_file,
                                            file_name="cuestionario.pdf",
                                            mime="application/pdf"
                                        )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    main()
