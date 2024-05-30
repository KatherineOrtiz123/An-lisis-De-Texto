from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import tweepy
from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
import logging
from fastapi.templating import Jinja2Templates

# Descargar datos necesarios para NLTK
nltk.download('punkt')

# Configuración del clasificador de sentimientos
clasificador = pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')

# Configuración de FastAPI
app = FastAPI()

# Configuración para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración de templates
templates = Jinja2Templates(directory="templates")

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Función para analizar sentimientos de oraciones
def analizar_sentimientos_oraciones(oraciones):
    resultados = []
    for oracion in oraciones:
        resultado = clasificador(oracion)
        resultados.append(resultado[0])
    return resultados

# Función para combinar resultados de sentimientos
def combinar_resultados(resultados):
    suma_puntuaciones = sum(int(resultado['label'][0]) for resultado in resultados)
    promedio = suma_puntuaciones / len(resultados)
    return promedio

# Ruta para la interfaz gráfica
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta para análisis de sentimientos
@app.get("/sentimientos/{texto}")
def analizar_sentimiento_hf(texto: str):
    oraciones = sent_tokenize(texto)
    resultados = analizar_sentimientos_oraciones(oraciones)
    promedio = combinar_resultados(resultados)

    mapeo_sentimientos = {
        1: 'malo',
        2: 'no tan malo',
        3: 'intermedio',
        4: 'bueno',
        5: 'excelente',
    }

    sentimiento = round(promedio)
    return mapeo_sentimientos.get(sentimiento, "etiqueta desconocida")

# Configuración de la API de Twitter
BEARER_TOKEN = 'YOUR_BEARER_TOKEN'
client = tweepy.Client(bearer_token=BEARER_TOKEN)

@app.get("/twitter/sentimientos/")
def analizar_sentimientos_twitter(url: str):
    try:
        tweet_id = url.split('/')[-1]
        tweet = client.get_tweet(tweet_id, tweet_fields=['author_id'])
        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet no encontrado")
        query = f'conversation_id:{tweet_id} is:reply'
        tweets = client.search_recent_tweets(query=query, tweet_fields=['text'], max_results=100)
        oraciones = [tweet.text for tweet in tweets.data] if tweets.data else []
        if not oraciones:
            return {"mensaje": "No se encontraron comentarios para analizar."}
        resultados = analizar_sentimientos_oraciones(oraciones)
        promedio = combinar_resultados(resultados)
        mapeo_sentimientos = {
            1: 'malo',
            2: 'no tan malo',
            3: 'intermedio',
            4: 'bueno',
            5: 'excelente',
        }
        sentimiento = round(promedio)
        return mapeo_sentimientos.get(sentimiento, "etiqueta desconocida")
    except tweepy.TweepyException as e:
        logging.error(f"Error al procesar la solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))
