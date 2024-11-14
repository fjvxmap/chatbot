import speech_recognition as sr
import pyttsx3


class VoiceControl:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("voice", "com.apple.speech.synthesis.voice.yuna")

    def listen_to_user(self):
        """사용자의 음성을 듣고 텍스트로 변환."""
        try:
            with self.microphone as source:
                print("네, 듣고 있어요!")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio, language="ko-KR")
                print(f"인식된 명령: {command}")
                return command
        except sr.UnknownValueError:
            print("죄송합니다. 이해하지 못했습니다.")
            return None
        except sr.RequestError as e:
            print(f"음성 인식 서비스에 문제가 발생했습니다: {e}")
            return None

    def speak(self, text):
        """TTS로 텍스트 출력."""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
