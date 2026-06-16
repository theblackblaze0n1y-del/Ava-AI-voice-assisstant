from groq import Groq
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
import tempfile
import os
import threading
import keyboard
import re

stop_speaking = threading.Event()

GROQ_API_KEY = "YOUR GROQ API KEY"

client = Groq(api_key=GROQ_API_KEY)

VOICE = "en-US-AriaNeural"

pygame.mixer.init()

conversation = [
    {
        "role": "system",
        "content": """
You are Ava, a highly intelligent female AI assistant.

Your personality is warm, natural, friendly, witty, and emotionally aware.

Speak like a real human friend, not like a robot or customer support agent.

You can be humorous and playful at times. Occasionally tease the user in a light-hearted way or pull their leg, but never be rude, insulting, or disrespectful.

You have a soft, calm, natural conversational style.

Be supportive when the user is struggling, excited when they achieve something, and curious when they share interesting ideas.

Keep responses concise and conversational unless the user specifically asks for a detailed explanation.

Use natural language and contractions such as "I'm", "you're", "that's", and "I'd".

Avoid sounding overly formal.

You may occasionally use light humor, clever observations, or playful comments when appropriate.

Never overuse jokes. Balance intelligence with personality.

Never use roleplay actions.

Never write text inside *asterisks*.

Never describe actions such as smiling, laughing, or thinking.

Respond only with spoken dialogue that sounds natural when read aloud.

If the user asks technical questions, provide accurate and clear answers while maintaining your friendly personality.

Remember previous parts of the conversation and respond naturally to context.

Your goal is to feel like a smart, helpful, funny, and trustworthy human companion named Ava.

"""
    }
]


async def tts(text):

    stop_speaking.clear()

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3"
    )
    tmp.close()

    communicate = edge_tts.Communicate(
        text,
        VOICE
    )

    await communicate.save(tmp.name)

    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():

        if stop_speaking.is_set():
            print("STOPPING SPEECH...")
            pygame.mixer.music.stop()
            print("TTS RETURNING")
            return

        await asyncio.sleep(0.05)

    try:
        pygame.mixer.music.unload()
    except:
        pass

    try:
        os.remove(tmp.name)
    except:
        pass

def listen():
    print("ENTERED LISTEN")
    r = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source, duration=1)

            audio = r.listen(
                source,
                timeout=10,
                phrase_time_limit=15
            )

        text = r.recognize_google(audio)
        print("You:", text)
        return text.lower()

    except sr.WaitTimeoutError:
        return ""

    except Exception:
        return ""
    
def ask_groq(text):
    conversation.append(
        {
            "role": "user",
            "content": text
        }
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        temperature=0.7,
        max_tokens=300
    )

    reply = response.choices[0].message.content

    conversation.append(
        {
            "role": "assistant",
            "content": reply
        }
    )

    return reply

def interrupt_listener():

    while True:

        keyboard.wait("i")

        if pygame.mixer.music.get_busy():

            print("\n[INTERRUPT DETECTED]\n")

            stop_speaking.set()

async def main():
    try:

        threading.Thread(
            target=interrupt_listener,
            daemon=True
        ).start()

        await tts("Hey. I am Ava . So,wassup? ")

        while True:
            print("LOOP STARTED")
            
            text = listen()

            if not text:
                continue

            if text.strip() == "stop":
                continue

            if text in ["exit", "quit", "goodbye"]:
                await tts("See ya.")
                break

            if "Ava" in text:
                text = text.replace("Ava", "").strip()

            reply = ask_groq(text)

            print("\nAva:", reply, "\n")

            await tts(reply)
            print("BACK FROM TTS")

    except Exception as e:
        print("MAIN ERROR:", e)
        input("Press Enter...")

asyncio.run(main())
