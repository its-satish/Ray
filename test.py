import sys
import os
from dotenv import dotenv_values
import langdetect

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
InputLanguage = env_vars.get("InputLanguage", "en-US")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

# Language settings - support multiple languages
InputLanguage = env_vars.get("InputLanguage", "en-US")  # Default to English
SecondaryLanguage = env_vars.get("SecondaryLanguage", "hi-IN")  # Hindi
AutoDetectLanguage = env_vars.get("AutoDetectLanguage", "true").lower() == "true"

# Voice settings for different languages
AssistantVoice_EN = env_vars.get("AssistantVoice_EN", "en-US-AriaNeural")
AssistantVoice_HI = env_vars.get("AssistantVoice_HI", "hi-IN-SwaraNeural")  # Hindi voice
AssistantVoice = AssistantVoice_EN  # Default

def setup_language_detection():
    """
    Optional: Use langdetect library for better language detection
    Install with: pip install langdetect
    """
    try:
        from langdetect import detect
        
        def detect_language_advanced(text):
            try:
                detected = detect(text)
                if detected == 'hi':
                    return "hi-IN", AssistantVoice_HI
                elif detected == 'en':
                    return "en-US", AssistantVoice_EN
                else:
                    return "en-US", AssistantVoice_EN  # Default to English
            except:
                return "en-US", AssistantVoice_EN
        
        return detect_language_advanced
    except ImportError:
        print("langdetect not installed. Using basic language detection.")
        return AutoDetectLanguage

# Usage example
if __name__ == "__main__":
    # Test language detection
    test_texts = [
        "Hello, how are you?",
        "नमस्ते, आप कैसे हैं?",
        "मैं ठीक हूं, धन्यवाद।",
        "Thank you very much!"
    ]
    
    for text in test_texts:
        lang, voice = AutoDetectLanguage(text)
        print(f"Text: {text}")
        print(f"Detected Language: {lang}, Voice: {voice}")
        print("---")