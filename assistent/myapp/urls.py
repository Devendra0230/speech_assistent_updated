from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.index, name='index'),
    path('text_to_speech/', views.text_to_speech, name='text_to_speech'),
    path('speech_to_text/', views.speech_to_text, name='speech_to_text'),
]