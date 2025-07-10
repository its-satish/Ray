# Enhanced Professional UI.py - Modern Design with Animations
import threading
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QFrame, QScrollArea
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QTextCharFormat, QMovie, QFont, QTextDocument
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5.QtCore import QMetaType
from PyQt5.QtGui import QTextCursor, QTextCharFormat
import sys
import os
from dotenv import dotenv_values
import time
import speech_recognition as sr
from threading import Thread
import uuid
import pygame
import random
import asyncio
import edge_tts

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Backend.chat_processor import EnhancedChatProcessor
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Chatbot import ChatBot
from Backend.Automation import Automation
from Data.database import db

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
InputLanguage = env_vars.get("InputLanguage", "en-US")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")
DataDirPath = os.path.join(current_dir, "Data")

# Create directories if they don't exist
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)
os.makedirs(DataDirPath, exist_ok=True)

# Professional Color Scheme
COLORS = {
    'primary_blue': '#2563eb',
    'light_blue': '#3b82f6',
    'hover_blue': '#1d4ed8',
    'primary_orange': '#ea580c',
    'light_orange': '#f97316',
    'hover_orange': '#c2410c',
    'background': '#0f172a',      # Main background
    'chat_background': '#0a0f1c',  # Even darker for chat area
    'surface': '#1e293b',
    'surface_light': "#2F3D50",
    'text_primary': '#f8fafc',
    'text_secondary': '#cbd5e1',
    'text_trinary': "#8f9194",
    'border': "#4D5B6E",
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444'
}

def GraphicsDirectoryPath(Filename):
    path = os.path.join(GraphicsDirPath, Filename)
    if not os.path.exists(path):
        print(f"[WARNING] Image not found: {path}")
    return path.replace('\\', '/')

def TempDirectoryPath(Filename):
    path = os.path.join(TempDirPath, Filename)
    return path.replace('\\', '/')

def SetMicrophoneStatus(Command):
    with open(TempDirectoryPath('Mic.data'), "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    try:
        with open(TempDirectoryPath('Mic.data'), "r", encoding='utf-8') as file:
            return file.read().strip()
    except:
        SetMicrophoneStatus("False")
        return "False"

def SetAssistantStatus(Status):
    with open(TempDirectoryPath('Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
            status = file.read().strip()
            return status if status else "Ready"
    except:
        SetAssistantStatus("Ready")
        return "Ready"

def SetAudioOutputStatus(status):
    """Set audio output status (True/False)"""
    with open(TempDirectoryPath('AudioOutput.data'), "w", encoding='utf-8') as file:
        file.write(str(status))

def GetAudioOutputStatus():
    """Get audio output status"""
    try:
        with open(TempDirectoryPath('AudioOutput.data'), "r", encoding='utf-8') as file:
            return file.read().strip() == "True"
    except:
        SetAudioOutputStatus(True)
        return True

def capitalize_first_letter(text):
    """Capitalize the first letter of a string"""
    if not text:
        return text
    return text[0].upper() + text[1:]

class ChatBubble(QWidget):
    """Custom chat bubble widget - FIXED VERSION"""
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.initUI()
        
    def initUI(self):
        # Main layout for the bubble container
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)  # Reduced margins
        main_layout.setSpacing(0)
        
        # Create bubble container
        bubble = QFrame()
        bubble.setMaximumWidth(280)  # Limit bubble width
        bubble.setMinimumWidth(100)   # Minimum width
        
        # Message label with word wrap
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 11))
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        message_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            padding: 12px 16px;
            background: transparent;
            border: none;
        """)
        
        # Set bubble style and alignment based on sender
        if self.is_user:
            # User messages - right aligned, blue background
            bubble.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
                    border-radius: 18px;
                    border-bottom-right-radius: 6px;
                    margin: 2px;
                }}
            """)
            # Add stretch to push user messages to the right
            main_layout.addStretch(1)
            main_layout.addWidget(bubble)
            
        else:
            # Assistant messages - left aligned, dark background
            bubble.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #1a202c, stop:1 #2d3748);
                    border-radius: 18px;
                    border-bottom-left-radius: 6px;
                    margin: 2px;
                    border: 1px solid #4a5568;
                }}
            """)
            # Assistant messages stay on the left
            main_layout.addWidget(bubble)
            main_layout.addStretch(1)
        
        # Add message to bubble
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addWidget(message_label)
    
    def show_animated(self):
        """Show bubble with animation"""
        target_height = self.sizeHint().height() + 16
        self.animation.setStartValue(0)
        self.animation.setEndValue(target_height)
        self.animation.start()
        self.show()

class TTSThread(QThread):
    """Thread for handling Text-to-Speech operations"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.should_stop = False
        
    def run(self):
        try:
            # Convert text to audio file
            asyncio.run(self.text_to_audio_file(self.text))
            
            if self.should_stop:
                return
                
            # Play the audio
            pygame.mixer.init()
            speech_file = os.path.join(DataDirPath, "speech.mp3")
            pygame.mixer.music.load(speech_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and not self.should_stop:
                self.msleep(100)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass
            self.finished.emit()
    
    async def text_to_audio_file(self, text):
        """Convert text to audio file using edge_tts"""
        file_path = os.path.join(DataDirPath, "speech.mp3")
        
        # Remove existing file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Generate speech
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
        await communicate.save(file_path)
    
    def stop(self):
        """Stop TTS playback"""
        self.should_stop = True

class SpeechRecognitionThread(QThread):
    recognized = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    listening_state = pyqtSignal(bool)
    processing_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_running = True
        self._should_listen = False
        self._listening_enabled = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Adjust recognition settings for better performance
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.3
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone initialization error: {e}")

    def run(self):
        while self._is_running:
            if self._should_listen and self._listening_enabled:
                try:
                    self.status_changed.emit("Listening...")
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                        #self.status_changed.emit("Processing...")
                        self.status_changed.emit("Ready")
                        text = self.recognizer.recognize_google(audio, language=InputLanguage)
                        if text and len(text.strip()) > 2:
                            self.recognized.emit(text)
                            # Don't stop listening - continue listening for more commands
                            # self._should_listen = False  # REMOVED THIS LINE
                            # self.listening_state.emit(False)  # REMOVED THIS LINE
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"Recognition error: {e}")
                    self.msleep(1000)
                    continue
            else:
                self.msleep(100)

    def start_listening(self):
        self._should_listen = True
        self._listening_enabled = True
        self.listening_state.emit(True)
        self.status_changed.emit("Listening...")

    def stop_listening(self):
        self._should_listen = False
        self._listening_enabled = False
        self.listening_state.emit(False)
        self.status_changed.emit("Ready")

    def stop(self):
        self._is_running = False
        self._should_listen = False
        self._listening_enabled = False
        self.wait()

