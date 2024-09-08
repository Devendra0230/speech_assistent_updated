import json
import logging
import os
import threading
from datetime import datetime

import speech_recognition as sr
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from gtts import gTTS
from meta_ai_api import MetaAI
from pydub import AudioSegment
from pydub.playback import play

from .models import UserQuery

# Set up logging
logger = logging.getLogger(__name__)

current_language = 'en-IN'  # Default to Indian English

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def text_to_speech(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode("utf-8"))
        text = data.get('text', '')
        try:
            tts = gTTS(text, lang=current_language)
            
            # Generate a unique filename using the current timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            audio_filename = f"audio_{timestamp}.mp3"
            audio_path = os.path.join(settings.BASE_DIR, 'static/audio', audio_filename)
            
            tts.save(audio_path)
            audio_url = settings.STATIC_URL + f'audio/{audio_filename}'
            
            return JsonResponse({'status': 'Text-to-speech conversion successful', 'audio_url': audio_url})
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            return JsonResponse({'error': 'Text-to-speech conversion failed'})
    return JsonResponse({'error': 'Invalid request'})

# handle_post_processing function
def handle_post_processing(response_text):
    try:
        tts = gTTS(text=response_text, lang=current_language)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        audio_filename = f"response_{timestamp}.mp3"
        audio_path = os.path.join(settings.BASE_DIR, 'static/audio', audio_filename)
        tts.save(audio_path)

        return audio_filename

    except Exception as e:
        logger.error(f"Error during post-processing: {e}")
        return None

@csrf_exempt
def speech_to_text(request):
    try:
        if request.method == 'POST':
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            query_text = recognizer.recognize_google(audio)
            response_text = send_to_meta_ai(query_text)
            response = response_text['message']

            audio_filename = handle_post_processing(response)

            if audio_filename:
                audio_url = settings.STATIC_URL + 'audio/' + audio_filename
                return JsonResponse({
                    'status': 'success',
                    'query': query_text,
                    'response': response,
                    'audio_url': audio_url
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Audio processing failed'})

        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    except Exception as e:
        logger.error(f"Server error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Internal server error'})

def send_to_meta_ai(query_text):
    try:
        ai = MetaAI()
        logger.debug(f"Sendj query to Meta AI: {query_text}")
        response = ai.prompt(message=query_text)
        logger.debug(f"response from Meta AI: {response}")
        return response
    except Exception as e:
        logger.error(f"Error with Meta AI: {e}")
        return "There was an error. Please try again later."
