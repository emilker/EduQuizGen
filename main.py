import logging
from document_processor import DocumentProcessor
from vector_db import VectorDatabase
from quiz_generator import QuizGenerator
import argparse
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Generador de Cuestionarios Educativos")
    parser.add_argument("file", help="Ruta al archivo PDF educativo")
    parser.add_argument("-n", "--num_preguntas", type=int, default=5, help="Número de preguntas a generar")
    parser.add_argument("-t", "--tema", help="Tema principal (opcional)")
    args = parser.parse_args()
    
    # Paso 1: Procesar documento
    processor = DocumentProcessor()
    chunks = processor.load_and_split(args.file)
    if not chunks:
        return
    
    # Paso 2: Crear base de datos vectorial
    db = VectorDatabase()
    vector_db = db.create_db(chunks, "cuestionario_db")
    if not vector_db:
        return
    
    # Paso 3: Configurar generador
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    generator = QuizGenerator(retriever)
    
    # Paso 4: Generar cuestionario
    tema = args.tema if args.tema else "contenido educativo del documento"
    quiz = generator.generate_quiz(
        topic=tema,
        num_questions=args.num_preguntas,
        percentages=(40, 40, 20)
    )
    
    if quiz is None:
        print("\n❌ Error: No se generó ningún cuestionario (respuesta None)")
        return
        
    if "error" in quiz:
        print(f"\n⚠️ Error en la generación: {quiz['error']}")
        if "raw_response" in quiz:
            print("\n💬 Respuesta cruda del modelo:")
            print(quiz["raw_response"])
        return
    
    print("\n✅ CUESTIONARIO GENERADO CON ÉXITO")
    print(f"📚 Temas cubiertos: {', '.join(quiz.get('metadata', {}).get('temas_cubiertos', ['No especificados']))}")
    print(f"📊 Total preguntas: {len(quiz.get('cuestionario', []))}")
    print("="*50)
    
    for i, pregunta in enumerate(quiz.get("cuestionario", []), 1):
        print(f"\n🔍 Pregunta {i} | Tipo: {pregunta.get('tipo', 'sin tipo').upper()} | Dificultad: {pregunta.get('dificultad', 'sin nivel').upper()}")
        
        if pregunta.get("incompleta", False):
            print("⚠️ [ADVERTENCIA: Estructura incompleta]")
        
        print(f"\n📝 {pregunta.get('enunciado', 'Sin enunciado')}")
        
        if pregunta.get("tipo") == "opcion_multiple":
            print("\nOpciones:")
            for j, opcion in enumerate(pregunta.get("opciones", [])):
                print(f"   {chr(97+j)}) {opcion}")
        
        print(f"\n✅ Respuesta correcta: {pregunta.get('respuesta_correcta', 'No especificada')}")
        print(f"📚 Explicación: {pregunta.get('explicacion', 'No proporcionada')}")
        print("-"*50)

    # Opcional: Guardar en archivo
    guardar = input("\n¿Deseas guardar el cuestionario en un archivo JSON? (s/n): ")
    if guardar.lower() == 's':
        with open('cuestionario_generado.json', 'w', encoding='utf-8') as f:
            json.dump(quiz, f, ensure_ascii=False, indent=2)
        print("💾 Cuestionario guardado como 'cuestionario_generado.json'")

if __name__ == "__main__":
    main()