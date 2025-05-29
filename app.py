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

def generar_pdf(quiz, filename="cuestionario.pdf"):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50

    max_width = width - 100  # margen derecho e izquierdo

    def draw_wrapped_text(c, text, x, y, font_name, font_size, max_width, line_height):
        c.setFont(font_name, font_size)
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                c.drawString(x, y, line)
                y -= line_height
                line = word
        if line:
            c.drawString(x, y, line)
            y -= line_height
        return y

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Cuestionario generado automáticamente")
    y -= 40

    for i, pregunta in enumerate(quiz["cuestionario"], 1):
        c.setFont("Helvetica-Bold", 12)
        y = draw_wrapped_text(c, f"{i}. {pregunta.get('enunciado', '')}", 50, y, "Helvetica-Bold", 12, max_width, 15)

        if pregunta.get("tipo") == "opcion_multiple":
            c.setFont("Helvetica", 11)
            for j, opcion in enumerate(pregunta.get("opciones", [])):
                y = draw_wrapped_text(c, f"{chr(65+j)}. {opcion}", 70, y, "Helvetica", 11, max_width, 13)

        c.setFont("Helvetica-Oblique", 11)
        if pregunta.get("tipo") == "pregunta_abierta":
            y = draw_wrapped_text(c, "Respuesta: [Respuesta abierta]", 70, y, "Helvetica-Oblique", 11, max_width, 13)
        else:
            y = draw_wrapped_text(c, f"Respuesta: {pregunta.get('respuesta_correcta', '')}", 70, y, "Helvetica-Oblique", 11, max_width, 13)

        explicacion = pregunta.get("explicacion", "")
        if explicacion:
            c.setFont("Helvetica", 10)
            y = draw_wrapped_text(c, f"Explicación: {explicacion}", 70, y, "Helvetica", 10, max_width, 12)
            y -= 10
        else:
            y -= 10

        if y < 100:
            c.showPage()
            y = height - 50

    c.save()

def main():
    st.sidebar.header("⚙️ Configuración")
    num_preguntas = st.sidebar.slider("Número de preguntas", 3, 20, 5)
    tipo_preguntas = st.sidebar.radio(
        "Distribución de preguntas",
        ["Mixto", "Opción múltiple", "Verdadero/Falso", "Pregunta abierta"],
        help="Selecciona el tipo de preguntas que deseas generar"
    )
    tema_estudio = st.sidebar.text_input("Tema de estudio (opcional)", 
                                         placeholder="Ej: Historia del Renacimiento",
                                         help="Especifica el tema principal para enfocar el cuestionario")

    uploaded_file = st.file_uploader("Sube tu documento académico (PDF)", type="pdf")

    if uploaded_file:
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        try:
            with st.spinner("Procesando documento..."):
                processor = DocumentProcessor()
                chunks = processor.load_and_split(temp_path)

            if chunks:
                st.success("✅ Documento procesado correctamente. Base de conocimiento lista.")

                # Crear la base de conocimiento y guardarla en sesión para usar después
                if "vector_db" not in st.session_state:
                    with st.spinner("Creando base de conocimiento..."):
                        db = VectorDatabase()
                        st.session_state.vector_db = db.create_db(chunks, "quiz_temp")

        except Exception as e:
            st.error(f"❌ Error al procesar: {str(e)}")

        # Si la base de conocimiento ya está creada:
        if "vector_db" in st.session_state:
            if st.button("🎛️ Generar cuestionario"):
                with st.spinner("Generando cuestionario..."):
                    generator = QuizGenerator(st.session_state.vector_db.as_retriever())

                    if tipo_preguntas == "Opción múltiple":
                        percentages = (100, 0, 0)
                    elif tipo_preguntas == "Verdadero/Falso":
                        percentages = (0, 100, 0)
                    elif tipo_preguntas == "Pregunta abierta":
                        percentages = (0, 0, 100)
                    else:
                        percentages = (33, 33, 33)

                    quiz = generator.generate_quiz(
                        topic=tema_estudio if tema_estudio else "contenido del documento",
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
                                if pregunta.get("tipo") == "pregunta_abierta":
                                    st.markdown("**Respuesta:** [Respuesta abierta]")
                                else:
                                    st.markdown(f"**Respuesta:** {pregunta.get('respuesta_correcta', '')}")
                                st.markdown(f"**Explicación:** {pregunta.get('explicacion', '')}")

                        generar_pdf(quiz)
                        with open("cuestionario.pdf", "rb") as pdf_file:
                            st.download_button(
                                label="📥 Descargar cuestionario (PDF)",
                                data=pdf_file,
                                file_name="cuestionario.pdf",
                                mime="application/pdf"
                            )
        # Limpieza
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    main()
