from django.shortcuts import render

import base64
import io
import json
import logging
import numpy as np
from PIL import Image
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from deepface import DeepFace
import pyttsx3
import wave
import librosa
import numpy as np
import speech_recognition as sr

logger = logging.getLogger(__name__)

@csrf_exempt
def detect_gender_age(request):
    try:
        if request.method == 'POST':
            try:
            # Decode the JSON body
                body_unicode = request.body.decode('utf-8')
                body = json.loads(body_unicode)
                logger.info("Request body parsed successfully.")

            # Get the image data from the JSON
                image_data = body.get('image', None)
            
                if not image_data:
                    logger.error("No image data provided in the request.")
                    return JsonResponse({'error': 'No image data provided'}, status=400)

            # Decode base64 image
                format, imgstr = image_data.split(';base64,')
                image_bytes = base64.b64decode(imgstr)
                image = Image.open(io.BytesIO(image_bytes)).convert('RGB')  # Convert to RGB
                logger.info("Image decoded, loaded, and converted to RGB successfully.")

            # Convert PIL image to numpy array
                image_np = np.array(image)
                logger.info("Image converted to numpy array.")

            # Analyze the image for age and gender
                result = DeepFace.analyze(img_path=image_np, actions=['age', 'gender' , 'emotion' , 'race'] ,  enforce_detection=False)
                print(result)
            
                age = result[0]['age']
                dominant_gender = result[0]['dominant_gender']
                dominant_emotion = result[0]['dominant_emotion']
                dominant_race = result[0]['dominant_race']
            
            
                print("Age:", age)
                print("Dominant Gender:", dominant_gender)
                print("dominant_emotion:" , dominant_emotion)
                print("Race:", dominant_race )
                return JsonResponse({
            'age': age,
            'gender': dominant_gender,
            'emotion':dominant_emotion,
            'race':dominant_race
            
        })
            
                logger.info("DeepFace analysis successful.")
            

        
        
            except Exception as e:
                logger.exception("Error processing the image:")
                return JsonResponse({'error': str(e)}, status=500)
    
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except:
        logger.exception("not running")

def face_capture(request):
    try:
        return render(request, 'face.html')
    except Exception as e:
        logger.exception("error in capturing the photo")
        




def speech_to_text(request):
    try:
        def convert_to_binary(audio_data):
            return audio_data.get_wav_data()

        def get_audio_frequency(audio_data):
            """Extract the sample rate (frequency) directly from in-memory audio data."""
            audio_buffer = io.BytesIO(audio_data.get_wav_data())
            with wave.open(audio_buffer, 'rb') as wf:
                sample_rate = wf.getframerate()
            return sample_rate

        def analyze_pitch(audio_data, sample_rate):
            """Analyze pitch using librosa's pyin to infer gender."""
        # Convert speech_recognition.AudioData to a NumPy array
            audio_buffer = io.BytesIO(audio_data.get_wav_data())
            with wave.open(audio_buffer, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio_signal = np.frombuffer(frames, dtype=np.int16)

        # Normalize the audio signal
            audio_signal = audio_signal / np.max(np.abs(audio_signal))

        # Use librosa to estimate the pitch with pyin (more reliable for human voice)
            pitches, voiced_flags, _ = librosa.pyin(audio_signal.astype(float), 
                                                fmin=librosa.note_to_hz('C2'), 
                                                fmax=librosa.note_to_hz('C7'),
                                                sr=sample_rate)

        # Filter out non-voiced frames (where voiced_flags is False)
            valid_pitches = pitches[voiced_flags]

            if len(valid_pitches) == 0:
                return None

        # Calculate the median and mean pitch
            median_pitch = np.median(valid_pitches)
            mean_pitch = np.mean(valid_pitches)

            return median_pitch, mean_pitch

        def infer_gender(pitch_median, pitch_mean):
            """Infer the gender based on pitch statistics."""
        # Adjusted pitch thresholds for better detection
            if pitch_median < 165:  # Lower threshold for male voices
                engine.say("your gender is male")
                return "Male"
            elif pitch_median >= 165 and pitch_median <= 255:  # Typical female voice range
                engine.say("your gender is female")
                return "Female"
            else:
                engine.say("sorry i am not able to determine your voice")
                return "Unknown"
        def save_audio_to_wav(audio_binary, output_filename):
        
            """Convert binary audio data back to a WAV file."""
            try:
            
                output_filename = "audio.wav"
        # Write binary data to a WAV file
                with wave.open(output_filename, 'wb') as wf:
                # The original audio format should be retrieved or known (e.g., channels, sample width, and rate)
                    wf.setnchannels(1)  # Assuming mono audio; adjust if stereo
                    wf.setsampwidth(2)   # Assuming 16-bit audio (2 bytes); adjust if needed
                    wf.setframerate(44100)  # Assuming 44.1kHz sample rate; adjust if needed
                    wf.writeframes(audio_data)
            except Exception as e:
                print(f"Error writing WAV file: {e}")
        engine = pyttsx3.init()
        recognizer = sr.Recognizer()
        def talk(text):
            engine.say(text)
            engine.runAndWait()
    
    
        if request.method == 'POST':
            with sr.Microphone() as source:
                print("Please speak...")
                talk("please speak")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

                try:
            # Recognize the speech
                    text = recognizer.recognize_google(audio)
                    print("You said: " + text)

            # Speak the recognized text using pyttsx3
                    talk("You said: " + text)
                    engine.runAndWait()

            # Convert the audio data to binary data
                    audio_data = convert_to_binary(audio)
                    save_audio_to_wav(audio_data, "audio.wav")
            #print(audio_data)

            # Get the frequency (sample rate) directly from audio data
                    frequency = get_audio_frequency(audio)
                    print(f"Frequency of the recorded audio: {frequency} Hz")

            # Analyze the pitch of the audio and infer gender
                    pitch_result = analyze_pitch(audio, frequency)
                    if pitch_result is not None:
                        median_pitch, mean_pitch = pitch_result
                        gender = infer_gender(median_pitch, mean_pitch)
                        engine.say("your gender is " + gender)
                        response = {
                        'text': text,
                        'gender': gender,
                        'frequency': frequency,
                    }
                    
                        print(f"Detected pitch (Median): {median_pitch:.2f} Hz, (Mean): {mean_pitch:.2f} Hz, Gender inferred: {gender}")
                        return JsonResponse(response)
                    else:
                        print("Unable to detect pitch for gender inference.")
                        return JsonResponse({'error': 'Unable to detect pitch for gender inference.'}, status=400)

                    print("Audio analysis, frequency, and gender detection completed successfully!")
                    return render(request ,"face.html")

                except sr.UnknownValueError:
                    print("Could not understand the audio.")
                    return render(request ,"face.html")
                except sr.RequestError:
                    print("Error in request.")
                    return render(request ,"face.html")
    except:
        print("sorry")
