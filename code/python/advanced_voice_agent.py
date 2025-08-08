import asyncio
import json
import requests
import speech_recognition as sr
import pyttsx3
import threading
import time
from queue import Queue

class AdvancedVoiceAgent:
    def __init__(self, nlweb_url="http://localhost:8000", wake_word="computer"):
        self.nlweb_url = nlweb_url
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # TTS setup
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 180)
        
        # State management
        self.listening_for_wake_word = True
        self.conversation_active = False
        self.audio_queue = Queue()
        
    def continuous_listen(self):
        """Continuously listen for audio in background thread"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        while True:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                self.audio_queue.put(audio)
            except sr.WaitTimeoutError:
                pass
    
    def process_audio_queue(self):
        """Process audio from queue"""
        while True:
            if not self.audio_queue.empty():
                audio = self.audio_queue.get()
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    if self.listening_for_wake_word:
                        if self.wake_word in text:
                            print(f"Wake word '{self.wake_word}' detected!")
                            self.handle_wake_word_activation()
                    else:
                        self.handle_user_query(text)
                        
                except sr.UnknownValueError:
                    pass  # Ignore unclear audio
                except sr.RequestError as e:
                    print(f"Speech recognition error: {e}")
            
            time.sleep(0.1)
    
    def handle_wake_word_activation(self):
        """Handle wake word detection"""
        self.listening_for_wake_word = False
        self.conversation_active = True
        self.speak_response("Yes, how can I help you?")
        
        # Set timeout for user response
        threading.Timer(10.0, self.conversation_timeout).start()
    
    def handle_user_query(self, query):
        """Process user query through NLWeb"""
        if any(exit_word in query for exit_word in ['goodbye', 'exit', 'quit', 'bye', 'thanks']):
            self.speak_response("You're welcome! Let me know if you need anything else.")
            self.reset_to_wake_word_mode()
            return
        
        # Query NLWeb
        response = self.query_nlweb(query)
        self.speak_response(response)
        
        # Continue conversation or timeout
        threading.Timer(15.0, self.conversation_timeout).start()
    
    def conversation_timeout(self):
        """Handle conversation timeout"""
        if self.conversation_active:
            self.speak_response("I'm here if you need anything else.")
            self.reset_to_wake_word_mode()
    
    def reset_to_wake_word_mode(self):
        """Reset to listening for wake word"""
        self.listening_for_wake_word = True
        self.conversation_active = False
        print(f"Listening for wake word: '{self.wake_word}'")
    
    def query_nlweb(self, question):
        """Query NLWeb API"""
        try:
            payload = {"question": question}
            response = requests.post(
                f"{self.nlweb_url}/api/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "I couldn't find an answer to that.")
            else:
                return "I'm having trouble processing that request right now."
                
        except Exception as e:
            return "I'm having trouble connecting to my knowledge base."
    
    def speak_response(self, text):
        """Text to speech output"""
        print(f"Assistant: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def start(self):
        """Start the voice agent"""
        print(f"Voice agent starting... Say '{self.wake_word}' to activate.")
        
        # Start background threads
        listen_thread = threading.Thread(target=self.continuous_listen, daemon=True)
        process_thread = threading.Thread(target=self.process_audio_queue, daemon=True)
        
        listen_thread.start()
        process_thread.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nVoice agent shutting down...")

if __name__ == "__main__":
    agent = AdvancedVoiceAgent(wake_word="computer")
    agent.start()

