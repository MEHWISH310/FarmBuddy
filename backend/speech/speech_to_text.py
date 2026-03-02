import speech_recognition as sr

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def listen(self, timeout=5, phrase_time_limit=10):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            text = self.recognizer.recognize_google(audio)
            return text, None
            
        except sr.WaitTimeoutError:
            return None, "Listening timeout"
        except sr.UnknownValueError:
            return None, "Could not understand audio"
        except sr.RequestError as e:
            return None, f"Speech recognition service error: {e}"
        except Exception as e:
            return None, str(e)
    
    def listen_for_phrase(self, phrase_time_limit=10):
        return self.listen(phrase_time_limit=phrase_time_limit)
    
    def listen_background(self, callback, phrase_time_limit=5):
        def callback_wrapper(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio)
                callback(text, None)
            except Exception as e:
                callback(None, str(e))
        
        stop_listening = self.recognizer.listen_in_background(
            self.microphone, 
            callback_wrapper,
            phrase_time_limit=phrase_time_limit
        )
        return stop_listening