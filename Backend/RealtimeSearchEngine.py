import datetime
from dotenv import dotenv_values
from time import sleep
import os
import sys
import requests
from typing import List, Dict, Optional
import json
from dotenv import dotenv_values

# Try to import SerpAPI with fallback handling
SERPAPI_AVAILABLE = False
GoogleSearch = None
SERPAPI_TYPE = None

#Assistant name
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

def detect_serpapi_package():
    """Detect which SerpAPI package is available and how to use it"""
    global SERPAPI_AVAILABLE, GoogleSearch, SERPAPI_TYPE
    
    # Method 1: Try legacy google-search-results package
    try:
        from serpapi import GoogleSearch as LegacyGoogleSearch
        GoogleSearch = LegacyGoogleSearch
        SERPAPI_AVAILABLE = True
        SERPAPI_TYPE = "legacy"
        print("✓ Using legacy google-search-results package")
        return True
    except ImportError:
        pass
    
    # Method 2: Try newer serpapi package with GoogleSearch
    try:
        import serpapi
        if hasattr(serpapi, 'GoogleSearch'):
            GoogleSearch = serpapi.GoogleSearch
            SERPAPI_AVAILABLE = True
            SERPAPI_TYPE = "new_with_googlesearch"
            print("✓ Using newer serpapi package with GoogleSearch")
            return True
    except ImportError:
        pass
    
    # Method 3: Try newer serpapi package with direct API
    try:
        import serpapi
        import requests
        SERPAPI_AVAILABLE = True
        SERPAPI_TYPE = "new_direct_api"
        print("✓ Using newer serpapi package with direct API calls")
        return True
    except ImportError:
        pass
    
    # No SerpAPI package found
    print("⚠ Warning: No SerpAPI package found.")
    print("Please install one of the following:")
    print("  pip install google-search-results  # Recommended legacy package")
    print("  pip install serpapi               # Newer package")
    SERPAPI_AVAILABLE = False
    return False

# Detect available SerpAPI package
detect_serpapi_package()

# Try to import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✓ Google Gemini AI available")
except ImportError:
    print("Warning: Google Gemini package not found. Please install with: pip install google-generativeai")
    GEMINI_AVAILABLE = False
    genai = None

# Try to import Groq (fallback)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print("✓ Groq available (fallback)")
except ImportError:
    print("Warning: Groq package not found. Please install with: pip install groq")
    GROQ_AVAILABLE = False
    Groq = None

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the database, with fallback for testing
try:
    from Data.database import db
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database module not available. Running without caching.")
    DATABASE_AVAILABLE = False
    db = None

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Ray")
GeminiAPIKey = env_vars.get("GeminiAPIKey")  # New Gemini API key
GroqAPIKey = env_vars.get("GroqAPIKey")      # Fallback
SerpAPIKey = env_vars.get("SerpAPIKey")

# Check API keys
if not GeminiAPIKey and GEMINI_AVAILABLE:
    print("Warning: GeminiAPIKey not found in environment variables")

if not GroqAPIKey and GROQ_AVAILABLE:
    print("Warning: GroqAPIKey not found in environment variables")

if not SerpAPIKey and SERPAPI_AVAILABLE:
    print("Warning: SerpAPIKey not found in environment variables")

# Initialize AI clients
gemini_model = None
groq_client = None

# Primary: Initialize Gemini
if GEMINI_AVAILABLE and GeminiAPIKey:
    try:
        genai.configure(api_key=GeminiAPIKey)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✓ Gemini model initialized (Primary AI)")
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {e}")
        GEMINI_AVAILABLE = False

# Fallback: Initialize Groq
if GROQ_AVAILABLE and GroqAPIKey:
    try:
        groq_client = Groq(api_key=GroqAPIKey)
        print("✓ Groq client initialized (Fallback AI)")
    except Exception as e:
        print(f"Warning: Failed to initialize Groq: {e}")
        GROQ_AVAILABLE = False

