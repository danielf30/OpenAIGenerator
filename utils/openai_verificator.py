import openai
import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_openai_verifier_handler(event_link, event_content):
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

    # Obtener el enlace y el contenido generado anteriormente desde el evento
    link = event_link    
    generated_content = event_content

    # Prompt para verificar el contenido generado
    prompt = f"""
    El siguiente es un resumen generado para el artículo en {link}:
    {generated_content}

    Tu tarea es verificar si este resumen es consistente con el contenido del artículo proporcionado y asegurarte de que no incluye información inventada.

    Por favor, proporciona la respuesta en formato JSON con las siguientes claves:
    - 'Título': El título del artículo.
    - 'Resumen': El resumen proporcionado.
    - 'Enlace': El enlace al artículo.
    - 'Hashtags': Los hashtags asociados (precedidos por # y separados por comas).
    - 'Verificacion': Un valor booleano (`true` si el contenido es consistente, `false` si contiene información inventada o no relacionada).

    Asegúrate de que el campo 'Verificacion' refleje correctamente si el resumen es fiel al contenido del artículo.
    """

    try:
        response = openai.ChatCompletion.create(
            messages=[
                {"role": "system", "content": "Eres un asistente experto en verificar contenido."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-3.5-turbo",
        )
    except openai.error.RateLimitError:
        return {'error': 'Se alcanzó el límite de tasa de OpenAI. Por favor, intenta de nuevo más tarde.'}
    
    # Obtener la respuesta de verificación
    verification_result = response.choices[0].message.content
    return verification_result