class FloatingButton(QLabel):
    # Signal for when button is clicked
    clicked = pyqtSignal()
    
    def __init__(self, parent=None, toggle_callback=None, assistant_name="Assistant"):
        super().__init__(parent)
        self.setFixedSize(75, 75)
        self.toggle_callback = toggle_callback
        self.assistant_name = assistant_name
        self.setToolTip(f"Open {self.assistant_name}")
        
        # Drag support variables
        self.drag_position = None
        self.is_dragging = False
        
        self.initUI()
        self.setup_breathing_animation()
        
    def initUI(self):
        """Initialize the UI components"""
        self.set_icon()
        
        self.setStyleSheet("""
        QLabel {
            border-radius: 37px;
            background: transparent;
            border: none;
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        """)
        
    def setup_breathing_animation(self):
        """Setup subtle breathing animation using opacity instead of geometry"""
        self.breathing_animation = QPropertyAnimation(self, b"windowOpacity")
        self.breathing_animation.setDuration(3000)  # Slower, more subtle
        self.breathing_animation.setLoopCount(-1)
        self.breathing_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.breathing_animation.setStartValue(0.8)
        self.breathing_animation.setEndValue(1.0)
        self.start_breathing()
        
    def set_icon(self):
        """Set icon from assistant.png or fallback to emoji"""
        assistant_icon_path = os.path.join("Frontend", "Graphics", "eve.png")
        
        if os.path.exists(assistant_icon_path):
            try:
                pixmap = QPixmap(assistant_icon_path)
                # Use smaller scaling to prevent cutting and add margins
                scaled_pixmap = pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(scaled_pixmap)
                self.setAlignment(Qt.AlignCenter)
                print(f"✓ Loaded assistant.png from {assistant_icon_path}")
                return
            except Exception as e:
                print(f"Error loading assistant.png: {e}")
        
        # Fallback to emoji
        self.setText("🤖")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(self.styleSheet() + """
        QLabel {
            font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif;
            font-size: 20px;
        }
        """)
    
    def start_breathing(self):
        """Start the breathing animation"""
        if hasattr(self, 'breathing_animation'):
            self.breathing_animation.start()
    
    def stop_breathing(self):
        """Stop the breathing animation"""
        if hasattr(self, 'breathing_animation'):
            self.breathing_animation.stop()
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            # Calculate movement distance to determine if this is a drag
            movement_distance = (event.globalPos() - self.drag_position - self.frameGeometry().topLeft()).manhattanLength()
            
            if movement_distance > 3:  # Threshold to distinguish between click and drag
                self.is_dragging = True
                # Move the widget
                new_pos = event.globalPos() - self.drag_position
                
                # Get parent boundaries to keep button within window
                if self.parent():
                    parent_rect = self.parent().rect()
                    # Ensure button stays within parent boundaries
                    new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - self.width())))
                    new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - self.height())))
                
                self.move(new_pos)
                event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                # This was a click, not a drag
                if self.toggle_callback:
                    self.toggle_callback()
                self.clicked.emit()
            
            # Reset drag state
            self.drag_position = None
            self.is_dragging = False
            event.accept()
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events"""
        self.stop_breathing()
        # Add hover effect
        self.setStyleSheet(self.styleSheet() + """
        QLabel {
            background: rgba(255, 255, 255, 0.1);
        }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events"""
        self.start_breathing()
        # Remove hover effect
        self.setStyleSheet("""
        QLabel {
            border-radius: 37px;
            background: transparent;
            border: none;
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        """)
        super().leaveEvent(event)
    
    def cleanup(self):
        """Clean up animations when widget is destroyed"""
        if hasattr(self, 'breathing_animation'):
            self.breathing_animation.stop()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


class AssistantLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_processor = None
        self.processor_thread = None
        
        # Initialize main window
        self.assistant_window = MainWindow(self)
        self.assistant_window.hide()

        # Initialize floating button
        self.floating_btn = FloatingButton(toggle_callback=self.toggle_assistant)
        self.floating_btn.setParent(self)
        self.floating_btn.move(0, 0)

        # Position launcher
        screen_geometry = QApplication.desktop().availableGeometry()
        self.setGeometry(
            screen_geometry.width() - 80,
            screen_geometry.height() - 80,
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

class MainWindow(QMainWindow):
    update_chat_safe = pyqtSignal(str, bool)  # message, is_user
    
    def __init__(self, launcher):
        super().__init__()
        self.launcher = launcher
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Animation properties
        self.opacity_animation = None
        self.geometry_animation = None

        # Connect the thread-safe update signal
        self.update_chat_safe.connect(self._handle_chat_update, Qt.QueuedConnection)

        self.search_engine = RealtimeSearchEngine()
        self.chatbot = ChatBot()
        
        # Generate unique conversation ID for this session
        self.conversation_id = str(uuid.uuid4())
        print(f"Started new conversation: {self.conversation_id}")
        
        # Response mode flag
        self.summary_mode = False
        self.rtse_mode = False
        
        # TTS related
        self.current_tts_thread = None
        self.tts_responses = [
            "The rest of the result has been displayed in the chat.",
            "You can see the complete response above.",
            "The full answer is now visible in the chat.",
            "Please check the chat for the complete response.",
            "The detailed response is shown in the conversation."
        ]
        
        # Initialize UI components
        self.initUI()
        self.last_message = ""
        self.processed_messages = set()
        self.last_displayed_messages = set()
        
        # Initialize speech recognition
        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.recognized.connect(self.on_speech_recognized)
        self.speech_thread.status_changed.connect(self.update_status)
        self.speech_thread.listening_state.connect(self.update_listening_ui)
        self.speech_thread.start()
        
        # Setup timer for updating UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)
        
        # Greeting system
        self.greeting_shown = False
        self.greeting_timer = QTimer(self)
        self.greeting_timer.timeout.connect(self.show_greeting)
        self.greeting_timer.setSingleShot(True)
        self.greeting_timer.start(1500)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background with gradient
        gradient_rect = self.rect()
        painter.setBrush(QColor(COLORS['background']))
        painter.setPen(QPen(QColor(COLORS['border']), 1))
        painter.drawRoundedRect(gradient_rect, 24, 24)
        
        # Subtle inner border
        inner_rect = gradient_rect.adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawRoundedRect(inner_rect, 23, 23)

    def show_animated(self):
        """Show window with animation"""
        target_geometry = QRect(
            QApplication.desktop().availableGeometry().width() - 380,
            QApplication.desktop().availableGeometry().height() - 600,
            360,
            580
        )
        
        # Start from smaller size
        start_geometry = QRect(
            target_geometry.center().x() - 50,
            target_geometry.center().y() - 50,
            100,
            100
        )
        
        self.setGeometry(start_geometry)
        self.show()
        
        # Animate to full size
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(400)
        self.geometry_animation.setEasingCurve(QEasingCurve.OutBack)
        self.geometry_animation.setStartValue(start_geometry)
        self.geometry_animation.setEndValue(target_geometry)
        self.geometry_animation.start()
        
        self.raise_()
        self.activateWindow()

    def close_animated(self):
        """Close window with animation"""
        current_geometry = self.geometry()
        target_geometry = QRect(
            current_geometry.center().x() - 25,
            current_geometry.center().y() - 25,
            50,
            50
        )
        
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(300)
        self.geometry_animation.setEasingCurve(QEasingCurve.InBack)
        self.geometry_animation.setStartValue(current_geometry)
        self.geometry_animation.setEndValue(target_geometry)
        self.geometry_animation.finished.connect(self.hide_window)
        self.geometry_animation.start()

    def initUI(self):
        self.setFixedSize(360, 580)
    
    # Main container
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(container)

    # Main layout
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

    # Title bar (called only once)
        self.create_title_bar(main_layout)
    
    # Chat area
        self.create_chat_area(main_layout)
    
    # Status and animation area
        self.create_status_area(main_layout)
    
    # Input area
        self.create_input_area(main_layout)

    def create_title_bar(self, main_layout):
        """Create professional title bar with improved toggle layout"""
    
        title_bar = QWidget()
        title_bar.setFixedHeight(80)
        title_bar.setStyleSheet(f"""
        QWidget {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {COLORS['surface']}, stop:1 {COLORS['surface_light']});
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        border-bottom: 1px solid {COLORS['border']};
    }}
        """)

        title_layout = QVBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 10, 15, 10)
        title_layout.setSpacing(8)

    # Top row - Title and minimize button
        top_row = QHBoxLayout()

    # Title with professional AI icon
        title_container = QWidget()
        title_container_layout = QHBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        title_container_layout.setSpacing(12)

    # Robot icon using eve.png
        ai_icon = QLabel()
        ai_icon.setFixedSize(24, 24)
        ai_icon.setAlignment(Qt.AlignCenter)
    
        try:
            robot_icon_path = GraphicsDirectoryPath("eve.png")
            if os.path.exists(robot_icon_path):
                pixmap = QPixmap(robot_icon_path)
                scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                ai_icon.setPixmap(scaled_pixmap)
            else:
            # Fallback to AI text
                ai_icon.setText("AI")
        except Exception as e:
            print(f"Error loading robot icon in title: {e}")
            ai_icon.setText("AI")
    
        ai_icon.setStyleSheet(f"""
        QLabel {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1);
        border-radius: 16px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 900;
        font-size: 14px;
        letter-spacing: 1px;
        }}
        """)

    # Title text
        title_label = QLabel(f"{Assistantname} AI Assistant")
        title_label.setStyleSheet(f"""
        color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: 600;
    font-family: 'Segoe UI', Arial, sans-serif;
        """)

        title_container_layout.addWidget(ai_icon)
        title_container_layout.addWidget(title_label)

    # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setStyleSheet(f"""
        QPushButton {{
        background-color: {COLORS['surface_light']};
        border: 1px solid {COLORS['border']};
        border-radius: 15px;
        color: {COLORS['text_secondary']};
        font-size: 16px;
        font-weight: bold;
        }}
        QPushButton:hover {{
        background-color: {COLORS['error']};
        color: white;
        }}
        """)
        self.minimize_btn.clicked.connect(self.close_animated)

        top_row.addWidget(title_container)
        top_row.addStretch()
        top_row.addWidget(self.minimize_btn)

    # Bottom row - Mode toggles with SAME COLOR SCHEME
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(10)

    # Standard/Summary Mode toggle (left) - SAME COLOR AS AI CHAT
        self.mode_toggle_btn = QPushButton("📝 Standard Mode")
        self.mode_toggle_btn.setFixedHeight(30)
        self.mode_toggle_btn.setStyleSheet(f"""
        QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
        color: white;
        border: none;
        border-radius: 15px;
        font-size: 11px;
        font-weight: 600;
        padding: 0px 16px;
        }}
        QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
        }}
        """)
        self.mode_toggle_btn.clicked.connect(self.toggle_response_mode_manual)

    # AI Chat/Search Mode toggle (right) - SAME COLOR SCHEME
        self.rtse_toggle_btn = QPushButton("🤖 AI Chat")
        self.rtse_toggle_btn.setFixedHeight(30)
        self.rtse_toggle_btn.setStyleSheet(f"""
        QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
        color: white;
        border: none;
        border-radius: 15px;
        font-size: 11px;
        font-weight: 600;
        padding: 0px 16px;
        }}
        QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
        }}
        """)
        self.rtse_toggle_btn.clicked.connect(self.toggle_rtse_mode)

        toggle_row.addWidget(self.mode_toggle_btn)
        toggle_row.addStretch()
        toggle_row.addWidget(self.rtse_toggle_btn)

    # Add rows to main layout
        title_layout.addLayout(top_row)
        title_layout.addLayout(toggle_row)

        main_layout.addWidget(title_bar)

    def update_status_display(self, status):
        """Update status display with proper colors - separated from SetAssistantStatus"""
        self.status_label.setText(status)
    
    # Update status colors based on state
        if status == "Ready":
            self.status_dot.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        elif status == "Listening...":
            self.status_dot.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        elif status in ["Processing...", "Processingggg..."]:
            self.status_dot.setStyleSheet(f"""
            color: {COLORS['warning']};
            font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
            color: {COLORS['warning']};
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        else:
            self.status_dot.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)


    def create_chat_area(self, main_layout):
        """Create chat area with bubbles - FIXED VERSION"""
    # Chat container with dark background
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll.setStyleSheet(f"""
        QScrollArea {{
            background-color: #0a0f1c;  /* Very dark background */
            border: none;
            border-radius: 0px;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: #0a0f1c;  /* Ensure content background is also dark */
        }}
        QScrollBar:vertical {{
            background-color: {COLORS['surface']};
            width: 6px;
            border-radius: 3px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['text_secondary']};
        }}
        """)
    
    # Chat content widget with dark background
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: #0a0f1c;")  # Dark background
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(10, 15, 10, 15)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignTop)  # Align to top instead of stretch
    
        self.chat_scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.chat_scroll)

    # Continuation of Enhanced Professional UI.py - Complete remaining code

    def create_status_area(self, main_layout):
        """Create status and audio control area with NO BORDER"""
        status_container = QWidget()
        status_container.setFixedHeight(50)
        status_container.setStyleSheet(f"""
    background-color: {COLORS['surface']};
    border-top: 1px solid {COLORS['border']};
        """)

        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(20, 10, 20, 10)

    # Status widget WITHOUT border
        status_widget = QWidget()
        status_widget.setFixedHeight(30)
        status_widget.setStyleSheet(f"""
    QWidget {{
    background-color: {COLORS['surface']};
    border-radius: 15px;
    border: none;
    }}
        """)

        status_widget_layout = QHBoxLayout(status_widget)
        status_widget_layout.setContentsMargins(12, 0, 12, 0)

    # Status indicator dot
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"""
    color: {COLORS['primary_blue']};
    font-size: 12px;
        """)

    # Status text
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
    color: {COLORS['text_primary']};
    font-size: 12px;
    font-weight: 600;
    font-family: 'Segoe UI', Arial, sans-serif;
        """)

    # Add animation label (mic indicator)
        self.animation_label = QLabel()
        self.animation_label.setFixedSize(30, 30)
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setStyleSheet(f"""
    border-radius: 15px;
    background-color: transparent;
    border: none;
        """)

        status_widget_layout.addWidget(self.status_dot)
        status_widget_layout.addWidget(self.status_label)
        status_widget_layout.addStretch()
        status_widget_layout.addWidget(self.animation_label)

    # Audio toggle button with SAME COLOR SCHEME as other buttons
        self.audio_toggle_btn = QPushButton("🔊")
        self.audio_toggle_btn.setFixedSize(35, 30)
        self.audio_toggle_btn.setToolTip("Toggle Audio Output")
        self.audio_toggle_btn.clicked.connect(self.toggle_audio_output)

    # Add to layout
        status_layout.addWidget(status_widget)
        status_layout.addStretch()
        status_layout.addWidget(self.audio_toggle_btn)

        main_layout.addWidget(status_container)

    def create_input_area(self, main_layout):
        """Create input area with mic on left, send on right - SAME COLOR SCHEME"""
        input_container = QWidget()
        input_container.setFixedHeight(80)
        input_container.setStyleSheet(f"""
    background-color: {COLORS['surface']};
    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
    border-top: 1px solid {COLORS['border']};
        """)

        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(15, 15, 15, 15)

    # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

    # Voice button (left) - SAME COLOR SCHEME
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(40, 40)
        self.voice_btn.setCheckable(True)
        self.voice_btn.setToolTip("Voice Input")
        self.voice_btn.setStyleSheet(f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
        border: none;
        border-radius: 20px;
        font-size: 16px;
        color: white;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
    }}
    QPushButton:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['border']}, stop:1 {COLORS['text_trinary']});
    }}
    QPushButton:checked:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['text_trinary']}, stop:1 {COLORS['border']});
    }}
        """)
        self.voice_btn.clicked.connect(self.toggle_voice_input)

    # Text input (center)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Ask {Assistantname} anything...")
        self.input_field.setFixedHeight(40)
        self.input_field.setStyleSheet(f"""
    QLineEdit {{
        background-color: {COLORS['background']};
        border: 2px solid {COLORS['border']};
        border-radius: 20px;
        padding: 0px 16px;
        color: {COLORS['text_primary']};
        font-size: 13px;
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary_blue']};
        background-color: {COLORS['surface']};
    }}
    """)
        self.input_field.returnPressed.connect(self.send_message)

    # Send button (right) - SAME COLOR SCHEME
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 40)
        self.send_btn.setStyleSheet(f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
        color: white;
        border: none;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
    }}
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    """)
        self.send_btn.clicked.connect(self.send_message)

    # Add to input row in correct order: mic, text field, send
        input_row.addWidget(self.voice_btn)
        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)

        input_layout.addLayout(input_row)
        main_layout.addWidget(input_container)

    # Update audio button style
        self.update_audio_button_style()

    # 6. Fix Audio Button Style - SAME COLOR SCHEME
    def update_audio_button_style(self):
        """Update audio button style with SAME COLOR SCHEME"""
        audio_enabled = GetAudioOutputStatus()
        if audio_enabled:
            self.audio_toggle_btn.setStyleSheet(f"""
            QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
        }}
        """)
            self.audio_toggle_btn.setToolTip("Audio: ON - Click to disable")
        else:
            self.audio_toggle_btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['border']}, stop:1 {COLORS['text_trinary']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS['text_trinary']}, stop:1 {COLORS['border']});
        }}
        """)
            self.audio_toggle_btn.setToolTip("Audio: OFF - Click to enable")

    def show_greeting(self):
        """Show initial greeting message"""
        if not self.greeting_shown:
            greeting_messages = [
                f"Hello {Username}! I'm {Assistantname}, your AI assistant.",
                "I'm here to help you with questions, tasks, and conversations.",
                "You can type your message or use the microphone to speak with me.",
                "How can I assist you today?"
            ]
            
            greeting_text = " ".join(greeting_messages)
            self.add_chat_bubble(greeting_text, is_user=False)
            self.greeting_shown = True

    def add_chat_bubble(self, message, is_user=False):
        """Add a chat bubble to the conversation - FIXED VERSION"""
        if not message.strip():
            return
    
    # Create and add bubble
        bubble = ChatBubble(message, is_user)
        self.chat_layout.addWidget(bubble)
    
    # Force layout update
        self.chat_widget.updateGeometry()
    
    # Auto-scroll to bottom after a short delay
        QTimer.singleShot(50, self.scroll_to_bottom)

    def add_system_message(self, message):
        """Add a system message (centered, italic) to the conversation"""
        if not message.strip():
            return
    
    # Create system message widget
        system_widget = QWidget()
        system_layout = QHBoxLayout(system_widget)
        system_layout.setContentsMargins(20, 5, 20, 5)
    
    # System message label
        system_label = QLabel(message)
        system_label.setAlignment(Qt.AlignCenter)
        system_label.setWordWrap(True)
        system_label.setStyleSheet(f"""
            QLabel {{
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-style: italic;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 8px 16px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
    
        system_layout.addWidget(system_label)
        self.chat_layout.addWidget(system_widget)
    
    # Force layout update and scroll
        self.chat_widget.updateGeometry()
        QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scroll chat area to bottom - ENHANCED VERSION"""
    # Force layout update first
        self.chat_widget.adjustSize()
        QApplication.processEvents()
    
    # Scroll to bottom
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # Ensure we're at the bottom with a second attempt
        QTimer.singleShot(100, lambda: scrollbar.setValue(scrollbar.maximum()))

    def _handle_chat_update(self, message, is_user):
        """Thread-safe handler for chat updates"""
        try:
            self.add_chat_bubble(message, is_user)
            if not is_user and GetAudioOutputStatus():
                self.speak_response(message)
        
        # Update status after response is complete
            if not is_user:
                if GetMicrophoneStatus() == "True":
                    SetAssistantStatus("Listening...")
                else:
                    SetAssistantStatus("Ready")
                
        except Exception as e:
            print(f"Error updating chat: {e}")

    def send_message(self):
        """Send user message"""
        message = self.input_field.text().strip()
        if not message:
            return
        
        self.input_field.clear()
        self.add_chat_bubble(message, is_user=True)
        
        # Process message in background
        Thread(target=self.process_user_message, args=(message,), daemon=True).start()

    def process_automation_commands(self, message):
        """Process automation commands from speech or text"""
        try:
            message_lower = message.lower().strip()
            commands = []
        
        # Parse different command types
            if message_lower.startswith(("open ", "launch ", "start ")):
            # Extract app name
                app_name = message_lower.replace("open ", "").replace("launch ", "").replace("start ", "")
                commands.append(f"open {app_name}")
            
            elif message_lower.startswith(("close ", "quit ", "exit ")):
            # Extract app name
                app_name = message_lower.replace("close ", "").replace("quit ", "").replace("exit ", "")
                commands.append(f"close {app_name}")
            
            elif message_lower.startswith(("play ", "youtube ")):
            # Extract search query
                query = message_lower.replace("play ", "").replace("youtube ", "")
                commands.append(f"play {query}")
            
            elif message_lower.startswith(("search ", "google ")):
            # Extract search query
                query = message_lower.replace("search ", "").replace("google ", "")
                commands.append(f"google search {query}")
            
            elif message_lower.startswith("youtube search "):
            # Extract search query
                query = message_lower.replace("youtube search ", "")
                commands.append(f"youtube search {query}")
            
            elif message_lower.startswith(("write ", "content ", "create ")):
            # Extract content topic
                topic = message_lower.replace("write ", "").replace("content ", "").replace("create ", "")
                commands.append(f"content {topic}")
            
            elif message_lower in ["mute", "unmute", "volume up", "volume down"]:
            # System commands
                commands.append(f"system {message_lower}")
            
        # Execute automation commands if any found
            if commands:
            # Run automation in background thread
                Thread(target=self.run_automation, args=(commands,), daemon=True).start()
                return True
            
            return False
        
        except Exception as e:
            print(f"Automation command processing error: {e}")
            return False

    def run_automation(self, commands):
        """Run automation commands asynchronously"""
        try:
        # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run automation
            loop.run_until_complete(Automation(commands))
            loop.close()
        
        # Show success message in chat
            self.update_chat_safe.emit("✓ Command executed successfully", False)
        
        except Exception as e:
            error_msg = f"✗ Automation error: {str(e)}"
            self.update_chat_safe.emit(error_msg, False)
    

    def process_user_message(self, message):
        """Process user message and get response with voice command detection"""
        try:
        # Only set processing status for actual message processing
            process_message = True
        
        # Check for voice commands
            message_lower = message.lower().strip()
        
        # Handle mode switching commands
            if any(phrase in message_lower for phrase in ["rtse mode", "search mode", "search mod", "real time search"]):
                if not self.rtse_mode:
                    self.toggle_rtse_mode()
                QTimer.singleShot(100, lambda: self.add_system_message("Switched to Search Mode"))
                #SetAssistantStatus("Ready")
                process_message = False
        
            if any(phrase in message_lower for phrase in ["summary mode", "summary mod", "brief mode", "short mode"]):
                if not self.summary_mode:
                    self.toggle_response_mode_manual()
                QTimer.singleShot(100, lambda: self.add_system_message("Switched to Summary Mode"))
                #SetAssistantStatus("Ready")
                process_message = False
        
            if any(phrase in message_lower for phrase in ["standard mode", "normal mode", "full mode"]):
                if self.summary_mode:
                    self.toggle_response_mode_manual()
                QTimer.singleShot(100, lambda: self.add_system_message("Switched to Standard Mode"))
                #SetAssistantStatus("Ready")
                process_message = False
        
            if any(phrase in message_lower for phrase in ["ai chat", "chat mode", "ai mode"]):
                if self.rtse_mode:
                    self.toggle_rtse_mode()
                QTimer.singleShot(100, lambda: self.add_system_message("Switched to AI Chat Mode"))
                #SetAssistantStatus("Ready")
                process_message = False
        
        # Handle mic control commands
            elif any(phrase in message_lower for phrase in ["mic off", "microphone off", "stop listening"]):
                self.speech_thread.stop_listening()
                SetMicrophoneStatus("False")
                self.voice_btn.setChecked(False)
                self.update_chat_safe.emit("Microphone turned off", False)
                process_message = False
            
            elif any(phrase in message_lower for phrase in ["mic on", "microphone on", "start listening"]):
                self.speech_thread.start_listening()
                SetMicrophoneStatus("True")
                self.voice_btn.setChecked(True)
                self.update_chat_safe.emit("Microphone turned on", False)
                process_message = False
        
        # Handle audio/speaker control commands
            elif any(phrase in message_lower for phrase in ["audio off", "speaker off", "mute audio", "turn off audio"]):
                SetAudioOutputStatus(False)
                self.update_audio_button_style()
            # Stop current TTS if running
                if self.current_tts_thread and self.current_tts_thread.isRunning():
                    self.current_tts_thread.stop()
                self.update_chat_safe.emit("Audio output turned off", False)
                process_message = False
            
            elif any(phrase in message_lower for phrase in ["audio on", "speaker on", "unmute audio", "turn on audio"]):
                SetAudioOutputStatus(True)
                self.update_audio_button_style()
                self.update_chat_safe.emit("Audio output turned on", False)
                process_message = False
            
             # NEW: Check for automation commands BEFORE processing as chat
            elif self.process_automation_commands(message):
                process_message = False
            
        # Only process message if it's not a command
            if process_message:
            # Set processing status
                SetAssistantStatus("Processing...")
            
            # Store original message for context
                original_message = message
            
            # Process normal message
                if self.rtse_mode:
                # Use search engine
                    response = self.search_engine.process(message, self.conversation_id)
                    #response = self.search_engine.process_query(message)
                else:
                # Use chatbot with summary mode consideration
                    context = db.get_conversation_context(self.conversation_id, limit=5)
                
                # Modify message for summary mode
                    if self.summary_mode:
                        message = f"Please provide a brief, concise summary (2-3 sentences maximum) for this request: {original_message}"
                
                    response = self.chatbot.generate_response(message, context, self.conversation_id)
                
                # Store the original message in database, not the modified one
                    if hasattr(self.chatbot, 'last_conversation_stored') and not self.chatbot.last_conversation_stored:
                        db.add_message(self.conversation_id, "user", original_message)
                        self.chatbot.last_conversation_stored = True
            
                if response and response.strip():
                    self.update_chat_safe.emit(response, False)
            
            # Set back to appropriate status after processing
                if GetMicrophoneStatus() == "True":
                    SetAssistantStatus("Listening...")
                else:
                    SetAssistantStatus("Ready")
        
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.update_chat_safe.emit(error_msg, False)
        # Set back to appropriate status after error
            if GetMicrophoneStatus() == "True":
                SetAssistantStatus("Listening...")
            else:
                SetAssistantStatus("Ready")

    def speak_response(self, text):
        """Convert text to speech"""
        if not GetAudioOutputStatus() or not text.strip():
            return
        
        try:
            # Stop current TTS if running
            if self.current_tts_thread and self.current_tts_thread.isRunning():
                self.current_tts_thread.stop()
                self.current_tts_thread.wait()
            
            # Start new TTS
            self.current_tts_thread = TTSThread(text)
            self.current_tts_thread.finished.connect(self.on_tts_finished)
            self.current_tts_thread.error.connect(self.on_tts_error)
            self.current_tts_thread.start()
            
        except Exception as e:
            print(f"TTS Error: {e}")

    def on_tts_finished(self):
        """Handle TTS completion"""
        pass

    def on_tts_error(self, error):
        """Handle TTS error"""
        print(f"TTS Error: {error}")

    def verify_speech_thread(self):
        """Verify that speech thread is actually listening"""
        try:
            actual_listening = (hasattr(self.speech_thread, '_should_listen') and 
                            self.speech_thread._should_listen and
                            hasattr(self.speech_thread, '_listening_enabled') and 
                            self.speech_thread._listening_enabled)
            mic_status = GetMicrophoneStatus() == "True"
        
            if mic_status and not actual_listening:
                print("Speech thread failed to start - retrying...")
            # Try to restart
                self.speech_thread.stop_listening()
                QTimer.singleShot(200, lambda: self.speech_thread.start_listening())
            elif mic_status and actual_listening:
                print("Speech recognition verified - listening active")
        
        except Exception as e:
            print(f"Error verifying speech thread: {e}")

    def toggle_voice_input(self):
        """Toggle voice input on/off with continuous listening"""
        try:
            current_mic_status = GetMicrophoneStatus() == "True"
    
            if self.voice_btn.isChecked() and not current_mic_status:
        # Start continuous listening
                self.speech_thread.start_listening()
                SetMicrophoneStatus("True")
                SetAssistantStatus("Listening...")

                QTimer.singleShot(500, self.verify_speech_thread)
            else:
        # Stop listening
                self.speech_thread.stop_listening()
                SetMicrophoneStatus("False")
                SetAssistantStatus("Ready")
                self.voice_btn.setChecked(False)

        except Exception as e:
            print(f"Error toggling voice input: {e}")
        # Reset states on error
            SetMicrophoneStatus("False")
            SetAssistantStatus("Ready")
            self.voice_btn.setChecked(False)


    def on_speech_recognized(self, text):
        """Handle recognized speech"""
        if text.strip():
        # Set processing status when speech is recognized
            SetAssistantStatus("Processing...")
            self.input_field.setText(text)
            self.send_message()

    def update_status(self, status):
        """Update status display with proper colors - DEPRECATED, use update_status_display instead"""
    # This method is kept for compatibility but now just calls the new method
        SetAssistantStatus(status)
        self.update_status_display(status)
    
    # Update status colors based on state
        if status == "Ready":
            self.status_dot.setStyleSheet(f"""
        color: {COLORS['primary_blue']};
        font-size: 12px;
            """)
            self.status_label.setStyleSheet(f"""
        color: {COLORS['text_primary']};
        font-size: 12px;
        font-weight: 600;
        font-family: 'Segoe UI', Arial, sans-serif;
            """)
        elif status == "Listening...":
            self.status_dot.setStyleSheet(f"""
        color: {COLORS['text_primary']};
        font-size: 12px;
            """)
            self.status_label.setStyleSheet(f"""
        color: {COLORS['text_primary']};
        font-size: 12px;
        font-weight: 600;
        font-family: 'Segoe UI', Arial, sans-serif;
            """)
        elif status == "Processing...":
            self.status_dot.setStyleSheet(f"""
        color: {COLORS['warning']};
        font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
        color: {COLORS['warning']};
        font-size: 12px;
        font-weight: 600;
        font-family: 'Segoe UI', Arial, sans-serif;
        """)
        else:
            self.status_dot.setStyleSheet(f"""
        color: {COLORS['text_primary']};
        font-size: 12px;
        """)
            self.status_label.setStyleSheet(f"""
        color: {COLORS['text_primary']};
        font-size: 12px;
        font-weight: 600;
        font-family: 'Segoe UI', Arial, sans-serif;
        """)
            

    def update_listening_ui(self, is_listening):
        """Update UI based on listening state"""
        if is_listening:
            #self.animation_label.setText("🎤")
            self.animation_label.setStyleSheet(f"""
        border-radius: 15px;
        color: white;
        font-size: 16px;
            """)
        else:
            self.animation_label.setText("")
            self.animation_label.setStyleSheet(f"""
        border-radius: 15px;
        background-color: {COLORS['surface']};
            """)

    def toggle_response_mode_manual(self):
        """Toggle between standard and summary response modes"""
        self.summary_mode = not self.summary_mode
        if self.summary_mode:
            self.mode_toggle_btn.setText("📋 Summary Mode")
            self.mode_toggle_btn.setStyleSheet(f"""
            QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['surface_light']}, stop:1 {COLORS['border']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
            padding: 0px 16px;
            }}
            QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['border']}, stop:1 {COLORS['surface_light']});
            }}
        """)
        else:
            self.mode_toggle_btn.setText("📝 Standard Mode")
            self.mode_toggle_btn.setStyleSheet(f"""
            QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
            padding: 0px 16px;
            }}
            QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
            }}
            """)


    def toggle_rtse_mode(self):
        """Toggle between AI Chat and Search modes"""
        self.rtse_mode = not self.rtse_mode
        if self.rtse_mode:
            self.rtse_toggle_btn.setText("🔍 Search Mode")
            self.rtse_toggle_btn.setStyleSheet(f"""
            QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['surface_light']}, stop:1 {COLORS['border']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
            padding: 0px 16px;
            }}
            QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['border']}, stop:1 {COLORS['surface_light']});
            }}
            """)
        else:
            self.rtse_toggle_btn.setText("🤖 AI Chat")
            self.rtse_toggle_btn.setStyleSheet(f"""
            QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary_blue']}, stop:1 {COLORS['light_blue']});
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
            padding: 0px 16px;
            }}
            QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['light_blue']}, stop:1 {COLORS['primary_blue']});
            }}
            """)


    def toggle_audio_output(self):
        """Toggle audio output on/off"""
        current_status = GetAudioOutputStatus()
        SetAudioOutputStatus(not current_status)
        self.update_audio_button_style()
        
        # Stop current TTS if disabling audio
        if not GetAudioOutputStatus() and self.current_tts_thread:
            if self.current_tts_thread.isRunning():
                self.current_tts_thread.stop()

    def update_ui(self):
        """Update UI elements periodically with better state management"""
        try:
        # Get current states
            current_status = GetAssistantStatus()
            mic_status = GetMicrophoneStatus()
            is_listening = mic_status == "True"
        
        # Check if speech thread is actually listening (using correct attributes)
            actual_speech_listening = (hasattr(self.speech_thread, '_should_listen') and 
                                    self.speech_thread._should_listen and
                                    hasattr(self.speech_thread, '_listening_enabled') and 
                                    self.speech_thread._listening_enabled)
        
        # Sync UI states with actual states
            if self.voice_btn.isChecked() != is_listening:
                self.voice_btn.setChecked(is_listening)
                self.update_listening_ui(is_listening)
        
        # Fix disconnect: if UI shows listening but speech thread isn't actually listening
            if is_listening and not actual_speech_listening:
                print("Fixing speech thread - restarting listening")
                self.speech_thread.start_listening()
            elif not is_listening and actual_speech_listening:
                print("Fixing speech thread - stopping listening")
                self.speech_thread.stop_listening()
        
        # Update status display
            if self.status_label.text() != current_status:
                self.update_status_display(current_status)
        
        # Ensure proper status based on ACTUAL mic state (only if not processing)
            if current_status not in ["Processing...", "Processingggg..."]:
                if actual_speech_listening and current_status != "Listening...":
                    SetAssistantStatus("Listening...")
                elif not actual_speech_listening and current_status == "Listening...":
                    SetAssistantStatus("Ready")
        
        except Exception as e:
            print(f"UI update error: {e}")


    def hide_window(self):
        """Hide window and show launcher"""
        self.hide()
        self.launcher.show_robot()

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Stop speech recognition
            if hasattr(self, 'speech_thread'):
                self.speech_thread.stop()
            
            # Stop TTS
            if self.current_tts_thread and self.current_tts_thread.isRunning():
                self.current_tts_thread.stop()
                self.current_tts_thread.wait()
            
            # Stop timers
            if hasattr(self, 'timer'):
                self.timer.stop()
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        self.hide()
        self.launcher.show_robot()
        event.ignore()  # Don't actually close, just hide

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