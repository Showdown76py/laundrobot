import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice

import os
import time
from datetime import datetime
from dotenv import load_dotenv

import api
import database

import logging
from logging.handlers import TimedRotatingFileHandler

fP = os.path.dirname(os.path.realpath(__file__))



for log_name, log_obj in logging.Logger.manager.loggerDict.items():
	if log_name.startswith("discord"):
		log_obj.level = logging.ERROR


logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.DEBUG,
	datefmt='%Y-%m-%d %H:%M:%S'
)

if not 'logs' in os.listdir(fP): os.mkdir(f"{fP}/logs")
handler = TimedRotatingFileHandler(f"{fP}/logs/laudrobot.log", when="midnight", interval=1)
handler.suffix = "%Y%m%d"
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)


logger.info("Running bot in %s mode", "production" if not config.dev_in_progress else "development")

""" Actual bot code """

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
	command_prefix=commands.when_mentioned_or("laundry:") if not config.dev_in_progress else "laundry;",
	description="Laundrobot | Your laudromat bot",
	intents=intents
)
slash = bot.tree

import utils




@bot.event
async def on_ready():
	logger.info(f"{'<'*12} Logged in as {bot.user.name}#{bot.user.discriminator} {'>'*12}")

	if config.dev_in_progress:
		await bot.change_presence(activity=discord.Game("getting some updates"))

	else:
		await bot.change_presence(activity=discord.Game("monitoring your laundromat"))


bot.run()