import os
import subprocess

import pypandoc
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from Rag.Retriever import conectar_crhroma

retriever_base = conectar_crhroma()

# ==========================================
# BUSQUEDA RAG GENERAL (sin filtros)
# =========================================
@tool()
def obtener_info_rag(pregunta: str):

    """ Esta herramienta se encarga de conectar con ChromaDB, hacer la consulta y devolver la información relevante para el agente. 
    Todas las respuestas deben de responderse utilizando esta herramienta exclusivamente y sin inventar informacion. 
    Si la información no se encuentra en la base de datos, se debe responder con un mensaje claro indicando que no se encontró información relevante. """

    retriever = conectar_crhroma()
    return retriever.invoke(pregunta)

# ==========================================
# MOTOR BASE DE BÚSQUEDA CON FILTROS DINÁMICOS
# =========================================
def motor_busqueda_chroma(query: str, filtros_dict: dict = None) -> str:
    """
    Función genérica que maneja la comunicación con ChromaDB, 
    aplica cualquier filtro dinámico y formatea la salida.
    """
    # Aplicar filtros si existen
    if filtros_dict:
        # Limpiamos los filtros que sean None
        filtros_limpios = {k: v for k, v in filtros_dict.items() if v is not None}
        
        if len(filtros_limpios) == 1:
            retriever_base.search_kwargs = {"filter": filtros_limpios}
        elif len(filtros_limpios) > 1:
            condiciones = [{k: v} for k, v in filtros_limpios.items()]
            retriever_base.search_kwargs = {"filter": {"$and": condiciones}}
    else:
        retriever_base.search_kwargs = {}

    # Ejecutar búsqueda
    try:
        documentos = retriever_base.invoke(query)
    except Exception as e:
        return f"Error en la base de datos: {e}"
    
    # Formatear salida
    if not documentos:
        return f"No se encontró información para la consulta: '{query}'."
        
    resultados = [
        f"--- Doc {i+1} ---\nCat: {doc.metadata.get('categoria', 'N/A')} | Cultivo: {doc.metadata.get('cultivo', 'N/A')}\n{doc.page_content}"
        for i, doc in enumerate(documentos)
    ]
    return "\n\n".join(resultados)


# ==========================================
# SCHEMAS PYDANTIC
# ==========================================

class BuscarFitosanitariosInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo afectado."
    )
    problema: str = Field(
        description="Plaga, enfermedad o mala hierba. Ej: 'sigatoka negra', 'tuta absoluta', 'fusarium'."
    )
    tipo_produccion: Literal["convencional", "integrada", "ecologica"] = Field(
        description="Modalidad de producción. Cambia radicalmente qué productos están autorizados."
    )
    fase_cultivo: Optional[Literal["floracion", "pre_cosecha", "vegetativo"]] = Field(
        default=None,
        description="Fase del cultivo. Algunos productos no se pueden aplicar en floración por toxicidad para polinizadores."
    )


class BuscarAyudasInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo principal de la explotación."
    )
    isla: Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ] = Field(description="Isla donde está la explotación. Algunas ayudas son específicas por isla o cabildo.")
    tipo_explotacion: Literal["convencional", "ecologica", "integrada"] = Field(
        description="Modalidad de producción de la explotación."
    )
    situacion: Optional[Literal["nuevo_agricultor", "agricultor_joven", "cooperativa", "exportador"]] = Field(
        default=None,
        description="Situación especial del solicitante. Desbloquea categorías específicas de ayudas."
    )
    superficie_ha: Optional[float] = Field(
        default=None,
        description="Superficie en hectáreas. Algunas ayudas tienen umbrales mínimos o máximos."
    )


class RegistrarTratamientoInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo tratado."
    )
    parcela: str = Field(
        description="Identificador de la parcela (referencia SIGPAC o nombre propio)."
    )
    fecha: str = Field(
        description="Fecha de aplicación en formato DD/MM/AAAA."
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
        description="Hectáreas tratadas."
    )
    maquinaria: Optional[str] = Field(
        default=None,
        description="Equipo de aplicación. Obligatorio en algunos tipos de inspección."
    )


class VerificarCuadernoInput(BaseModel):
    registros: List[dict] = Field(
        description="Entradas del cuaderno del período a revisar en formato JSON."
    )
    tipo_certificacion: Literal["convencional", "integrada", "ecologica", "globalGAP"] = Field(
        description="Certificación a auditar. Cada una tiene requisitos distintos."
    )
    periodo: str = Field(
        description="Período a auditar. Ej: '2024-Q1' o '2024-01-01/2024-06-30'."
    )


