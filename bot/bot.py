#!/usr/bin/env python

import os
import aiohttp
import requests
import discord
import json
import time
from discord.ext import tasks
from dotenv import load_dotenv
from modules.logging_setup import _Logging
from modules.ollama_api import _Ollama
from langdetect import detect

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
        self.DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

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

        # Check the message length, ignore anything under 50 characters.
        if len(message.content) < 50 or len(message.content) > 1900:
            self.logging.info(f"Message (under 50 characters, ignoring) {message.author} (User ID: {message.author.id}) Channel: {message.channel} (Channel ID: {message.channel.id}) Server: {message.guild.name} (Server ID: {message.guild.id})")
            return

        # Ignore threads.
        if isinstance(message.channel, discord.Thread):
            self.logging.info(f"Message (in thread) {message.author} (User ID: {message.author.id}) Channel: {message.channel} (Channel ID: {message.channel.id}) Server: {message.guild.name} (Server ID: {message.guild.id})")
            return
        else:
            self.logging.info(f"Message: {message.author} (User ID: {message.author.id}) Channel: {message.channel} (Channel ID: {message.channel.id}) Server: {message.guild.name} (Server ID: {message.guild.id})")

        # Detect the users native language based on the message content.
        try:
            detected_language = detect(message.content)
            if detected_language == "en":
                users_language="English"
                translate_into_language="Japanese"
            elif detected_language == "ja":
                users_language="Japanese"
                translate_into_language="English"
            else:
                # Assume English.
                users_language="English"
                translate_into_language="Japanese"
        except Exception as e:
            self.logging.warning(f"Error detecting language: {e} - we assume English")
            users_language="English"

        # Prepare to send data to AI.
        ai_api_call_start = time.time()

        # Summarise the original message.
        try:
            self.logging.info(f"Sending request to AI - Summarise original message")
            original_message_summary = _Ollama.ollama_query(self.OLLAMA_URL,self.OLLAMA_TOKEN,self.OLLAMA_MODEL,[
                { "role": "user",
                 "content": f"Please summarise the following message. Do not provide anything else but the summary: {message.content}"
                }
                ])
        except Exception as e:
            self.logging.error(f"Issue with AI (summary): {e}")
            return

        # Translate the original message.
        try:
            self.logging.info(f"Sending request to AI - Translate original message (from {users_language} into {translate_into_language})")
            translated_message = _Ollama.ollama_query(self.OLLAMA_URL,self.OLLAMA_TOKEN,self.OLLAMA_MODEL,[
                { "role": "user",
                 "content": f"Please translate this message from {users_language} into {translate_into_language}. Do not provide anything else but the summary: {message.content}"
                }
                ])
        except Exception as e:
            self.logging.error(f"Issue with AI (translation): {e}")
            return

        # Translate the summary.
        try:
            self.logging.info(f"Sending request to AI - Translate original message summary (from {users_language} into {translate_into_language})")
            translated_message_summary = _Ollama.ollama_query(self.OLLAMA_URL,self.OLLAMA_TOKEN,self.OLLAMA_MODEL,[
                { "role": "user",
                 "content": f"Please translate this message from {users_language} into {translate_into_language}. Do not provide anything else but the summary: {translated_message}"
                }
                ])
        except Exception as e:
            self.logging.error(f"Issue with AI (translation summary): {e}")
            return

        # Log result.
        ai_api_call_duration = time.time() - ai_api_call_start
        self.logging.info(f"AI response (duration: {ai_api_call_duration} seconds)")

        # Convert the repsonse to a dictionary.
        discord_message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

        # Prepare Discord webhook embed.
        webhook_payload = {
                "username": "KKL Bot",
                "avatar_url": "https://cdn.discordapp.com/avatars/1316008262121816094/7c772c0978df400f722b0a2f119e5142.png",
                "content": f"Message author / メッセージ作成者: `{message.author}` Channel / チャネル: `{message.channel}`",
                "embeds": [
                    {
                        "title": "Original message / 元のメッセージ",
                        "description": f"{message.content}",
                        "color": 255,
                        "fields": [
                            {
                                "name": "Summary",
                                "value": f"{original_message_summary}",
                                "inline": False
                            }
                        ]
                    },
                    {
                        "title": "Translated message",
                        "description": f"{translated_message}",
                        "color": 65280,
                        "fields": [
                            {
                                "name": "Message summary / メッセージの概要",
                                "value": f"{translated_message_summary}",
                                "inline": False
                            }
                        ]
                    },
                    {
                        "title": "Other",
                        "color": 16753920,
                        "fields": [
                            {
                                "name": "AI model / AIモデル",
                                "value": f"`{self.OLLAMA_MODEL}`",
                                "inline": True
                            },
                            {
                                "name": "Generation time / 生成時間",
                                "value": f"`{ai_api_call_duration:.2f} seconds`",
                                "inline": True
                            },
                            {
                                "name": "Original Message Link / 元のメッセージリンク",
                                "value": f"[View message / メッセージを見る]({discord_message_link})",
                                "inline": False
                            }
                        ]
                    }
                ]
            }

        # Send the message to Discord.
        try:
            webhook_response = requests.post(self.DISCORD_WEBHOOK_URL, json=webhook_payload)
        except Exception as e:
            self.logging.error(f"Webhook POST error: {e}")
            return
        finally:
            if webhook_response.status_code == 204:
                self.logging.info(f"Webhook sent successfully about user {message.author} in {message.guild.name}")
            else:
                self.logging.error(f"Failed to send webhook. Status: {webhook_response.status_code}, Reason: {webhook_response.text}")


# Create the bot instance and run it.
bot = KklBot()
bot.run(TOKEN)
