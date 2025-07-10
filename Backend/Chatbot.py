# Enhanced Chatbot.py - Added summarization capabilities like RTSE
from groq import Groq
import datetime
from dotenv import dotenv_values
import os
import sys
from typing import List, Tuple, Optional
import re

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Data.database import db

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment variables")

client = Groq(api_key=GroqAPIKey)

class ChatBot:
    def __init__(self):
        """Initialize the enhanced chatbot"""
        self.client = client
        self.max_context_messages = 10
        self.system_prompt = self._build_system_prompt()
        self.concise_system_prompt = self._build_concise_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the standard system prompt for the chatbot"""
        current_time = datetime.datetime.now()
        return f"""You are {Assistantname}, an intelligent AI assistant created to help {Username}.

Key Instructions:
1. Be helpful, concise, and professional
2. Maintain context from previous messages
3. Provide accurate and relevant responses
4. Use proper grammar and punctuation
5. If you don't know something, admit it honestly

Current Context:
- Date: {current_time.strftime('%A, %B %d, %Y')}
- Time: {current_time.strftime('%I:%M %p')}
- User: {Username}

Respond naturally and helpfully to the user's queries."""

    def _build_concise_system_prompt(self) -> str:
        """Build the concise system prompt similar to RTSE"""
        current_time = datetime.datetime.now()
        return f"""You are {Assistantname}, an AI assistant that provides concise, summarized responses.

Instructions:
1. Provide concise answers in 2-4 lines maximum
2. Include only the most relevant information
3. Be accurate and to the point
4. Format clearly with line breaks if needed
5. Remove unnecessary details and examples
6. Focus on key facts and main points
7. Use simple, clear language

Current Context:
- Date: {current_time.strftime('%A, %B %d, %Y')}
- Time: {current_time.strftime('%I:%M %p')}
- User: {Username}

Provide a concise summary response in 2-4 lines."""

    def generate_response(self, query: str, context: List[Tuple] = None, 
                         conversation_id: str = None, summarize: bool = False) -> str:
        """
        Generate response with optional summarization
        
        Args:
            query: User's input query
            context: List of (role, content) tuples for conversation context
            conversation_id: Current conversation ID
            summarize: Whether to generate a concise summary response
            
        Returns:
            Generated response string
        """
        try:
            # Choose system prompt based on summarize flag
            system_prompt = self.concise_system_prompt if summarize else self.system_prompt
            
            # Build message history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add context if provided
            if context:
                # Limit context to prevent token overflow
                recent_context = context[-self.max_context_messages:]
                for role, content in recent_context:
                    if role in ["user", "assistant"] and content.strip():
                        messages.append({"role": role, "content": content})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Generate response with summarization parameters if needed
            if summarize:
                response = self._call_concise_llm(messages)
            else:
                response = self._call_llm(messages)
            
            return self._clean_response(response, summarize)
            
        except Exception as e:
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            print(f"ChatBot Error: {e}")
            return error_msg

    def _call_llm(self, messages: List[dict]) -> str:
        """Make standard API call to Groq"""
        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
                stream=False
            )
            
            response = completion.choices[0].message.content
            if not response:
                return "I'm sorry, I couldn't generate a response. Please try again."
                
            return response
            
        except Exception as e:
            print(f"LLM API Error: {e}")
            return "I'm having trouble connecting to my language model. Please try again in a moment."

    def _call_concise_llm(self, messages: List[dict]) -> str:
        """Make API call for concise responses (similar to RTSE)"""
        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=150,   # Reduced for shorter responses (same as RTSE)
                top_p=0.9,
                stream=False
            )
            
            response = completion.choices[0].message.content
            
            # Post-process to ensure concise output (same as RTSE)
            if response:
                # Split into lines and take first 4 non-empty lines
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                response = '\n'.join(lines[:4])
                return response
            
            return "Unable to generate concise response."
            
        except Exception as e:
            print(f"Concise LLM API Error: {e}")
            return "Having trouble generating concise response. Please try again."

    def _clean_response(self, response: str, is_concise: bool = False) -> str:
        """Clean and format the response"""
        if not response:
            return "I apologize, but I couldn't generate a proper response."
        
        # Remove common artifacts
        cleaned = response.strip()
        cleaned = cleaned.replace("</s>", "")
        cleaned = cleaned.replace("<|end|>", "")
        
        # Additional cleaning for concise responses (similar to RTSE)
        if is_concise:
            # Remove citations and references
            cleaned = re.sub(r'\(Source:.*?\)', '', cleaned)
            cleaned = re.sub(r'\[.*?\]', '', cleaned)
            # Remove URLs
            cleaned = re.sub(r'http\S+|www\.\S+', '', cleaned)
        
        # Remove excessive whitespace
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Ensure proper sentence ending
        if cleaned and not cleaned.endswith(('.', '!', '?', ':')):
            cleaned += '.'
        
        return cleaned

    def generate_summary_response(self, query: str, context: List[Tuple] = None, 
                                conversation_id: str = None) -> str:
        """
        Generate a concise summary response (wrapper method)
        
        Args:
            query: User's input query
            context: List of (role, content) tuples for conversation context
            conversation_id: Current conversation ID
            
        Returns:
            Concise summary response
        """
        return self.generate_response(query, context, conversation_id, summarize=True)

    def generate_streaming_response(self, query: str, context: List[Tuple] = None, 
                                  summarize: bool = False):
        """
        Generate streaming response for real-time UI updates with optional summarization
        
        Args:
            query: User's input query
            context: List of (role, content) tuples for conversation context
            summarize: Whether to generate concise responses
            
        Yields:
            Response chunks as they're generated
        """
        try:
            # Choose system prompt based on summarize flag
            system_prompt = self.concise_system_prompt if summarize else self.system_prompt
            
            # Build message history
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                recent_context = context[-self.max_context_messages:]
                for role, content in recent_context:
                    if role in ["user", "assistant"] and content.strip():
                        messages.append({"role": role, "content": content})
            
            messages.append({"role": "user", "content": query})
            
            # Stream response with appropriate parameters
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.3 if summarize else 0.7,
                max_tokens=150 if summarize else 1024,
                top_p=0.9,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error: {str(e)}"

    def get_conversation_summary(self, conversation_id: str, concise: bool = False) -> str:
        """Get a summary of the conversation for context with optional concise mode"""
        try:
            # Get conversation messages
            context_messages = db.get_conversation_context(conversation_id, limit=20)
            
            if not context_messages:
                return "No conversation history found."
            
            # Build summary prompt
            conversation_text = "\n".join([f"{role}: {content}" for role, content in context_messages])
            
            if concise:
                summary_prompt = f"""Provide a brief 2-3 line summary of this conversation:

{conversation_text}

Concise Summary:"""
            else:
                summary_prompt = f"""Please provide a brief summary of this conversation:

{conversation_text}

Summary:"""
            
            messages = [
                {"role": "system", "content": self.concise_system_prompt if concise else "You are a helpful assistant that summarizes conversations."},
                {"role": "user", "content": summary_prompt}
            ]
            
            if concise:
                response = self._call_concise_llm(messages)
            else:
                response = self._call_llm(messages)
                
            return self._clean_response(response, concise)
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def handle_follow_up(self, query: str, conversation_id: str, summarize: bool = False) -> str:
        """Handle follow-up questions with conversation context and optional summarization"""
        try:
            # Get recent context from database
            context = db.get_conversation_context(conversation_id, limit=6)
            
            # Add context awareness to the prompt
            enhanced_query = f"""Based on our conversation history, please respond to: {query}

Consider the context of our previous discussion when providing your answer."""
            
            return self.generate_response(enhanced_query, context, conversation_id, summarize)
            
        except Exception as e:
            return f"Error handling follow-up: {str(e)}"

    def get_capabilities(self) -> str:
        """Return information about chatbot capabilities including summarization"""
        return f"""I'm {Assistantname}, and I can help you with:

• General conversation and questions
• Information and explanations
• Creative writing and brainstorming
• Problem-solving assistance
• Task planning and organization
• Code explanations (basic level)
• Mathematical calculations
• Language translation help
• Concise summaries (similar to search responses)

Response Modes:
• Standard: Detailed, comprehensive responses
• Summary: Concise 2-4 line responses (like search engine)

For real-time information or web searches, I'll work with the search engine.
For system tasks like opening apps, I'll coordinate with the task handlers.

How can I assist you today?"""

