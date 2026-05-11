import os
import subprocess

import pypandoc
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from Rag.Retriever import buscar_documentos, format_resultados


def _buscar(query: str, filtros: dict = None) -> str:
    try:
        docs = buscar_documentos(query, filtros, k=4)
    except Exception as e:
        return f"Error en la base de datos: {e}"
    if not docs:
        return f"No se encontro informacion para la consulta: '{query}'."
    return format_resultados(docs)


@tool()
def obtener_info_rag(pregunta: str):
    """Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante."""
    return _buscar(pregunta)


class BuscarFitosanitariosInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo afectado."
    )
    problema: str = Field(
        description="Plaga, enfermedad o mala hierba. Ej: 'sigatoka negra', 'tuta absoluta', 'fusarium'."
    )
    tipo_produccion: Literal["convencional", "integrada", "ecologica"] = Field(
        description="Modalidad de produccion. Cambia radicalmente que productos estan autorizados."
    )
    fase_cultivo: Optional[Literal["floracion", "pre_cosecha", "vegetativo"]] = Field(
        default=None,
        description="Fase del cultivo. Algunos productos no se pueden aplicar en floracion por toxicidad para polinizadores."
    )


class BuscarAyudasInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo principal de la explotacion."
    )
    isla: Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ] = Field(description="Isla donde esta la explotacion. Algunas ayudas son especificas por isla o cabildo.")
    tipo_explotacion: Literal["convencional", "ecologica", "integrada"] = Field(
        description="Modalidad de produccion de la explotacion."
    )
    situacion: Optional[Literal["nuevo_agricultor", "agricultor_joven", "cooperativa", "exportador"]] = Field(
        default=None,
        description="Situacion especial del solicitante. Desbloquea categorias especificas de ayudas."
    )
    superficie_ha: Optional[float] = Field(
        default=None,
        description="Superficie en hectareas. Algunas ayudas tienen umbrales minimos o maximos."
    )


class RegistrarTratamientoInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo tratado."
    )
    parcela: str = Field(
        description="Identificador de la parcela (referencia SIGPAC o nombre propio)."
    )
    fecha: str = Field(
        description="Fecha de aplicacion en formato DD/MM/AAAA."
    )
    producto: str = Field(
        description="Nombre comercial del producto aplicado."
    )
    dosis: str = Field(
        description="Dosis aplicada con unidades. Ej: '1,5 L/ha'."
    )
    motivo: str = Field(
        description="Plaga, enfermedad o causa que justifica el tratamiento."
    )
    superficie: float = Field(
        description="Hectareas tratadas."
    )
    maquinaria: Optional[str] = Field(
        default=None,
        description="Equipo de aplicacion. Obligatorio en algunos tipos de inspeccion."
    )


class VerificarCuadernoInput(BaseModel):
    registros: List[dict] = Field(
        description="Entradas del cuaderno del periodo a revisar en formato JSON."
    )
    tipo_certificacion: Literal["convencional", "integrada", "ecologica", "globalGAP"] = Field(
        description="Certificacion a auditar. Cada una tiene requisitos distintos."
    )
    periodo: str = Field(
        description="Periodo a auditar. Ej: '2024-Q1' o '2024-01-01/2024-06-30'."
    )


class CalcularPlazosInput(BaseModel):
    tipo_tramite: Literal[
        "posei", "pac", "ecologica_conversion",
        "renovacion_dop", "certificado_fitosanitario", "auditoria_globalGAP"
    ] = Field(description="Tramite sobre el que calcular el plazo.")
    fecha_referencia: Optional[str] = Field(
        default=None,
        description="Fecha base para el calculo en formato DD/MM/AAAA. Por defecto usa la fecha actual."
    )
    isla: Optional[Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ]] = Field(
        default=None,
        description="Algunas convocatorias tienen plazos distintos por isla o delegacion territorial."
    )


class VerificarCumplimientoDopInput(BaseModel):
    dop: Literal["platano_canarias", "papas_antiguas", "miel_tenerife", "vino_denominacion"] = Field(
        description="Denominacion de Origen o IGP a verificar."
    )
    practica: str = Field(
        description="Descripcion de la practica agricola a verificar. Ej: 'usar portainjertos Grande Naine en nuevas plantaciones'."
    )


