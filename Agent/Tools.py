import os
import subprocess
import datetime as dt

import pypandoc
from langchain.tools import tool
from Rag.Retriever import conectar_chroma


@tool()
def obtener_info_rag(pregunta: str):
    """Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente.
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion.
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante."""
    retriever = conectar_chroma()
    docs = retriever.invoke(pregunta)

    if not docs:
        return "No se encontró información relevante para esta consulta."

    return "\n\n---\n\n".join(doc.page_content for doc in docs)


@tool()
def verificar_cuaderno():
    """Audita un cuaderno de campo para comprobar si cumpliría una auditoría.
    Busca el archivo en C:\\Users\\gamba\\Documentos y verifica que los campos obligatorios
    estén preenchidos."""
    ruta_cuaderno = r"C:\Users\gamba\Documentos\modelo_de_cuaderno_de_explotacion.doc"
    directorio = os.path.dirname(ruta_cuaderno)

    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'docx',
        ruta_cuaderno, '--outdir', directorio
    ], check=True, capture_output=True)

    ruta_docx = os.path.splitext(ruta_cuaderno)[0] + '.docx'
    ruta_md = os.path.splitext(ruta_docx)[0] + '.md'
    pypandoc.convert_file(ruta_docx, 'gfm', outputfile=ruta_md)

    with open(ruta_md, 'r', encoding='utf-8') as f:
        contenido = f.read()

    lineas = [l.strip() for l in contenido.split('\n') if l.strip()]
    campos_vacios = []

    for i, linea in enumerate(lineas):
        if linea.endswith(':'):
            if i + 1 >= len(lineas):
                campos_vacios.append(linea)
            else:
                siguiente = lineas[i + 1].strip()
                if not siguiente or siguiente.startswith('#') or siguiente == linea:
                    campos_vacios.append(linea)

    if campos_vacios:
        return f"✗ Campos sin preencher: {', '.join(campos_vacios)}"
    return "✓ Cuaderno completo"

@tool()
def obtener_fecha():
    "Devuelve la fecha actual en formato DD/MM/YYYY. Usar esta herramienta para responder a preguntas sobre la fecha actual o para calcular plazos a partir de la fecha de hoy."
    return dt.datetime.now().strftime("%d/%m/%Y")


def obtener_tools():
    return [
        obtener_info_rag,
        verificar_cuaderno,
        obtener_fecha
    ]
