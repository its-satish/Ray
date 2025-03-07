import asyncio
import os
import requests
from random import randint
from PIL import Image
from dotenv import load_dotenv
from time import sleep

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("HuggingFaceAPIKey")

if not API_KEY:
    raise ValueError("API key is missing! Please check your .env file.")

# API details for Hugging Face Stable Diffusion model
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Function to open and display images
def open_images(prompt):
    folder_path = "Data"
    prompt = prompt.replace(" ", "_")

    # List all generated files
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]
    
    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)
        
        try:
            if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                img = Image.open(image_path)
                print(f"Opening image: {image_path}")
                img.show()
                sleep(1)
            else:
                print(f"Skipping {image_path} (file does not exist or is empty)")
        except IOError:
            print(f"Unable to open {image_path}")

# Async function to query Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"API Error {response.status_code}: {response.text}")
        return None
    
    return response.content

# Async function to generate images
async def generate_images(prompt: str):
    tasks = []
    prompt = prompt.replace(" ", "_")

    # Create 4 image generation tasks
    for i in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}"
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    # Wait for all tasks to complete
    image_bytes_list = await asyncio.gather(*tasks)

    # Ensure "Data" folder exists
    os.makedirs("Data", exist_ok=True)

    for i, image_bytes in enumerate(image_bytes_list):
        file_path = f"Data/{prompt}{i + 1}.jpg"
        
        if image_bytes:  # Only save if valid
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            # Verify if the saved file is a valid image
            try:
                Image.open(file_path).verify()  # Check if it's a real image
            except:
                print(f"Error: {file_path} is not a valid image!")
                os.remove(file_path)  # Delete the corrupted file
        else:
            print(f"Skipping {file_path} (API returned invalid data)")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# Main loop to monitor image generation requests
while True:
    try:
        with open("Frontend/Files/ImageGeneration.data", "r") as f:
            data = f.read().strip()

        if not data:
            continue

        prompt, status = data.split(",")

        if status.strip().lower() == "true":
            print("Generating Images ...")
            GenerateImages(prompt=prompt.strip())

            # Reset the status in the file after generating images
            with open("Frontend/Files/ImageGeneration.data", "w") as f:
                f.write("False, False")

            break
        else:
            sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        sleep(1)
