from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
<<<<<<< HEAD
import time  # Added for proper delays

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")  # Default to en-US if not set

# HTML Code with improved speech recognition
=======

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
# Get the input language setting from the environment variables.
InputLanguage = env_vars.get("InputLanguage")
# Define the HTML code for the speech recognition interface.
>>>>>>> 9c5cf6a2519cd1b02854e9a55419503dac015cb8
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
    <style>
        #output {
            min-height: 20px;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <button id="start">Start Recognition</button>
    <button id="end" disabled>Stop Recognition</button>
    <div id="output">Status: Ready</div>
    <script>
        const output = document.getElementById('output');
        const startBtn = document.getElementById('start');
        const endBtn = document.getElementById('end');
        let recognition;

        startBtn.addEventListener('click', () => {
            try {
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = document.body.getAttribute('data-lang') || 'en-US';
                recognition.continuous = true;
                recognition.interimResults = true;

                recognition.onstart = () => {
                    output.textContent = 'Listening... Speak now';
                    startBtn.disabled = true;
                    endBtn.disabled = false;
                };

                recognition.onresult = (event) => {
                    const transcript = Array.from(event.results)
                        .map(result => result[0].transcript)
                        .join('');
                    output.textContent = transcript;
                };

                recognition.onerror = (event) => {
                    output.textContent = 'Error: ' + event.error;
                    startBtn.disabled = false;
                    endBtn.disabled = true;
                };

                recognition.onend = () => {
                    if (startBtn.disabled) {
                        recognition.start();  // Continue listening
                    }
                };

                recognition.start();
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            }
        });

        endBtn.addEventListener('click', () => {
            if (recognition) {
                recognition.stop();
                startBtn.disabled = false;
                endBtn.disabled = true;
            }
        });
    </script>
</body>
</html>'''
<<<<<<< HEAD
=======
# Replace the language setting in the HTML code with the input language from the environment variables.
HtmlCode = str(HtmlCode).replace("recognition.lang '';", f"recognition.lang = '{InputLanguage}';")
# Write the modified HTML code to a file.
os.makedirs("Data", exist_ok=True)
with open(r"Data\Voice.html", "w") as f:
    f.write(HtmlCode)
# Get the current working directory.
current_dir = os.getcwd()
# Generate the file path for the HTML file.
Link = f"{current_dir}/Data/Voice.html"
>>>>>>> 9c5cf6a2519cd1b02854e9a55419503dac015cb8

# Set language in HTML
HtmlCode = HtmlCode.replace('<body>', f'<body data-lang="{InputLanguage}">')

# Write HTML file
os.makedirs("Data", exist_ok=True)
with open(r"Data\Voice.html", "w") as f:
    f.write(HtmlCode)

current_dir = os.getcwd()
Link = f"file:///{current_dir}/Data/Voice.html"

# Chrome options
chrome_options = Options()
#chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
<<<<<<< HEAD
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1
})

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Helper functions
def SetAssistantStatus(Status):
    os.makedirs("Frontend/Files", exist_ok=True)
    with open(r'Frontend/Files/Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    if not Query:
        return Query
        
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    
=======
chrome_options.add_argument("--headless=new")
# Initialize the Chrome WebDriver using the ChromeDriverManager.
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
# Define the path for temporary files.
TempDirPath = rf"{current_dir}/Frontend/Files"
os.makedirs(TempDirPath, exist_ok=True)

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}/Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

# Function to modify a query to ensure proper punctuation and formatting.
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's", "can you"]
    # Check if the query is a question and add a question mark if necessary.
>>>>>>> 9c5cf6a2519cd1b02854e9a55419503dac015cb8
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()
<<<<<<< HEAD
=======

# Function to translate text into English using the mtranslate library
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# Function to perform speech recognition using the WebDriver.
def SpeechRecognition():
    # Open the HTML file in the browser.
    driver.get("file:///" + Link)
    # Start speech recognition by clicking the start button.
    driver.find_element(by=By.ID, value="start").click()
    while True:
        try:
            # Get the recognized text from the HTML output element.
            Text = driver.find_element(by=By.ID, value="output").text
            if Text:
                # Stop recognition by clicking the stop button.
                driver.find_element(by=By.ID, value="end").click()
                # If the input language is English, return the modified query.
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    # If the input language is not English, translate the text and return it.
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception as e:
            pass
>>>>>>> 9c5cf6a2519cd1b02854e9a55419503dac015cb8

def UniversalTranslator(Text):
    if not Text:
        return Text
    try:
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    except:
        return Text

# Speech recognition function
def SpeechRecognition():
    driver.get(Link)
    time.sleep(1)  # Wait for page to load
    
    start_button = driver.find_element(By.ID, "start")
    start_button.click()
    
    last_text = ""
    timeout = time.time() + 15  # 15 second timeout
    
    while time.time() < timeout:
        try:
            current_text = driver.find_element(By.ID, "output").text.strip()
            
            if current_text and current_text != "Listening... Speak now":
                if current_text == last_text:  # Text hasn't changed for a while
                    driver.find_element(By.ID, "end").click()
                    return current_text
                last_text = current_text
                
        except Exception as e:
            pass
        
        time.sleep(0.5)
    
    driver.find_element(By.ID, "end").click()
    return ""

# Main execution
if __name__ == "__main__":
    try:
        while True:
<<<<<<< HEAD
            print("Speak now (waiting for input)...")
            recognized_text = SpeechRecognition()
            
            if recognized_text:
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    final_text = QueryModifier(recognized_text)
                else:
                    SetAssistantStatus("Translating...")
                    final_text = QueryModifier(UniversalTranslator(recognized_text))
                
                print("You said:", final_text)
            else:
                print("No speech detected or timeout reached")
                
=======
            Text = SpeechRecognition()
            if Text:
                print(Text)
>>>>>>> 9c5cf6a2519cd1b02854e9a55419503dac015cb8
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        driver.quit()