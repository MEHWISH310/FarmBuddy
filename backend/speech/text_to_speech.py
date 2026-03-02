import pyttsx3
import threading

class TextToSpeech:
    def __init__(self):
        self.engine = None
        self.speaking = False
        self.initialize_engine()
        
    def initialize_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
            
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'english' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            self.engine = None
    
    def speak(self, text):
        if not self.engine:
            return False
        
        def _speak():
            self.speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.speaking = False
        
        thread = threading.Thread(target=_speak)
        thread.daemon = True
        thread.start()
        return True
    
    def speak_sync(self, text):
        if not self.engine:
            return False
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except:
            return False
    
    def stop(self):
        if self.engine and self.speaking:
            self.engine.stop()
            self.speaking = False
    
    def set_rate(self, rate):
        if self.engine:
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume):
        if self.engine and 0 <= volume <= 1:
            self.engine.setProperty('volume', volume)
    
    def set_voice(self, voice_id):
        if self.engine:
            try:
                self.engine.setProperty('voice', voice_id)
            except:
                pass