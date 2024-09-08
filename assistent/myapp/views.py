import json
import logging
import os
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
            audio_path = os.path.join(settings.BASE_DIR, 'static/audio', 'temp.mp3')
            tts.save(audio_path)
            audio_url = settings.STATIC_URL + 'audio/temp.mp3'
            
            return JsonResponse({'status': 'Text-to-speech conversion successful', 'audio_url': audio_url})
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            return JsonResponse({'error': 'Text-to-speech conversion failed'})
    return JsonResponse({'error': 'Invalid request'})

@csrf_exempt
def speech_to_text(request):
    try:
        if request.method == 'POST':
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening...")
                request.session['listening'] = True
                audio = recognizer.listen(source)

            try:
                query_text = recognizer.recognize_google(audio)
                print(f"Recognized query: {query_text}")
                
                # Store user query in text file
                query_file = os.path.join(settings.BASE_DIR, 'static/text', 'user_queries.txt')
                with open(query_file, 'a') as file:
                    file.write(f"{query_text}\n")
                
                # Send query Meta AI and get response
                response_text = send_to_meta_ai(query_text)
                response = response_text['message']
                print(f"Meta AI response: {response}")

                # Convert response to speech and play
                try:
                    tts = gTTS(text=response, lang=current_language)  
                    audio_path = os.path.join(settings.BASE_DIR, 'static/audio', 'response.mp3')
                    tts.save(audio_path)
                    audio_url = settings.STATIC_URL + 'audio/response.mp3'
                    play(AudioSegment.from_file(audio_path))
                except Exception as e:
                    logger.error(f"Error during TTS conversion or playback: {e}")
                    return JsonResponse({'status': 'error', 'message': str(e)})

                # Store response in text file
                response_file = os.path.join(settings.BASE_DIR, 'static/text', 'responses.txt')
                with open(response_file, 'a') as file:
                    file.write(f"{response_text}\n")

                return JsonResponse({
                    'status': 'success',
                    'query': query_text,
                    'response': response,
                    'audio_url': audio_url
                })

            except Exception as e:
                logger.error(f"Error during processing: {e}")
                return JsonResponse({'status': 'error', 'message': str(e)})
        else:
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