class CalcularPlazosInput(BaseModel):
    tipo_tramite: Literal[
        "posei", "pac", "ecologica_conversion",
        "renovacion_dop", "certificado_fitosanitario", "auditoria_globalGAP"
    ] = Field(description="Trámite sobre el que calcular el plazo.")
    fecha_referencia: Optional[str] = Field(
        default=None,
        description="Fecha base para el cálculo en formato DD/MM/AAAA. Por defecto usa la fecha actual."
    )
    isla: Optional[Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ]] = Field(
        default=None,
        description="Algunas convocatorias tienen plazos distintos por isla o delegación territorial."
    )


class VerificarCumplimientoDopInput(BaseModel):
    dop: Literal["platano_canarias", "papas_antiguas", "miel_tenerife", "vino_denominacion"] = Field(
        description="Denominación de Origen o IGP a verificar."
    )
    practica: str = Field(
        description="Descripción de la práctica agrícola a verificar. Ej: 'usar portainjertos Grande Naine en nuevas plantaciones'."
    )


class RequisitosExportacionInput(BaseModel):
    producto: str = Field(
        description="Producto a exportar. Ej: 'platano', 'tomate cherry', 'papa nueva'."
    )
    mercado_destino: Literal["union_europea", "reino_unido", "eeuu", "otros"] = Field(
        description="País o mercado de destino. UK tiene requisitos especiales post-Brexit."
    )
    tipo_certificacion: Optional[Literal["convencional", "ecologico", "DOP"]] = Field(
        default=None,
        description="Tipo de certificación del producto. Cambia los documentos requeridos."
    )


class AlertasEnfermedadesInput(BaseModel):
    cultivo: Literal["platano", "tomate", "papa", "pimiento", "otros"] = Field(
        description="Cultivo de interés."
    )
    isla: Literal[
        "tenerife", "gran_canaria", "la_palma",
        "lanzarote", "fuerteventura", "la_gomera", "el_hierro"
    ] = Field(description="Las alertas son específicas por zona geográfica.")
    incluir_web: bool = Field(
        default=True,
        description="Si True, complementa con búsqueda en ASAJA Canarias, Gobierno de Canarias y MAPA para alertas recientes no ingestadas."
    )


# ==========================================
# TOOLS
# ==========================================

@tool("consultar_fitosanitarios", args_schema=BuscarFitosanitariosInput)
def tool_buscar_fitosanitarios(
    cultivo: str,
    problema: str,
    tipo_produccion: str,
    fase_cultivo: Optional[str] = None
) -> str:
    """
    Busca productos fitosanitarios autorizados para un cultivo y plaga concretos.
    Devuelve materia activa, dosis máxima, número máximo de aplicaciones por campaña,
    plazo de seguridad (días antes de cosecha) y observaciones especiales.
    Usar cuando el agricultor pregunta qué puede aplicar para una plaga o enfermedad.
    """
    query = f"{problema} en {cultivo} producción {tipo_produccion}"
    if fase_cultivo:
        query += f" fase {fase_cultivo}"

    filtros = {
        "categoria": "fitosanitario",
        "cultivo": cultivo,
        "tipo_produccion": tipo_produccion
    }
    return motor_busqueda_chroma(query, filtros)


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
    Devuelve nombre, organismo convocante, importe aproximado, documentación necesaria y plazo.
    Usar cuando el agricultor pregunta por ayudas, subvenciones o el POSEI.
    """
    query = f"ayudas subvenciones {cultivo} {tipo_explotacion} {isla}"
    if situacion:
        query += f" {situacion}"
    if superficie_ha:
        query += f" {superficie_ha} hectáreas"

    filtros = {
        "categoria": "ayuda",
        "cultivo": cultivo,
        "isla": isla,
        "tipo_produccion": tipo_explotacion
    }
    return motor_busqueda_chroma(query, filtros)


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
    Calcula automáticamente la fecha de re-entrada a la parcela y la fecha mínima de cosecha
    según el plazo de seguridad del producto. Verifica que el producto esté autorizado para ese cultivo.
    Usar cuando el agricultor quiere registrar un tratamiento fitosanitario aplicado.
    """
    query = f"plazo seguridad re-entrada {producto} en {cultivo} cuaderno campo RD 1311/2012"

    filtros = {
        "categoria": "cuaderno",
        "cultivo": cultivo
    }
    return motor_busqueda_chroma(query, filtros)


