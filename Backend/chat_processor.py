import time
import threading
import traceback
from datetime import datetime
import sys
import os

# Add project root to Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Data.database import db

class EnhancedChatProcessor:
    def __init__(self):
        self.is_running = False
        self.processing_thread = None
        self.debug = True
        self.currently_processing = set()
        self.processed_messages = set()  # Track processed messages to prevent duplicates
        
    def log_debug(self, message):
        """Debug logging function"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[DEBUG {timestamp}] ChatProcessor: {message}")
    
    def start_processing(self):
        """Start the message processing loop"""
        self.is_running = True
        self.log_debug("Starting chat processor...")
    
        while self.is_running:
            try:
                self.process_pending_messages()
                time.sleep(1)  # Increased to reduce system load
            except Exception as e:
                self.log_debug(f"Error in processing loop: {e}")
                time.sleep(2)
    
    def process_pending_messages(self):
        """Process pending user messages with duplicate prevention"""
        try:
            unprocessed = db.get_unprocessed_messages(limit=5)  # Reduced batch size
            
            if unprocessed:
                self.log_debug(f"Processing {len(unprocessed)} messages")
            
            for message_data in unprocessed:
                try:
                    message_id = message_data['id']
                    content = message_data['content']
                    conversation_id = message_data['conversation_id']
                    
                    # Create simple message identifier to prevent duplicates
                    message_key = f"{message_id}_{conversation_id}"
                    
                    # Skip if already processed or currently processing
                    if (message_id in self.currently_processing or 
                        message_key in self.processed_messages):
                        continue
                        
                    self.currently_processing.add(message_id)
                    self.processed_messages.add(message_key)
                    
                    self.log_debug(f"Processing message {message_id}")
                    
                    # Mark as processed BEFORE generating response
                    db.mark_as_processed(message_id)
                    
                    # Generate concise response
                    response = self.generate_response(content, conversation_id)
                    
                    # Only add response if it's not empty and under length limit
                    if response and len(response.strip()) > 0:
                        # Ensure response is concise (max 200 characters, 2-4 lines)
                        response = self.ensure_concise_response(response)
                        
                        response_id = db.add_message(
                            role="assistant",
                            content=response,
                            conversation_id=conversation_id,
                            parent_message_id=message_id,
                            is_processed=True  # Mark assistant messages as processed immediately
                        )
                        
                        if response_id:
                            self.log_debug(f"Response added for message {message_id}")
                        else:
                            self.log_debug(f"Duplicate response prevented for message {message_id}")
                    
                except Exception as e:
                    self.log_debug(f"Error processing message {message_id}: {e}")
                finally:
                    self.currently_processing.discard(message_id)
                    
        except Exception as e:
            self.log_debug(f"Error in process_pending_messages: {e}")

    def ensure_concise_response(self, response):
        """Ensure response is concise and professional (2-4 lines max)"""
        lines = response.strip().split('\n')
        
        # Remove empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        # Limit to 4 lines maximum
        if len(lines) > 4:
            lines = lines[:4]
            if not lines[-1].endswith('.'):
                lines[-1] += '.'
        
        # Join lines and ensure total length doesn't exceed 200 characters
        result = '\n'.join(lines)
        if len(result) > 200:
            # Truncate and add ellipsis
            result = result[:197] + '...'
        
        return result

    def generate_response(self, user_message, conversation_id=None):
        """Generate concise, professional responses"""
        try:
            user_message_lower = user_message.lower().strip()
            
            # Get conversation context for better responses
            context = db.get_conversation_context(conversation_id, limit=3) if conversation_id else []
            
            # Professional greeting responses
            if any(greeting in user_message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
                return "Hello! How may I assist you today?"
            
            # Time/Date queries
            if any(time_word in user_message_lower for time_word in ['time', 'clock']):
                return f"Current time: {datetime.now().strftime('%H:%M:%S')}"
            
            if any(date_word in user_message_lower for date_word in ['date', 'today', 'day']):
                return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            
            # Weather queries
            if 'weather' in user_message_lower:
                return "Please check your local weather service for current conditions."
            
            # Help/Command queries
            if user_message_lower.startswith('/help') or 'help' in user_message_lower:
                return "Available: /time, /date, /help\nAsk questions or give commands for assistance."
            
            # Question handling
            if user_message_lower.endswith('?'):
                if len(user_message) < 20:
                    return "Could you provide more details about your question?"
                else:
                    return f"I understand your question about {self.extract_topic(user_message)}.\nHow can I help you with this?"
            
            # Thank you responses
            if any(thanks in user_message_lower for thanks in ['thank', 'thanks', 'appreciate']):
                return "You're welcome! Anything else I can help with?"
            
            # Goodbye responses
            if any(bye in user_message_lower for bye in ['bye', 'goodbye', 'see you', 'farewell']):
                return "Goodbye! Have a great day!"
            
            # Task/Action requests
            if any(action in user_message_lower for action in ['do', 'make', 'create', 'write', 'generate']):
                return f"I'll help you with that task.\nPlease provide specific details about what you need."
            
            # Default professional response
            topic = self.extract_topic(user_message)
            if len(user_message) > 50:
                return f"I've received your message about {topic}.\nHow would you like me to proceed?"
            else:
                return f"Regarding {topic} - what specific assistance do you need?"
                
        except Exception as e:
            self.log_debug(f"Error generating response: {e}")
            return "I apologize for the technical issue. Please try rephrasing your request."
    
    def extract_topic(self, message):
        """Extract main topic from user message for professional responses"""
        # Remove common words and extract key terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        words = message.lower().replace('?', '').replace('.', '').replace(',', '').split()
        key_words = [word for word in words if word not in common_words and len(word) > 2]
        
        if key_words:
            return ' '.join(key_words[:3])  # First 3 key words
        else:
            return "your request"
    
    def stop_processing(self):
        """Stop the message processing"""
        self.log_debug("Stopping chat processor...")
        self.is_running = False
        # Clear processing sets
        self.currently_processing.clear()
        self.processed_messages.clear()


# Test function with duplicate prevention
def test_chat_processor():
    """Test the enhanced chat processor"""
    print("Testing Enhanced Chat Processor...")
    
    try:
        from Data.database import db
        
        test_conv_id = f"test_conv_{int(datetime.now().timestamp())}"
        
        # Add test messages
        test_messages = [
            "Hello, how are you?",
            "What's the weather like?",
            "Can you help me with a task?",
            "Thank you for your help!"
        ]
        
        for msg in test_messages:
            message_id = db.add_message(
                role="user",
                content=msg,
                conversation_id=test_conv_id,
                is_processed=False
            )
            print(f"Added test message: {message_id} - {msg}")
        
        # Process messages
        processor = EnhancedChatProcessor()
        processor.process_pending_messages()
        
        # Check results
        messages = db.get_conversation_messages(test_conv_id)
        print(f"\nConversation Results ({len(messages)} total messages):")
        
        for msg in messages:
            role_indicator = "👤" if msg['role'] == 'user' else "🤖"
            print(f"{role_indicator} {msg['role'].title()}: {msg['content']}")
            print(f"   Processed: {msg['is_processed']}")
            print()
            
    except Exception as e:
        print(f"Test failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    test_chat_processor()