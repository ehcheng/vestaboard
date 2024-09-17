import sys
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Vestaboard Read/Write API endpoint and credentials
API_URL = "https://rw.vestaboard.com/"
API_KEY = os.getenv('VESTABOARD_READ_WRITE_KEY')

def update_vestaboard(text):
    """Send the formatted text to Vestaboard."""
    headers = {
        'X-Vestaboard-Read-Write-Key': API_KEY,
        'Content-Type': 'application/json',
    }
    data = {'text': text}
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        print("Vestaboard updated successfully!")
        print(f"Response: {response.json()}")
    else:
        print(f"Failed to update Vestaboard. Status code: {response.status_code}")
        print(f"Response: {response.text}")

def read_file(file_path):
    """Read the contents of a text file."""
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python updateVestaBoard.py <text_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    text_content = read_file(file_path)
    update_vestaboard(text_content)
