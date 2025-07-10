from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import pyqtSignal, QPropertyAnimation, QEasingCurve, Qt, QPoint
from PyQt5.QtGui import QPixmap, QCursor
import os

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
        self.drag_start_position = None
        self.is_dragging = False
        self.drag_threshold = 10  # Increased threshold
        
        # Make it a top-level widget for better control
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
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
            self.drag_start_position = event.globalPos()
            self.is_dragging = False
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            event.accept()
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_start_position is not None:
            # Calculate movement distance
            distance = (event.globalPos() - self.drag_start_position).manhattanLength()
            
            if distance > self.drag_threshold:
                self.is_dragging = True
                
                # Calculate new position
                current_pos = self.pos()
                movement = event.globalPos() - self.drag_start_position
                new_pos = current_pos + movement
                
                # Get screen geometry and constrain position
                screen = QApplication.primaryScreen()
                screen_rect = screen.availableGeometry()
                
                # Constrain to screen boundaries
                new_x = max(screen_rect.left(), min(new_pos.x(), screen_rect.right() - self.width()))
                new_y = max(screen_rect.top(), min(new_pos.y(), screen_rect.bottom() - self.height()))
                
                constrained_pos = QPoint(new_x, new_y)
                self.move(constrained_pos)
                
                # Update drag start position for smooth dragging
                self.drag_start_position = event.globalPos()
                
                # Debug output
                print(f"Moving to: {constrained_pos}, Screen: {screen_rect}")
                
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ArrowCursor))
            
            if not self.is_dragging:
                # This was a click, not a drag
                print("Button clicked!")
                if self.toggle_callback:
                    self.toggle_callback()
                self.clicked.emit()
            else:
                print("Drag ended")
            
            # Reset drag state
            self.drag_start_position = None
            self.is_dragging = False
            event.accept()
    
    def enterEvent(self, event):
        """Handle mouse enter events"""
        self.stop_breathing()
        self.setCursor(QCursor(Qt.OpenHandCursor))
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
        self.setCursor(QCursor(Qt.ArrowCursor))
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
    
    def show_at_position(self, x, y):
        """Show the button at a specific screen position"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # Constrain to screen boundaries
        constrained_x = max(screen_rect.left(), min(x, screen_rect.right() - self.width()))
        constrained_y = max(screen_rect.top(), min(y, screen_rect.bottom() - self.height()))
        
        self.move(constrained_x, constrained_y)
        self.show()
        print(f"Button positioned at: ({constrained_x}, {constrained_y})")
    
    def cleanup(self):
        """Clean up animations when widget is destroyed"""
        if hasattr(self, 'breathing_animation'):
            self.breathing_animation.stop()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Example usage:
button = FloatingButton(toggle_callback=your_callback_function)
button.show_at_position(100, 100)  # Show at specific position