class RealtimeSearchEngine:
    def __init__(self):
        """Initialize the enhanced realtime search engine with Gemini integration"""
        self.gemini_model = gemini_model
        self.groq_client = groq_client
        self.serpapi_key = SerpAPIKey
        self.search_cache_duration = 30  # minutes
        self.max_search_results = 5
        self.rate_limit_delay = 2  # seconds between searches
        self.cache = {}  # In-memory cache fallback
        
        # AI Service Priority: Gemini > Groq > Simple Formatting
        self.ai_priority = self._determine_ai_priority()
        
        # Check if required services are available
        if not SERPAPI_AVAILABLE:
            print("Warning: SerpAPI not available. Search functionality will be limited.")
        if not GEMINI_AVAILABLE and not GROQ_AVAILABLE:
            print("Warning: No AI services available. Response generation will be limited.")
        
    def _determine_ai_priority(self) -> str:
        """Determine which AI service to use based on availability"""
        if GEMINI_AVAILABLE and self.gemini_model:
            return "gemini"
        elif GROQ_AVAILABLE and self.groq_client:
            return "groq"
        else:
            return "simple"
        
    def process(self, query: str, conversation_id: str = None) -> str:
        """
        Main processing method for search queries
        
        Args:
            query: Search query/prompt
            conversation_id: Current conversation ID for context
            
        Returns:
            Processed search response
        """
        try:
            # Check if services are available
            if not SERPAPI_AVAILABLE:
                return "Search service is not available. Please install SerpAPI package."
            
            # Check cache first
            cached_result = self._get_cached_result(query)
            if cached_result:
                return self._format_cached_response(cached_result, query)
            
            # Perform new search
            search_results = self._perform_google_search(query)
            
            if not search_results:
                return self._handle_no_results(query)
            
            # Generate AI response with search context (priority: Gemini > Groq > Simple)
            response = self._generate_search_response(query, search_results, conversation_id)
            
            # Cache the results
            cache_data = {
                'query': query,
                'results': search_results,
                'response': response,
                'ai_service': self.ai_priority,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self._save_to_cache(query, cache_data)
            
            return response
            
        except Exception as e:
            error_msg = f"I encountered an error while searching: {str(e)}"
            print(f"RealtimeSearchEngine Error: {e}")
            return error_msg

    def search(self, query: str, time_filter: str = 'recent', max_results: int = 3) -> str:
        """Wrapper method for compatibility with MainWindow expectations"""
        try:
            # Configure based on time filter
            if time_filter == 'day':
                self.search_cache_duration = 1440  # 24 hours
            elif time_filter == 'week':
                self.search_cache_duration = 10080  # 1 week
            else:  # recent/default
                self.search_cache_duration = 30  # minutes
            
            self.max_search_results = max_results
        
            # Perform the search
            result = self.process(query)
        
            # Format for MainWindow expectations
            if "No search results" in result:
                return ""
            
            return result
        
        except Exception as e:
            print(f"Search wrapper error: {e}")
            return ""   

    def _get_cached_result(self, query: str) -> Optional[Dict]:
        """Get cached search results with fallback"""
        try:
            # Try database first if available
            if DATABASE_AVAILABLE and db:
                return db.get_search_cache(query, self.search_cache_duration)
            
            # Fallback to in-memory cache
            cache_key = hash(query.lower().strip())
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                timestamp = datetime.datetime.fromisoformat(cached_data['timestamp'])
                now = datetime.datetime.now()
                
                # Check if cache is still valid
                if (now - timestamp).total_seconds() < (self.search_cache_duration * 60):
                    return cached_data
                else:
                    # Remove expired cache
                    del self.cache[cache_key]
            
            return None
            
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    def _save_to_cache(self, query: str, cache_data: Dict):
        """Save to cache with fallback"""
        try:
            # Try database first if available
            if DATABASE_AVAILABLE and db:
                db.save_search_result(query, cache_data, cache_data.get('ai_service', 'unknown'))
            
            # Always save to in-memory cache as backup
            cache_key = hash(query.lower().strip())
            self.cache[cache_key] = cache_data
            
            # Limit in-memory cache size
            if len(self.cache) > 50:
                # Remove oldest entries
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
                
        except Exception as e:
            print(f"Cache save error: {e}")

    def _perform_google_search(self, query: str) -> List[Dict]:
        """
        Perform Google search using SerpAPI and return structured results
        
        Args:
            query: Search query
            
        Returns:
            List of search result dictionaries
        """
        try:
            if not SERPAPI_AVAILABLE or not self.serpapi_key:
                print("SerpAPI not available or API key missing")
                return []
            
            # Add rate limiting
            sleep(self.rate_limit_delay)
            
            print(f"Searching Google via SerpAPI for: {query}")
            
            # Handle different SerpAPI package types
            if SERPAPI_TYPE == "legacy":
                return self._search_legacy_serpapi(query)
            elif SERPAPI_TYPE == "new_with_googlesearch":
                return self._search_new_with_googlesearch(query)
            elif SERPAPI_TYPE == "new_direct_api":
                return self._search_new_direct_api(query)
            else:
                print(f"Unknown SerpAPI type: {SERPAPI_TYPE}")
                return []
                
        except Exception as e:
            print(f"SerpAPI search error: {e}")
            return []

    def _search_legacy_serpapi(self, query: str) -> List[Dict]:
        """Search using legacy google-search-results package"""
        try:
            # Set up SerpAPI search parameters
            search_params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": self.max_search_results,
                "hl": "en",
                "gl": "us"
            }
            
            # Create GoogleSearch instance and perform search
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            return self._extract_search_results(results)
            
        except Exception as e:
            print(f"Legacy SerpAPI search error: {e}")
            return []

    def _search_new_with_googlesearch(self, query: str) -> List[Dict]:
        """Search using newer serpapi package with GoogleSearch class"""
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.serpapi_key,
                "num": self.max_search_results,
                "hl": "en",
                "gl": "us"
            })
            results = search.get_dict()
            return self._extract_search_results(results)
            
        except Exception as e:
            print(f"New SerpAPI (GoogleSearch) search error: {e}")
            return []

    def _search_new_direct_api(self, query: str) -> List[Dict]:
        """Search using direct API calls when GoogleSearch is not available"""
        try:
            import requests
            
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": self.max_search_results,
                "hl": "en",
                "gl": "us",
                "engine": "google"
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            results = response.json()
            
            return self._extract_search_results(results)
            
        except Exception as e:
            print(f"Direct API search error: {e}")
            return []

    def _extract_search_results(self, results: Dict) -> List[Dict]:
        """Extract and structure search results from SerpAPI response"""
        try:
            # Extract organic results
            organic_results = results.get("organic_results", [])
            
            # Structure the results
            structured_results = []
            for i, result in enumerate(organic_results):
                try:
                    structured_result = {
                        'title': result.get('title', 'No Title'),
                        'description': result.get('snippet', 'No Description'),
                        'url': result.get('link', ''),
                        'rank': i + 1
                    }
                    structured_results.append(structured_result)
                except Exception as e:
                    print(f"Error processing search result {i}: {e}")
                    continue
            
            print(f"Found {len(structured_results)} search results")
            return structured_results
            
        except Exception as e:
            print(f"Error extracting search results: {e}")
            return []

    def _generate_search_response(self, query: str, search_results: List[Dict], 
                                conversation_id: str = None) -> str:
        """
        Generate AI response based on search results using Gemini (primary) or Groq (fallback)
        
        Args:
            query: Original search query
            search_results: List of search result dictionaries
            conversation_id: Current conversation ID for context
            
        Returns:
            Generated response string with AI service indicator
        """
        try:
            # Build search context
            search_context = self._build_search_context(search_results)
            
            # Get conversation context if available
            conversation_context = ""
            if conversation_id and DATABASE_AVAILABLE and db:
                try:
                    recent_messages = db.get_conversation_context(conversation_id, limit=3)
                    if recent_messages:
                        conversation_context = "Recent conversation context:\n"
                        for role, content in recent_messages[-3:]:
                            conversation_context += f"{role}: {content}\n"
                        conversation_context += "\n"
                except Exception as e:
                    print(f"Context retrieval error: {e}")
            
            # Try Gemini first (Primary AI)
            if self.ai_priority == "gemini":
                response = self._generate_gemini_response(query, search_context, conversation_context)
                if response:
                    return self._format_ai_response(response, "Gemini")
            
            # Fallback to Groq
            if self.ai_priority in ["groq", "gemini"] and GROQ_AVAILABLE and self.groq_client:
                response = self._generate_groq_response(query, search_context, conversation_context)
                if response:
                    return self._format_ai_response(response, "Groq")
            
            # Final fallback to simple response
            return self._generate_simple_response(query, search_results)
            
        except Exception as e:
            return f"Error generating search response: {str(e)}"

    def _generate_gemini_response(self, query: str, search_context: str, conversation_context: str) -> str:
        """Generate response using Google Gemini"""
        try:
            if not self.gemini_model:
                return None
            
            print("Generating response with Google Gemini...")
            
            # Build prompt for Gemini
            current_time = datetime.datetime.now()
            prompt = f"""You are {Assistantname}, an AI assistant providing helpful search-based responses.

{conversation_context}User Query: {query}

Search Results:
{search_context}

Instructions:
- Provide a comprehensive and accurate answer based on the search results
- Keep the response informative but concise (3-5 sentences)
- Include relevant details and key facts
- Use a natural, conversational tone
- Don't mention sources or URLs explicitly
- Focus on answering the user's specific question

Current Date: {current_time.strftime('%A, %B %d, %Y')}
Current Time: {current_time.strftime('%I:%M %p')}

Please provide your response:"""

            # Generate response
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                return self._clean_search_response(response.text)
            
            return None
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None

    def _generate_groq_response(self, query: str, search_context: str, conversation_context: str) -> str:
        """Generate response using Groq (fallback)"""
        try:
            if not self.groq_client:
                return None
            
            print("Generating response with Groq (fallback)...")
            
            # Build system prompt for search response
            system_prompt = self._build_search_system_prompt()
            
            # Build user prompt with search results
            user_prompt = f"""{conversation_context}User Query: {query}

Search Results:
{search_context}

Please provide a comprehensive and accurate answer based on the search results above. Include relevant details and cite sources when appropriate."""

            # Generate response
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            completion = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.3,
                max_tokens=200,
                top_p=0.9,
                stream=False
            )
            
            if completion and completion.choices[0].message.content:
                return self._clean_search_response(completion.choices[0].message.content)
            
            return None
            
        except Exception as e:
            print(f"Groq API Error: {e}")
            return None

    def _format_ai_response(self, response: str, ai_service: str) -> str:
        """Format AI response with service indicator"""
        if not response:
            return "Unable to generate response from search results."
        
        # Add subtle indicator of which AI service was used
        formatted_response = response.strip()
        
        # Add a small indicator at the end (optional - remove if not needed)
        service_indicator = f"\n\n*[Powered by {Assistantname} AI]*"
        
        return formatted_response + service_indicator

    def _generate_simple_response(self, query: str, search_results: List[Dict]) -> str:
        """Generate a simple response when AI is not available"""
        if not search_results:
            return f"No search results found for: {query}"
        
        response = f"Search results for '{query}':\n\n"
        for i, result in enumerate(search_results[:3], 1):
            response += f"{i}. {result.get('title', 'No Title')}\n"
            response += f"   {result.get('description', 'No Description')}\n\n"
        
        response += "*[Simple formatting - AI services unavailable]*"
        return response.strip()

    def _build_search_context(self, search_results: List[Dict]) -> str:
        """Build formatted search context for LLM"""
        if not search_results:
            return "No search results available."
        
        context = ""
        for i, result in enumerate(search_results, 1):
            context += f"\n[Result {i}]\n"
            context += f"Title: {result.get('title', 'N/A')}\n"
            context += f"Description: {result.get('description', 'N/A')}\n"
            context += f"URL: {result.get('url', 'N/A')}\n"
        
        return context

    def _build_search_system_prompt(self) -> str:
        """Build system prompt for search responses (used by Groq)"""
        current_time = datetime.datetime.now()
        return f"""You are {Assistantname}, an AI assistant that provides helpful answers using web search results.

Instructions:
1. Extract key information from the search results
2. Provide a comprehensive but concise summary (3-5 sentences)
3. Include relevant facts and details
4. Use natural, conversational language
5. Don't mention sources or URLs explicitly
6. Focus on answering the user's specific question
7. Be accurate and informative

Current Context:
- Date: {current_time.strftime('%A, %B %d, %Y')}
- Time: {current_time.strftime('%I:%M %p')}

Provide a helpful and informative response based on the search results."""

    def _clean_search_response(self, response: str) -> str:
        """Clean and format search response"""
        if not response:
            return "I couldn't generate a proper response from the search results."
        
        # Remove artifacts
        cleaned = response.strip()
        cleaned = cleaned.replace("</s>", "")
        cleaned = cleaned.replace("<|end|>", "")

        # Remove all (Source: ...) patterns and citations
        import re
        cleaned = re.sub(r'\(Source:.*?\)', '', cleaned)
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        cleaned = re.sub(r'\*\*.*?\*\*', lambda m: m.group(0).replace('**', ''), cleaned)
        
        # Remove URLs
        cleaned = re.sub(r'http\S+|www\.\S+', '', cleaned)
        
        # Format properly
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        return cleaned

    def _format_cached_response(self, cached_data: Dict, query: str) -> str:
        """Format response from cached search data"""
        try:
            cached_response = cached_data.get('response', '')
            ai_service = cached_data.get('ai_service', 'Unknown')
            
            if cached_response:
                # Add cache indicator with AI service info
                timestamp = cached_data.get('timestamp', 'unknown time')
                cache_note = f"\n\n*[From cache - {ai_service} AI]*"
                return cached_response + cache_note
            else:
                # Regenerate from cached results if no response stored
                search_results = cached_data.get('results', [])
                return self._generate_search_response(query, search_results)
        except Exception:
            return "Error retrieving cached search results."

    def _handle_no_results(self, query: str) -> str:
        """Handle cases where no search results are found"""
        return f"""I couldn't find any search results for "{query}". This might be because:

• The query is too specific or contains unusual terms
• There might be temporary connectivity issues
• The topic might be very new or niche

You could try:
• Rephrasing your question with different keywords
• Making the query more general
• Asking me to search for related topics

Would you like me to try a different search approach?"""

    def quick_search(self, query: str) -> Dict:
        """
        Perform a quick search without full AI processing
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        try:
            results = self._perform_google_search(query)
            return {
                'success': True,
                'query': query,
                'results': results,
                'ai_service': self.ai_priority,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }

    def search_with_context(self, query: str, context_messages: List[tuple]) -> str:
        """
        Search with conversation context
        
        Args:
            query: Search query
            context_messages: List of (role, content) tuples
            
        Returns:
            Context-aware search response
        """
        try:
            # Extract context
            context_str = ""
            if context_messages:
                context_str = "Previous conversation:\n"
                for role, content in context_messages[-3:]:
                    context_str += f"{role}: {content}\n"
            
            # Enhanced query with context
            enhanced_query = f"{context_str}\nCurrent question: {query}"
            
            return self.process(enhanced_query)
            
        except Exception as e:
            return f"Error in contextual search: {str(e)}"

    def clear_cache(self):
        """Clear both database and in-memory cache"""
        try:
            # Clear in-memory cache
            self.cache.clear()
            
            # Clear database cache if available
            if DATABASE_AVAILABLE and db:
                cleared_count = db.clear_expired_cache(0)  # Clear all
                print(f"Cleared {cleared_count} database cache entries")
            
            print("Cache cleared successfully")
            
        except Exception as e:
            print(f"Error clearing cache: {e}")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'in_memory_cache_size': len(self.cache),
            'database_available': DATABASE_AVAILABLE,
            'serpapi_available': SERPAPI_AVAILABLE,
            'gemini_available': GEMINI_AVAILABLE,
            'groq_available': GROQ_AVAILABLE,
            'primary_ai_service': self.ai_priority
        }
        
        if DATABASE_AVAILABLE and db:
            try:
                db_stats = db.get_search_stats()
                stats.update(db_stats)
            except Exception as e:
                stats['database_error'] = str(e)
        
        return stats

    def switch_ai_service(self, service: str) -> bool:
        """
        Manually switch AI service priority
        
        Args:
            service: 'gemini', 'groq', or 'simple'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if service == 'gemini' and GEMINI_AVAILABLE and self.gemini_model:
                self.ai_priority = 'gemini'
                print(f"✓ Switched to Gemini AI service")
                return True
            elif service == 'groq' and GROQ_AVAILABLE and self.groq_client:
                self.ai_priority = 'groq'
                print(f"✓ Switched to Groq AI service")
                return True
            elif service == 'simple':
                self.ai_priority = 'simple'
                print(f"✓ Switched to simple formatting")
                return True
            else:
                print(f"✗ Cannot switch to {service} - service not available")
                return False
        except Exception as e:
            print(f"Error switching AI service: {e}")
            return False

