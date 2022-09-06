import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice

import os
import time
from datetime import datetime
from dotenv import load_dotenv

import api
import config
import database

import logging
from logging.handlers import TimedRotatingFileHandler

fP = os.path.dirname(os.path.realpath(__file__))

load_dotenv()



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






async def debug_predicate(interaction):
	logger.debug(
		"%s was invoked in %i with arguments: %s",
		interaction.command.name, interaction.guild.id, {d['name']:d['value'] for d in interaction.data.get('options', [])}
	)

	return True

debug = app_commands.check(debug_predicate)



class ResidenceSelect(discord.ui.Select):
	def __init__(self):
		opts = [
			discord.SelectOption(label=resName, emoji=resTypeEmote, description=resDescription)
			for resName, resTypeEmote, resDescription in database.laundromat.fetch_all(format_for_select=True)
		]

		super().__init__(placeholder="Choisis l'emplacement de ta laverie", min_values=1, max_values=1, options=opts)


	async def callback(self, interaction: discord.Interaction):
		laundromat = database.laundromat.get(name=self.values[0])

		await interaction.response.defer(ephemeral=True)


		results = await api.fetch_and_parse(parser=laundromat['provider'], url=laundromat['link'])

		content = f"{self.values[0]} - <t:{int(time.time())}:R>"

		#~ Washing Machines embed
		washersEmbed = discord.Embed(
			description="",
			color=0x2f3136
		)
		washersEmbed.set_author(name="Machines à laver")

		availableWashers = [w for w in results['washers'] if w['state'] == 'Available']
		unavailableWashers = [w for w in results['washers'] if w['state'] == 'Unavailable']
		unavailableWashers.sort(key=lambda e: e['available_in'])

		washersEmbed.description += f"{len(availableWashers)}/{len(results['washers'])} machine{'s' if len(availableWashers) > 1 else ''} disponible{'s' if len(availableWashers) > 1 else ''}"

		if len(availableWashers) < len(results['washers']):
			washersEmbed.description += f"\nLes autres se libérent dans {', '.join([uw['available_in'].split(':')[0] for uw in unavailableWashers[:-1]])} et {unavailableWashers[-1]['available_in'].split(':')[0]} minutes"


		#~ Clothes Dryers embed
		dryerEmbed = discord.Embed(
			description="",
			color=0x2f3136
		)
		dryerEmbed.set_author(name="Sèche-Linges")

		availableDryers = [w for w in results['dryers'] if w['state'] == 'Available']
		unavailableDryers = [w for w in results['dryers'] if w['state'] == 'Unavailable']
		unavailableDryers.sort(key=lambda e: e['available_in'])

		dryerEmbed.description += f"{len(availableDryers)}/{len(results['dryers'])} sèche-linge{'s' if len(availableDryers) > 1 else ''} disponible{'s' if len(availableDryers) > 1 else ''}"

		if len(availableDryers) < len(results['dryers']):
			dryerEmbed.description += f"\nLes autres se libérent dans {', '.join([uw['available_in'].split(':')[0] for uw in unavailableDryers[:-1]])} et {uavailableDryers[-1]['available_in'].split(':')[0]} minutes"


		await interaction.followup.edit_message(
			interaction.message.id,
			content=content, view=None, embeds=[washersEmbed, dryerEmbed]
		)



class ResidenceSelectView(discord.ui.View):
	def __init__(self, *, timeout=180):
		super().__init__(timeout=timeout)

		self.add_item(ResidenceSelect())




@slash.command(description="Ajoute ta laverie connectée au bot !")
@app_commands.rename(
	link="url_du_site",
	residence="localisation"
)
@app_commands.describe(
	link="Le lien pour voir le statut en ligne",
	residence="Le nom de la résidence/L'emplacement où est situé la laverie"
)
@debug
async def connect(interaction: discord.Interaction, link: str, residence: str):
	await interaction.response.defer(ephemeral=True)

	# Check that we did not already registered this one
	if link in database.laundromat.get_connected(only_links=True):
		embed = discord.Embed(
			title="Cette laverie est déjà connectée au bot !",
			description="Tu peux donc déjà utiliser la commande /status",
			color=0x0000FF
		)

		await interaction.followup.send(embed=embed)
		return


	embed = discord.Embed(
		title="Laundry connect request",
		description=f"Localisation: {residence}\nLink: {link}",
		color=0xFFFF00
	)
	embed.set_footer(
		text=f"Asked by {interaction.user.name}#{interaction.user.discriminator} / {interaction.user.id}",
		icon_url=interaction.user.avatar.url
	)

	for userid in config.dev_users_id:
		dev = bot.get_user(userid)
		if not dev:
			try:
				dev = await bot.fetch_user(userid)
			except:
				logger.error(f"The user '{userid}' registered as a dev in bot config cannot be found.")
				continue


		await dev.send(embed=embed)


	embed = discord.Embed(
		title="La requête a été envoyée !",
		description="Vous recevrez un message lorsque l'ajout aura été fait",
		color=0x00FF00
	)
	await interaction.followup.send(embed=embed)



@slash.command(description="Vérifie le status de ta laverie")
@debug
async def status(interaction: discord.Interaction):
	await interaction.response.send_message(view=ResidenceSelectView(), ephemeral=True)



bot.run(os.getenv('token'))