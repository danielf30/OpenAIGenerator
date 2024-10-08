import openai
import boto3
import json
from utils.text_clean import format_summary
from utils.openai_verificator import lambda_openai_verifier_handler
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Recuperar la clave API de OpenAI desde AWS Secrets Manager
    secret_name = "openai_api_key"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    secret = json.loads(secret)
    secret = secret.get(secret_name)
    
    # Configurar la clave API de OpenAI
    openai.api_key = secret
    
    # Obtener el enlace del artículo desde el evento de entrada
    link = event[0].get('Url', '')
    if not link:
        return {'error': 'No se proporcionó ningún enlace.'}
    
    prompt = f"""
    Genera un resumen profesional para LinkedIn basado en el siguiente artículo: {link}.
    El resumen debe consistir en 1 o 2 párrafos cortos que no solo destaquen los puntos más importantes del artículo, 
    sino también que incluyan mis reflexiones personales sobre lo aprendido y cómo estas ideas pueden ser aplicadas en la vida diaria y en los negocios.
    Además, incluye una recomendación basada en mi perspectiva sobre el tema, sugiriendo acciones o estrategias que podrían ser útiles para los lectores.
    Asegúrate de redactar en primera persona y evita suponer que tengo conocimientos específicos que no se mencionen explícitamente en el artículo.
    Proporciona el resultado en formato JSON con las claves 'Título', 'Resumen', 'Enlace', y 'Hashtags', donde los hashtags deben anteponerse con # y estar separados por comas, no deben estar contenidos en una lista.
    """

    try:
        response = openai.ChatCompletion.create(
            messages=[
                {"role": "system", "content": "Eres un asistente experto en marketing y creación de contenido profesional."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-3.5-turbo",
        )
        content = response.choices[0].message.content
        content = lambda_openai_verifier_handler(link,content)
        content = format_summary({'content': content})
        message = {'message': content}
        return {
            "statusCode": 200,
            "body": message
        }
    except openai.error.RateLimitError:
        return {'error': 'Se alcanzó el límite de tasa de OpenAI. Por favor, intenta de nuevo más tarde.'}
    except KeyError as e:
        print(f"Error: Clave no encontrada - {e}")
        return {
            "statusCode": 400,
            "body": json.dumps("Error: Clave no encontrada en el evento.")
        }
    except json.JSONDecodeError as e:
        print(f"Error: No se pudo decodificar el JSON - {e}")
        return {
            "statusCode": 400,
            "body": json.dumps("Error: JSON inválido en InputString.")
        }
    
    

