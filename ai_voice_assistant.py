import subprocess
from playsound import playsound
import os

def get_ai_response(prompt):
    # Replace this later with LLaMA integration
    return f"Echo: {prompt}"

def generate_voice(text):
    subprocess.run(f'python tortoise/do_tts.py --text "{text}" --voice random', shell=True)

def play_response():
    playsound("tortoise/results/generated_audio.wav")

if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        response = get_ai_response(user_input)
        print("AI:", response)
        generate_voice(response)
        play_response()
