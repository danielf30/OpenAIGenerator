import json
import logging
from typing import Dict, Any

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def format_summary(data) -> str:
    """
    Genera un texto de resumen a partir de los datos proporcionados.

    Args:
        data (Dict[str, Any]): Diccionario que contiene la clave 'content' con el resumen en formato JSON.

    Returns:
        str: Texto formateado del resumen o un mensaje de error si ocurre alguna excepción.
    """
    try:
        # Extraer el contenido JSON del string dado, eliminando los delimitadores de código
        raw_content = data.get('content', '')
        if not raw_content:
            logger.error("El campo 'content' está vacío o no existe.")
            return "Error: No se proporcionó contenido válido para el resumen."

        # Eliminar los delimitadores de código ```json y ```
        content = raw_content.strip().replace('```json', '').replace('```', '').strip()
        if not content:
            logger.error("El contenido después de la limpieza está vacío.")
            return "Error: No se pudo extraer contenido JSON válido."

        # Convertir el contenido JSON a un diccionario
        resumen_dict = json.loads(content)

        # Verificar el campo 'Verificacion'
        verificacion = resumen_dict.get('Verificacion', False)
        if verificacion is True:
            # Obtener los campos necesarios con valores por defecto si no existen
            titulo = resumen_dict.get('Título', 'Sin Título')
            resumen = resumen_dict.get('Resumen', 'Sin Resumen')
            hashtags = resumen_dict.get('Hashtags', 'Sin Hashtags')
            enlace = resumen_dict.get('Enlace', 'Sin Enlace')

            # Crear la estructura textual requerida
            texto_resumen = (
                f"**{titulo}**\n\n"
                f"{resumen}\n\n"
                f"{hashtags}\n\n"
                f"Fuente: {enlace}"
            )
            return texto_resumen
        else:
            logger.warning("La verificación del contenido ha fallado.")
            return "El resumen generado no es consistente con el contenido del artículo proporcionado."

    except json.JSONDecodeError as json_err:
        logger.error(f"Error al decodificar JSON: {json_err}")
        return "Error: El contenido proporcionado no es un JSON válido."
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {e}")
        return "Error: Ocurrió un problema al procesar el resumen."
