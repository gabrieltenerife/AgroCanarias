import os
import subprocess
import datetime as dt

import pypandoc
from langchain.tools import tool
from Rag.Retriever import conectar_chroma, get_fullpdf

GUIA_POR_DEFECTO = "guia_cuaderno.pdf"


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
def verificar_cuaderno(guia: str = GUIA_POR_DEFECTO):
    """Lee el cuaderno de campo y, junto con la guía de auditoría indicada, devuelve ambos contenidos para que los contrastes.

    El cuaderno está en C:\\Users\\gamba\\Documents\\modelo_de_cuaderno_de_explotacion.doc
    La guía se carga desde la colección de PDFs completos (Data/fullpdf/) por nombre exacto de archivo.

    Analiza el contenido devuelto y, comparándolo con los requisitos de la guía, identifica:

    1. Campos obligatorios que están vacíos o sin rellenar
    2. Campos con información incompleta o incoherente
    3. Secciones que faltan por completo

    Presenta el resultado en dos bloques claros:
    - ✓ Campos correctamente completados
    - ✗ Campos incompletos o vacíos (con una indicación de qué falta)

    Concluye con una valoración: si el cuaderno pasaría o no una auditoría y por qué, referenciando la guía.
    """

    ruta_cuaderno = "C:\\Users\\gamba\\Documents\\modelo_de_cuaderno_de_explotacion.doc"
    directorio = os.path.dirname(ruta_cuaderno)

    # .doc → .docx
    subprocess.run([
        r'C:\Program Files\LibreOffice\program\soffice.exe', '--headless', '--convert-to', 'docx',
        ruta_cuaderno, '--outdir', directorio
    ], check=True, capture_output=True)

    ruta_docx = os.path.splitext(ruta_cuaderno)[0] + '.docx'

    # .docx → .md
    ruta_md = os.path.splitext(ruta_docx)[0] + '.md'
    pypandoc.convert_file(ruta_docx, 'gfm', outputfile=ruta_md)

    with open(ruta_md, 'r', encoding='utf-8') as f:
        contenido_cuaderno = f.read()

    contenido_guia = get_fullpdf(guia)
    if not contenido_guia:
        return (
            f"Aviso: no se encontró la guía '{guia}' en la colección FullPDFs. "
            f"Asegúrate de haberla colocado en Data/fullpdf/ y re-ejecutado la ingestión.\n\n"
            f"=== CUADERNO DE CAMPO ===\n\n{contenido_cuaderno}"
        )

    return (
        f"=== GUÍA DE AUDITORÍA ({guia}) ===\n\n{contenido_guia}\n\n"
        f"=== CUADERNO DE CAMPO ===\n\n{contenido_cuaderno}"
    )


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
