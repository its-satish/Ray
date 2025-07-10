import sys
import os
import threading
# from threading import Thread
import traceback
# import uuid
# import random
# import asyncio
from dotenv import dotenv_values
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt
# from PyQt5.QtCore import *
# import pygame
from Frontend.MainWin2 import MainWindow
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.chat_processor import EnhancedChatProcessor
# from Backend.RealtimeSearchEngine import RealtimeSearchEngine
# from Backend.Chatbot import ChatBot
# from Backend.Automation import Automation
# from Data.database import db
from ui_utils import SetAssistantStatus
# from tts_and_speech import TTSThread, SpeechRecognitionThread
from floating_button import FloatingButton

env_vars = dotenv_values(".env")
# Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
# InputLanguage = env_vars.get("InputLanguage", "en-US")
# AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

class AssistantLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_processor = None
        self.processor_thread = None
        #SetAssistantStatus("Ready")
        
        # Initialize main window
        self.assistant_window = MainWindow(self)
        self.assistant_window.hide()

        # Initialize floating button
        self.floating_btn = FloatingButton(toggle_callback=self.toggle_assistant)
        self.floating_btn.setParent(self)
        self.floating_btn.move(0, 0)

        # Position launcher
        self.setGeometry(
            QApplication.desktop().availableGeometry().width() - 80,
            QApplication.desktop().availableGeometry().height() - 80,
            60,
            60
        )
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()
        
        # Initialize chat processor
        self._init_chat_processor()

    def _init_chat_processor(self):
        """Initialize the chat processor component"""
        self.chat_processor = EnhancedChatProcessor()
        self.processor_thread = threading.Thread(
            target=self.chat_processor.start_processing,
            daemon=True
        )
        self.processor_thread.start()

    def toggle_assistant(self):
        """Toggle between showing/hiding the assistant window"""
        if self.assistant_window.isVisible():
            self.assistant_window.close_animated()
        else:
            self.hide_robot()
            self.assistant_window.show_animated()

    def show_robot(self):
        """Show the floating robot button"""
        self.show()
        self.floating_btn.show()

    def hide_robot(self):
        """Hide the floating robot button"""
        self.hide()
def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        SetAssistantStatus("Ready")
        
        # Set application properties
        app.setApplicationName(f"{Assistantname} AI Assistant")
        app.setApplicationVersion("2.0")
        
        # Create and show launcher
        launcher = AssistantLauncher()
        
        # Handle application exit
        def cleanup_and_exit():
            try:
                launcher.assistant_window.close()
                app.quit()
            except:
                pass
        
        app.aboutToQuit.connect(cleanup_and_exit)
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Application error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()