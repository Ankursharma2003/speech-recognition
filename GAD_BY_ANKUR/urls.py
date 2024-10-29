from django.urls import path

from . import views

app_name = "GAD_BY_ANKUR"

urlpatterns = [
    path("detect/" , views.detect_gender_age , name ='detect_gender_age' ),
    path('face/', views.face_capture, name='face_capture'),
    path("speech-to-text/",views.speech_to_text , name="speech-to-text")
]
