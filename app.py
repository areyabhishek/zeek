import os
   from flask import Flask, request
   from twilio.twiml.voice_response import VoiceResponse
   from twilio.rest import Client
   import requests
   import openai
   from dotenv import load_dotenv

   load_dotenv()

   app = Flask(__name__)

   # Configure your API keys and Twilio credentials
   TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
   TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
   ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

   twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
   openai.api_key = OPENAI_API_KEY

   @app.route('/incoming_call', methods=['POST'])
   def incoming_call():
       response = VoiceResponse()
       response.say("Hello! How can I assist you today?")
       response.record(maxLength="30", action="/process_speech")
       return str(response)

   @app.route('/process_speech', methods=['POST'])
   def process_speech():
       recording_url = request.form['RecordingUrl']
       
       # Download the recording
       audio_file = requests.get(recording_url)
       
       # Transcribe the audio using OpenAI's Whisper API
       transcript = openai.Audio.transcribe("whisper-1", audio_file.content)
       
       # Generate a response using GPT-3
       gpt_response = openai.Completion.create(
           engine="text-davinci-002",
           prompt=f"User: {transcript}\nAI:",
           max_tokens=150
       )
       ai_response = gpt_response.choices[0].text.strip()
       
       # Generate speech from text using ElevenLabs
       eleven_labs_url = "https://api.elevenlabs.io/v1/text-to-speech/voice_id"
       headers = {
           "Accept": "audio/mpeg",
           "Content-Type": "application/json",
           "xi-api-key": ELEVENLABS_API_KEY
       }
       data = {
           "text": ai_response,
           "voice_settings": {
               "stability": 0,
               "similarity_boost": 0
           }
       }
       response = requests.post(eleven_labs_url, json=data, headers=headers)
       
       # Save the generated audio
       with open("static/response.mp3", "wb") as f:
           f.write(response.content)
       
       # Play the generated audio to the caller
       twiml_response = VoiceResponse()
       twiml_response.play(f"{request.url_root}static/response.mp3")
       
       return str(twiml_response)

   if __name__ == '__main__':
       app.run(debug=True)