@tool("verificar_cuaderno", args_schema=VerificarCuadernoInput)
def tool_verificar_cuaderno(
    registros: List[dict],
    tipo_certificacion: str,
    periodo: str
) -> str:
    """
    Revisa si el cuaderno de campo está completo y correcto para superar una auditoría.
    Devuelve informe de cumplimiento con entradas incompletas, campos faltantes por entrada
    y valoración general de si el cuaderno superaría una auditoría estándar.
    Usar antes de inspecciones GlobalG.A.P., certificación ecológica o revisión DOP.
    Si el usuario no proporciona la ubicaccion del archivo, debes de preguntar por esta.
    En todos los casos el formato del archivo sera .docc, por lo que debes de utilizar la herramienta 
    convertir_doc para convertirlo de doc a docx y a markdown y luego analizar su contenido.
    
    Los pasos a seguir son:
    1. Preguntar al usuario por la ubicación del archivo (si no la proporciona) .docx del cuaderno de campo y localizarlo.
    2. Utilizar la herramienta convertir_doc para convertir el archivo a markdown.
    3. Analizar el contenido del markdown y verificar que cumple con los requisitos de la certificación indicada.
    
    """
    query = f"requisitos cuaderno de campo campos obligatorios auditoría {tipo_certificacion}"

    filtros = {
        "categoria": "cuaderno",
        "tipo_certificacion": tipo_certificacion
    }
    return motor_busqueda_chroma(query, filtros)


@tool("calcular_plazos", args_schema=CalcularPlazosInput)
def tool_calcular_plazos(
    tipo_tramite: str,
    fecha_referencia: Optional[str] = None,
    isla: Optional[str] = None
) -> str:
    """
    Calcula plazos críticos de trámites agrícolas: POSEI, PAC, conversión ecológica,
    renovación DOP, certificado fitosanitario, auditoría GlobalG.A.P.
    Devuelve fecha límite, días restantes, documentos a preparar y pasos previos necesarios.
    Usar cuando el agricultor pregunta por fechas límite o cuándo tiene que solicitar algo.
    """
    query = f"plazo fecha límite documentación {tipo_tramite}"
    if isla:
        query += f" {isla}"

    filtros = {
        "categoria": "ayuda",
        "isla": isla
    }
    return motor_busqueda_chroma(query, filtros)


@tool("verificar_cumplimiento_dop", args_schema=VerificarCumplimientoDopInput)
def tool_verificar_cumplimiento_dop(
    dop: str,
    practica: str
) -> str:
    """
    Verifica si una práctica agrícola concreta es compatible con el pliego de condiciones
    de una DOP o IGP. Devuelve si es conforme, no conforme o requiere consulta al Consejo
    Regulador, con el artículo exacto del pliego que lo regula.
    Usar cuando el agricultor pregunta si puede hacer algo y mantener la DOP.
    """
    query = f"{practica} pliego condiciones {dop} conformidad"

    filtros = {
        "categoria": "dop",
        "dop": dop
    }
    return motor_busqueda_chroma(query, filtros)


@tool("requisitos_exportacion", args_schema=RequisitosExportacionInput)
def tool_requisitos_exportacion(
    producto: str,
    mercado_destino: str,
    tipo_certificacion: Optional[str] = None
) -> str:
    """
    Devuelve la lista completa de documentos necesarios para exportar a un mercado concreto:
    certificado fitosanitario, certificado de origen, análisis de residuos, etiquetado,
    organismo emisor, coste aproximado, tiempo de tramitación y LMR aplicables.
    Atención especial al Reino Unido: requisitos PHYTO y puntos de control fronterizos post-Brexit.
    Usar cuando el agricultor o responsable de exportación pregunta qué necesita para exportar.
    """
    query = f"requisitos exportación documentación {producto} {mercado_destino}"
    if tipo_certificacion:
        query += f" {tipo_certificacion}"

    filtros = {
        "categoria": "exportacion",
        "cultivo": producto,
        "mercado_destino": mercado_destino
    }
    return motor_busqueda_chroma(query, filtros)


@tool("alertas_plagas_enfermedades", args_schema=AlertasEnfermedadesInput)
def tool_alertas_plagas_enfermedades(
    cultivo: str,
    isla: str,
    incluir_web: bool = True
) -> str:
    """
    Devuelve alertas fitosanitarias activas para un cultivo e isla concretos:
    organismos causantes, síntomas de identificación, umbral de tratamiento recomendado
    y métodos de control disponibles.
    Siempre complementa con búsquedas en internet, tanto en ASAJA Canarias, como Gobierno de Canarias
    y MAPA para incluir alertas recientes no ingestadas en la base de conocimiento. Al realizar busquedas en internet,
    asegurate de añadir la fecha de la alerta y la fuente de la información.
    Usar cuando el agricultor pregunta por plagas activas o riesgos fitosanitarios actuales.
    """
    query = f"alerta plaga enfermedad {cultivo} {isla} activa tratamiento"

    filtros = {
        "categoria": "fitosanitario",
        "cultivo": cultivo,
        "isla": isla
    }
    return motor_busqueda_chroma(query, filtros)

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

def obtener_tools():
    tools_array = [
    obtener_info_rag,
    tool_buscar_fitosanitarios,
    tool_buscar_ayudas,
    tool_registrar_tratamiento,
    tool_verificar_cuaderno,
    tool_calcular_plazos,
    tool_verificar_cumplimiento_dop,
    tool_requisitos_exportacion,
    tool_alertas_plagas_enfermedades,
    convertir_doc
    ]
    return tools_array