# Standalone testing
if __name__ == "__main__":
    print(f"Enhanced {Assistantname} ChatBot with Summarization - Ready for testing")
    bot = ChatBot()
    
    # Test conversation
    test_conversation_id = "test_conv_001"
    
    print(f"\n{Assistantname}: {bot.get_capabilities()}")
    print("\nCommands: 'summary' for concise mode, 'standard' for normal mode, 'exit' to quit")
    
    summarize_mode = False
    
    while True:
        try:
            mode_indicator = "[SUMMARY]" if summarize_mode else "[STANDARD]"
            user_input = input(f"\n{Username} {mode_indicator}: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print(f"\n{Assistantname}: Goodbye! Have a great day!")
                break
            elif user_input.lower() == 'summary':
                summarize_mode = True
                print(f"\n{Assistantname}: Switched to concise summary mode (2-4 lines)")
                continue
            elif user_input.lower() == 'standard':
                summarize_mode = False
                print(f"\n{Assistantname}: Switched to standard detailed mode")
                continue
                
            if not user_input:
                continue
                
            # Get context from database
            context = db.get_conversation_context(test_conversation_id, limit=5)
            
            # Add user message to database
            db.add_message("user", user_input, test_conversation_id)
            
            # Generate response with appropriate mode
            response = bot.generate_response(user_input, context, test_conversation_id, summarize_mode)
            
            # Add response to database
            db.add_message("assistant", response, test_conversation_id)
            
            print(f"\n{Assistantname}: {response}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Assistantname}: Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")