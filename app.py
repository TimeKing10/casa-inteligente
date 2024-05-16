import streamlit as st
import cv2
import numpy as np
import face_recognition
import requests
import speech_recognition as sr
from google.cloud import speech
from PIL import Image

# Configuración de Google Cloud Speech-to-Text
client = speech.SpeechClient()

def transcribe_speech(audio_file):
    with open(audio_file, 'rb') as f:
        audio_data = f.read()

    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='es-ES'
    )

    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript if response.results else ""

# Cargar imágenes de caras conocidas
known_faces = []
known_names = []

def load_known_faces():
    import os
    for filename in os.listdir("known_faces"):
        image = face_recognition.load_image_file(f"known_faces/{filename}")
        encoding = face_recognition.face_encodings(image)[0]
        known_faces.append(encoding)
        known_names.append(filename.split(".")[0])

load_known_faces()

def recognize_face(image):
    unknown_image = face_recognition.load_image_file(image)
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

    results = face_recognition.compare_faces(known_faces, unknown_encoding)
    return any(results)

def control_led(state):
    url = "https://api.wokwi.com/projects/YOUR_PROJECT_ID/devices/YOUR_DEVICE_ID/led"
    data = {"state": state}
    response = requests.post(url, json=data)
    return response.json()

# Interfaz de Streamlit
st.title("Casa Inteligente")

page = st.sidebar.selectbox("Selecciona la página", ["Sistema de Seguridad"])

if page == "Sistema de Seguridad":
    st.header("Sistema de Seguridad")

    uploaded_image = st.file_uploader("Subir imagen de cámara", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption='Imagen subida', use_column_width=True)
        if recognize_face(uploaded_image):
            st.success("Reconocido como el dueño de la casa")
            st.subheader("Comandos de Voz")

            uploaded_audio = st.file_uploader("Subir archivo de audio", type=["wav"])
            if uploaded_audio:
                with open("temp.wav", "wb") as f:
                    f.write(uploaded_audio.getbuffer())
                transcription = transcribe_speech("temp.wav")
                st.write(f"Transcripción: {transcription}")

                if "prender" in transcription.lower():
                    control_led("on")
                    st.success("LED prendido")
                elif "apagar" in transcription.lower():
                    control_led("off")
                    st.success("LED apagado")
                else:
                    st.error("Comando no reconocido")
        else:
            st.error("No reconocido como el dueño de la casa")