class RequisitosExportacionInput(BaseModel):
    producto: str = Field(
        description="Producto a exportar. Ej: 'platano', 'tomate cherry', 'papa nueva'."
    )
    mercado_destino: Literal["union_europea", "reino_unido", "eeuu", "otros"] = Field(
        description="Pais o mercado de destino. UK tiene requisitos especiales post-Brexit."
    )
    tipo_certificacion: Optional[Literal["convencional", "ecologico", "DOP"]] = Field(
        default=None,
        description="Tipo de certificacion del producto. Cambia los documentos requeridos."
    )


class AlertasEnfermedadesInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo de interes."
    )
    isla: Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ] = Field(description="Las alertas son especificas por zona geografica.")
    incluir_web: bool = Field(
        default=True,
        description="Si True, complementa con busqueda en ASAJA Canarias, Gobierno de Canarias y MAPA para alertas recientes no ingestadas."
    )


@tool("consultar_fitosanitarios", args_schema=BuscarFitosanitariosInput)
def tool_buscar_fitosanitarios(
    cultivo: str,
    problema: str,
    tipo_produccion: str,
    fase_cultivo: Optional[str] = None
) -> str:
    """
    Busca productos fitosanitarios autorizados para un cultivo y plaga concretos.
    Devuelve materia activa, dosis maxima, numero maximo de aplicaciones por campana,
    plazo de seguridad (dias antes de cosecha) y observaciones especiales.
    Usar cuando el agricultor pregunta que puede aplicar para una plaga o enfermedad.
    """
    query = f"{problema} en {cultivo} produccion {tipo_produccion}"
    if fase_cultivo:
        query += f" fase {fase_cultivo}"
    filtros = {"categoria": "fitosanitario", "cultivo": cultivo, "tipo_produccion": tipo_produccion}
    return _buscar(query, filtros)


@tool("buscar_ayudas", args_schema=BuscarAyudasInput)
def tool_buscar_ayudas(
    cultivo: str,
    isla: str,
    tipo_explotacion: str,
    situacion: Optional[str] = None,
    superficie_ha: Optional[float] = None
) -> str:
    """
    Busca ayudas y subvenciones aplicables (POSEI, PAC, Gobierno de Canarias, Cabildos, FEDER)
    cruzando el perfil del agricultor con las convocatorias disponibles.
    Devuelve nombre, organismo convocante, importe aproximado, documentacion necesaria y plazo.
    Usar cuando el agricultor pregunta por ayudas, subvenciones o el POSEI.
    """
    query = f"ayudas subvenciones {cultivo} {tipo_explotacion} {isla}"
    if situacion:
        query += f" {situacion}"
    if superficie_ha:
        query += f" {superficie_ha} hectareas"
    filtros = {"categoria": "ayuda", "cultivo": cultivo, "isla": isla, "tipo_produccion": tipo_explotacion}
    return _buscar(query, filtros)


@tool("registrar_tratamiento", args_schema=RegistrarTratamientoInput)
def tool_registrar_tratamiento(
    cultivo: str,
    parcela: str,
    fecha: str,
    producto: str,
    dosis: str,
    motivo: str,
    superficie: float,
    maquinaria: Optional[str] = None
) -> str:
    """
    Genera la entrada del cuaderno de campo correctamente formateada conforme al RD 1311/2012.
    Calcula automaticamente la fecha de re-entrada a la parcela y la fecha minima de cosecha
    segun el plazo de seguridad del producto. Verifica que el producto este autorizado para ese cultivo.
    Usar cuando el agricultor quiere registrar un tratamiento fitosanitario aplicado.
    """
    query = f"plazo seguridad re-entrada {producto} en {cultivo} cuaderno campo RD 1311/2012"
    filtros = {"categoria": "cuaderno", "cultivo": cultivo}
    return _buscar(query, filtros)


@tool("verificar_cuaderno", args_schema=VerificarCuadernoInput)
def tool_verificar_cuaderno(
    registros: List[dict],
    tipo_certificacion: str,
    periodo: str
) -> str:
    """
    Revisa si el cuaderno de campo esta completo y correcto para superar una auditoria.
    Devuelve informe de cumplimiento con entradas incompletas, campos faltantes por entrada
    y valoracion general de si el cuaderno superaria una auditoria estandar.
    Usar antes de inspecciones GlobalG.A.P., certificacion ecologica o revision DOP.
    Si el usuario no proporciona la ubicacion del archivo, debes de preguntar por esta.
    En todos los casos el formato del archivo sera .doc, por lo que debes de utilizar la herramienta
    convertir_doc para convertirlo de doc a docx y a markdown y luego analizar su contenido.

    Los pasos a seguir son:
    1. Preguntar al usuario por la ubicacion del archivo (si no la proporciona) .docx del cuaderno de campo y localizarlo.
    2. Utilizar la herramienta convertir_doc para convertir el archivo a markdown.
    3. Analizar el contenido del markdown y verificar que cumple con los requisitos de la certificacion indicada.
    """
    query = f"requisitos cuaderno de campo campos obligatorios auditoria {tipo_certificacion}"
    filtros = {"categoria": "cuaderno", "tipo_certificacion": tipo_certificacion}
    return _buscar(query, filtros)


