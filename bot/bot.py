#!/usr/bin/env python

import os
import aiohttp
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from modules.logging_setup import _Logging
from modules.ollama_api import _Ollama
from langdetect import detect

# Set up logging

# Load .env settings
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the .env file")

class KklBot(discord.Client):
    def __init__(self):
        # Set up logging
        self.logging = _Logging.logging_setup()

        load_dotenv()
        self.OLLAMA_URL = os.getenv("OLLAMA_URL")
        self.OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

        # Init the bot.
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    async def setup_hook(self):
        # Start background task
        self.background_task.start()

        # Set up an HTTP session
        self.session = aiohttp.ClientSession()

    @tasks.loop(minutes=5)
    async def background_task(self):
        try:
            self.logging.info("Running background task...")
            # future task logic goes here.
        except Exception as e:
            self.logging.error(f"Background task encountered an error: {e}")

    async def on_ready(self):
        self.logging.info(f"{self.user.name} has connected to Discord!")
        self.logging.info(f"Bot is ready. Logged in as {self.user.name} (ID: {self.user.id})")

    async def close(self):
        self.logging.info("Shutting down bot...")
        self.background_task.cancel()
        await super().close()
        await self.session.close()

    # Log messages while testing.
    async def on_message(self, message: discord.Message):
        """Log user messages."""
        if message.author == self.user:
            return  # Ignore messages from the bot itself

        # Log the message for now.
        try:
            # Detect the language of the message
            detected_language = detect(message.content)
            # If language is detected as English (en) or Japanese (ja), return it
            if detected_language == "en":
                users_language="English"
            elif detected_language == "ja":
                users_language="Japanese"
            else:
                users_language="Unknown"
        except Exception as e:
            self.logging.warning(f"Error detecting language: {e}")
            users_language="Unknown"

        self.logging.info(f"Message from {message.author} Content: {message.content}")

        # Prepare to send data to AI.
        ai_system_message = """
            You are a Discord bot, and your job is to review message content from users.

            You understand both English and Japanese and should act as an intermediate real-time translator who summarizes messages.

            Sometimes user messages will contain a mix of English and Japanese, so you should decide what the native language is based on which language the majority of the message is written in.

            You should always perform the following tasks without fail:
            1) Take note of the original message.
            2) Provide a summary of the original message in the user's native language.
            3) Translate the original message into either English or Japanese (e.g., If the user's native language is English, translate the original message into Japanese. Or, if the user's native language is Japanese, translate the original message into English.).
            4) Provide a summary of the translated message in the respective language that it was translated into.
            5) Take note of what language was translated into.
            6) Personalise the message, always refer to the username when speaking about the user.

            Anything outside these tasks, you MUST not act. You MUST NOT provide any other information to the user other than the requested tasks.

            Respond with the following keys in valid JSON format and NEVER use markdown in your response:
            - native_language
            - original_message
            - original_message_summary
            - translated_message
            - translated_message_summary
            """

        ai_interactions = [
            {
                "role": "system",
                "content": f"{ai_system_message}"
            },
            {
                "role": "user",
                "content": f"Username: {message.author} Original message: {message.content} Native language detected: {users_language}"
            }
        ]

        # Send request to AI.
        try:
            ai_response = _Ollama.ollama_query(self.OLLAMA_URL,self.OLLAMA_TOKEN,self.OLLAMA_MODEL,ai_interactions)
        except Exception as e:
            self.logging.error(f"Issue with AI: {e}")

        # Log result.
        self.logging.info(f"AI response: {ai_response}")

# Create the bot instance and run it.
bot = KklBot()
bot.run(TOKEN)