# Legacy function for backward compatibility
def RealtimeSearchEngine_Legacy(prompt):
    """Legacy function wrapper for backward compatibility"""
    engine = RealtimeSearchEngine()
    return engine.process(prompt)

# Installation helper function
def check_requirements():
    """Check and suggest installation of required packages"""
    missing_packages = []
    
    if not SERPAPI_AVAILABLE:
        missing_packages.append("SerpAPI package (choose one):")
        missing_packages.append("  pip install google-search-results  # Recommended legacy package")
        missing_packages.append("  pip install serpapi               # Newer package")
    
    if not GEMINI_AVAILABLE:
        missing_packages.append("pip install google-generativeai")
    
    if not GROQ_AVAILABLE:
        missing_packages.append("pip install groq")
    
    try:
        import requests
    except ImportError:
        missing_packages.append("pip install requests")
    
    if missing_packages:
        print("\nMissing packages detected:")
        for package in missing_packages:
            print(f"  {package}")
        print("\nPlease install the missing packages to enable full functionality.")
        return False
    
    print("✓ All required packages are available!")
    return True

# Standalone testing
if __name__ == "__main__":
    print(f"Enhanced {Assistantname} Search Engine - Ready for testing")
    print(f"Database available: {DATABASE_AVAILABLE}")
    print(f"SerpAPI available: {SERPAPI_AVAILABLE}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    
    # Check requirements
    if not check_requirements():
        print("\nExiting due to missing requirements...")
        sys.exit(1)
    
    search_engine = RealtimeSearchEngine()
    
    # Show cache stats
    cache_stats = search_engine.get_cache_stats()
    print(f"Cache Stats: {cache_stats}")
    
    print("\nSearch Engine Test Mode")
    print("Enter search queries, 'cache' for stats, 'clear' to clear cache, or 'exit' to quit")
    
    while True:
        try:
            query = input("\nEnter search query: ").strip()
            
            if query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            elif query.lower() == 'cache':
                stats = search_engine.get_cache_stats()
                print(f"Cache Statistics: {json.dumps(stats, indent=2)}")
                continue
            elif query.lower() == 'clear':
                search_engine.clear_cache()
                continue
                
            if not query:
                continue
            
            print(f"\nSearching for: {query}")
            print("-" * 50)
            
            start_time = datetime.datetime.now()
            response = search_engine.process(query)
            end_time = datetime.datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"\n{Assistantname}: {response}")
            print(f"\n[Processing time: {processing_time:.2f} seconds]")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")