@tool("calcular_plazos", args_schema=CalcularPlazosInput)
def tool_calcular_plazos(
    tipo_tramite: str,
    fecha_referencia: Optional[str] = None,
    isla: Optional[str] = None
) -> str:
    """
    Calcula plazos criticos de tramites agricolas: POSEI, PAC, conversion ecologica,
    renovacion DOP, certificado fitosanitario, auditoria GlobalG.A.P.
    Devuelve fecha limite, dias restantes, documentos a preparar y pasos previos necesarios.
    Usar cuando el agricultor pregunta por fechas limite o cuando tiene que solicitar algo.
    """
    query = f"plazo fecha limite documentacion {tipo_tramite}"
    if isla:
        query += f" {isla}"
    filtros = {"categoria": "ayuda", "isla": isla}
    return _buscar(query, filtros)


@tool("verificar_cumplimiento_dop", args_schema=VerificarCumplimientoDopInput)
def tool_verificar_cumplimiento_dop(
    dop: str,
    practica: str
) -> str:
    """
    Verifica si una practica agricola concreta es compatible con el pliego de condiciones
    de una DOP o IGP. Devuelve si es conforme, no conforme o requiere consulta al Consejo
    Regulador, con el articulo exacto del pliego que lo regula.
    Usar cuando el agricultor pregunta si puede hacer algo y mantener la DOP.
    """
    query = f"{practica} pliego condiciones {dop} conformidad"
    filtros = {"categoria": "dop", "dop": dop}
    return _buscar(query, filtros)


@tool("requisitos_exportacion", args_schema=RequisitosExportacionInput)
def tool_requisitos_exportacion(
    producto: str,
    mercado_destino: str,
    tipo_certificacion: Optional[str] = None
) -> str:
    """
    Devuelve la lista completa de documentos necesarios para exportar a un mercado concreto:
    certificado fitosanitario, certificado de origen, analisis de residuos, etiquetado,
    organismo emisor, coste aproximado, tiempo de tramitacion y LMR aplicables.
    Atencion especial al Reino Unido: requisitos PHYTO y puntos de control fronterizos post-Brexit.
    Usar cuando el agricultor o responsable de exportacion pregunta que necesita para exportar.
    """
    query = f"requisitos exportacion documentacion {producto} {mercado_destino}"
    if tipo_certificacion:
        query += f" {tipo_certificacion}"
    filtros = {"categoria": "exportacion", "mercado_destino": mercado_destino}
    return _buscar(query, filtros)


@tool("alertas_plagas_enfermedades", args_schema=AlertasEnfermedadesInput)
def tool_alertas_plagas_enfermedades(
    cultivo: str,
    isla: str,
    incluir_web: bool = True
) -> str:
    """
    Devuelve alertas fitosanitarias activas para un cultivo e isla concretos:
    organismos causantes, sintomas de identificacion, umbral de tratamiento recomendado
    y metodos de control disponibles.
    Siempre complementa con busquedas en internet, tanto en ASAJA Canarias, como Gobierno de Canarias
    y MAPA para incluir alertas recientes no ingestadas en la base de conocimiento. Al realizar busquedas en internet,
    asegurate de anadir la fecha de la alerta y la fuente de la informacion.
    Usar cuando el agricultor pregunta por plagas activas o riesgos fitosanitarios actuales.
    """
    query = f"alerta plaga enfermedad {cultivo} {isla} activa tratamiento"
    filtros = {"categoria": "fitosanitario", "cultivo": cultivo, "isla": isla}
    return _buscar(query, filtros)


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


def obtener_filtros_rag():
    return [
        tool_buscar_fitosanitarios,
        tool_buscar_ayudas,
        tool_registrar_tratamiento,
        tool_calcular_plazos,
        tool_verificar_cumplimiento_dop,
        tool_requisitos_exportacion,
        tool_alertas_plagas_enfermedades,
    ]

def obtener_tools():
    return [
        obtener_info_rag,
        tool_verificar_cuaderno,
        convertir_doc
    ]