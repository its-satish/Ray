import sys
import os
import traceback
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database_connection():
    """Check if database is accessible and working"""
    print("=== DATABASE CONNECTION TEST ===")
    try:
        from Data.database import db
        
        # Test basic database operations
        test_conv_id = f"debug_test_{int(datetime.now().timestamp())}"
        
        # Add a test message
        message_id = db.add_message(
            role="user",
            content="Debug test message",
            conversation_id=test_conv_id
        )
        print(f"✓ Successfully added message with ID: {message_id}")
        
        # Retrieve the message
        messages = db.get_conversation_messages(test_conv_id)
        print(f"✓ Retrieved {len(messages)} messages")
        
        # Check unprocessed messages
        unprocessed = db.get_unprocessed_messages()
        print(f"✓ Found {len(unprocessed)} unprocessed messages")
        
        # Test marking as processed
        db.mark_as_processed(message_id)
        print("✓ Successfully marked message as processed")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        traceback.print_exc()
        return False

def check_chat_processor():
    """Check if chat processor is working"""
    print("\n=== CHAT PROCESSOR TEST ===")
    try:
        # Import the chat processor
        from Backend.chat_processor import EnhancedChatProcessor
        
        processor = EnhancedChatProcessor()
        print("✓ Successfully imported EnhancedChatProcessor")
        
        # Test message generation
        test_response = processor.generate_response("Hello test")
        print(f"✓ Generated test response: {test_response[:50]}...")
        
        return True
        
    except ImportError as e:
        print(f"✗ Could not import EnhancedChatProcessor: {e}")
        print("This might be why you're not getting responses!")
        return False
    except Exception as e:
        print(f"✗ Chat processor test failed: {e}")
        traceback.print_exc()
        return False

def check_file_structure():
    """Check if required files and directories exist"""
    print("\n=== FILE STRUCTURE CHECK ===")
    
    required_files = [
        "Data/database.py",
        "Backend/chat_processor.py",
        ".env"
    ]
    
    required_dirs = [
        "Data",
        "Backend", 
        "Frontend",
        "Frontend/Files",
        "Frontend/Graphics"
    ]
    
    all_good = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ Directory exists: {directory}")
        else:
            print(f"✗ Missing directory: {directory}")
            all_good = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ Missing file: {file_path}")
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check environment variables"""
    print("\n=== ENVIRONMENT VARIABLES CHECK ===")
    try:
        from dotenv import dotenv_values
        env_vars = dotenv_values(".env")
        
        required_vars = ["Username", "Assistantname", "InputLanguage"]
        
        for var in required_vars:
            value = env_vars.get(var)
            if value:
                print(f"✓ {var}: {value}")
            else:
                print(f"✗ Missing or empty: {var}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking environment variables: {e}")
        return False

def run_full_integration_test():
    """Run a full integration test"""
    print("\n=== FULL INTEGRATION TEST ===")
    try:
        from Data.database import db
        
        # Create test conversation
        test_conv_id = f"integration_test_{int(datetime.now().timestamp())}"
        print(f"Created test conversation: {test_conv_id}")
        
        # Step 1: Add user message
        message_id = db.add_message(
            role="user",
            content="Hello, this is a test message",
            conversation_id=test_conv_id
        )
        print(f"✓ Added user message: {message_id}")
        
        # Step 2: Check if it's unprocessed
        unprocessed = db.get_unprocessed_messages()
        test_message_found = any(
            (isinstance(msg, dict) and msg.get('id') == message_id) or 
            (isinstance(msg, tuple) and len(msg) > 0 and msg[0] == message_id)
            for msg in unprocessed
        )
        
        if test_message_found:
            print("✓ Message found in unprocessed queue")
        else:
            print("✗ Message NOT found in unprocessed queue")
            return False
        
        # Step 3: Try to process with chat processor
        try:
            from Backend.chat_processor import EnhancedChatProcessor
            processor = EnhancedChatProcessor()
            processor.process_pending_messages()
            print("✓ Ran chat processor")
            
            # Step 4: Check if response was generated
            messages = db.get_conversation_messages(test_conv_id)
            assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
            
            if assistant_messages:
                print(f"✓ Generated {len(assistant_messages)} assistant response(s)")
                for msg in assistant_messages:
                    print(f"  Response: {msg['content'][:50]}...")
                return True
            else:
                print("✗ No assistant responses generated")
                return False
                
        except ImportError:
            print("✗ Cannot import chat processor - this is the likely cause of no responses")
            return False
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("CHAT SYSTEM DIAGNOSTIC TOOL")
    print("=" * 40)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Environment Variables", check_environment_variables),
        ("Database Connection", check_database_connection),
        ("Chat Processor", check_chat_processor),
        ("Full Integration", run_full_integration_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 40)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    if all(results.values()):
        print("\n✓ All tests passed! Your system should be working.")
    else:
        print("\n✗ Some tests failed. Check the errors above.")
        print("\nMost likely causes for no responses:")
        print("1. Missing Backend/chat_processor.py file")
        print("2. EnhancedChatProcessor not properly imported")
        print("3. Chat processor not running in separate thread")
        print("4. Database connection issues")

if __name__ == "__main__":
    main()