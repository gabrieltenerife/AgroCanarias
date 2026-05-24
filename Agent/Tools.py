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
    return retriever.invoke(pregunta)


@tool()
def verificar_cuaderno():
    """Audita un cuaderno de campo para comprobar si cumpliria una auditoria.

    Pasos a seguir:
    1. Buscar en /home/inta/Documentos el archivo del cuaderno
       (por ejemplo: modelo_de_cuaderno_de_explotacion.doc).
    2. Si el archivo esta en formato .doc, utilizar la herramienta convertir_doc
       para convertirlo a markdown.
    3. Leer el contenido del archivo convertido y razonar sobre el
       para evaluar si cumple los requisitos de una auditoria."""


@tool()
def convertir_doc(ruta_docx: str):
    "convierte un documento de doc a docx a markdown para que el agente pueda leerlo e interpretarlo."
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'docx',
        ruta_docx, '--outdir', os.path.dirname(ruta_docx)
    ], check=True)
    ruta_docx_convertido = os.path.splitext(ruta_docx)[0] + '.docx'
    ruta_md = os.path.splitext(ruta_docx_convertido)[0] + '.md'
    pypandoc.convert_file(ruta_docx_convertido, 'gfm', outputfile=ruta_md)
    return ruta_md


@tool()
def obtener_fecha():
    "Devuelve la fecha actual en formato DD/MM/YYYY. Usar esta herramienta para responder a preguntas sobre la fecha actual o para calcular plazos a partir de la fecha de hoy."
    return dt.datetime.now().strftime("%d/%m/%Y")


def obtener_tools():
    return [
        obtener_info_rag,
        verificar_cuaderno,
        convertir_doc,
        obtener_fecha
    ]
