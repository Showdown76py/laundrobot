"""
	Author: Gaëtan
	Usage: Discord bot global utility functionnalities

	Requirements: 
		Import after "bot" and "logger" definition (So must define these two)
		Have a config file with these variables defined:
			report_error_webhook, dev_report_id

"""

from __main__ import bot, logger
import config

import os
import aiohttp
import sqlite3
import subprocess
import traceback

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import hybrid_command, hybrid_group, is_owner



def is_an_owner():
	async def predicate(ctx):
		return ctx.author.id in config.dev_users_id
	return commands.check(predicate)



@bot.hybrid_group(name="admin")
@is_an_owner()
async def administration(ctx):
	...


@administration.command(
	name="sync",
	description="Synchronize bot commands"
)
@app_commands.describe(
	everywhere="Set to True if you want to sync the bot globally"
)
@app_commands.default_permissions(administrator=True)
@is_an_owner()
async def synchronize(ctx, everywhere: bool=False):
	if everywhere:
		synced = await bot.tree.sync()

	else:
		synced = await bot.tree.sync(guild=ctx.guild)

	logger.debug("Synced %i AppCommand", len(synced))


	if ctx.interaction:
		await ctx.send('✅', ephemeral=True)
	else:
		try:
			await ctx.message.add_reaction('✅')
		except commands.MissingPermissions:
			await ctx.message.reply('✅')



@administration.command(
	name="whereisbot",
	description="Check the guilds the bot is in"
)
@app_commands.default_permissions(administrator=True)
@is_an_owner()
async def whereareyou(ctx):
	e = discord.Embed(description="", color=0x2f3136)
	e.set_author(name=f"Currently in {len(bot.guilds)} guilds", icon_url=bot.user.avatar.url)

	for guild in bot.guilds:
		invite = guild.vanity_url
		if not invite:
			for channel in guild.channels:
				if isinstance(channel, discord.TextChannel):
					invite = await channel.create_invite(
						max_uses=2,
						reason="Bot admin(s) might join through this link."
					)
					break

		e.description += f"`{guild.id}` -> [{guild.name}]({invite if isinstance(invite, str) else invite.url})" "\n"


	if len(e.description) < 4096:
		await ctx.reply(embed=e, ephemeral=True)

	else:
		with open('temp.txt', 'w') as f:
			f.write(e.description)

		await ctx.reply(file=discord.File('temp.txt'), ephemeral=True)

		os.remove('temp.txt')



@administration.command(
	name="database",
	description="Get the bot database(s)"
)
@app_commands.describe(
	specific="Input a file path if you don't want all local databases"
)
@app_commands.default_permissions(administrator=True)
@is_an_owner()
async def database(ctx, specific: str=None):
	if specific:
		if os.path.exists(specific):
			await ctx.reply(file=discord.File(specific), ephemeral=True)
		else:
			if ctx.interaction:
				await ctx.send('❌')
			else:
				try:
					await ctx.message.add_reaction('❌')
				except commands.MissingPermissions:
					await ctx.message.reply('❌')


	else:
		files = []
		for file in os.listdir():
			if file.split('.')[-1] in ['db', 'json', 'database', 'sqlite', 'sqlite3']:
				files.append(discord.File(file))

		await ctx.reply(files=files, ephemeral=True)



@administration.command(
	name="eval",
	description="Remotely execute code on bot server"
)
@app_commands.describe(
	command="Input the code to execute"
)
@app_commands.default_permissions(administrator=True)
@is_an_owner()
async def evaluate(ctx, command: str):
	await ctx.defer(ephemeral=True)


	result = subprocess.run(command, shell=True, capture_output=True)

	rslt = result.stdout if result.returncode == 0 else result.stderr
	rslt = bytearray( rslt.decode('windows-1252'), 'utf-8' ).decode("utf-8")

	rslt = rslt.strip('\r')

	if len(rslt) == 0:
		rslt = "Return data empty. Returning return-code: " + str(result.returncode)

	d = {"‚": "é", "Š": "è", "ˆ": "ê", "œ": "£", "æ": "µ", "‡": "ç", "ÿ": " "} # lastone is unknown
	for el in d:
		rslt = rslt.replace(el, d[el])


	embed = discord.Embed(
		description=f"```cmd\n{command}\n\n{rslt}\n```",
		color=0x2f3136
	)

	if len(embed.description) < 4096:
		await ctx.reply(embed=embed, ephemeral=True)
	else:
		with open('log.txt', 'w', encoding="utf-8") as f:
			f.write(embed.description)

		await ctx.reply(file=discord.File('log.txt'), ephemeral=True)

		os.remove('log.txt')




#~~ Error handling

@bot.tree.error
async def on_app_command_error(interaction, error):
	shallAutoReport = True

	if isinstance(error.original, sqlite3.OperationalError):
		await interaction.followup.send(
			"`❌`: Encountered an error while saving data. Please retry later.",
			ephemeral=True
		)
		logger.warning("Failed: %s", error.original)

	else:
		await interaction.followup.send(
			"`❌`: The bot encountered an unknown error. Please retry later.",
			ephemeral=True
		)
		logger.exception(error.original)




	if shallAutoReport is True:
		exc = getattr(error, 'original', error)
		trace = ''.join(traceback.format_exception(exc.__class__, exc, exc.__traceback__))

		adminsMentions = ' '.join(['<@'+str(uid)+'>' for uid in config.dev_report_id])


		message = \
			f"error-report! Error occured in **{interaction.guild}**\n```cmd\n{trace}\n```\n\n({adminsMentions})"

		# Purposely using interaction.guild and not interaction.guild.name
		# in order to not throw an error if it was not in a guild context


		async with aiohttp.ClientSession() as s:
			async with s.post(
				config.report_error_webhook,
				json={
					"username": "AER - Stats",
					"avatar_url": "https://cdn.discordapp.com/attachments/805956034576252958/1005952580037386260/unknown.png",
					"content": message
				}
			):
				pass


@bot.command()
async def raisesmth(ctx):
	ok



@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.message.add_reaction('❔')

	elif isinstance(error, commands.MissingPermissions):
		await ctx.reply(
			"`❌`: I am missing some permissions to execute this action..",
			ephemeral=True
		)

	elif isinstance(error, commands.NotOwner):
		await ctx.reply(
			"`❌`: You must be the bot owner to execute this action..",
			ephemeral=True
		)

	elif isinstance(error, commands.CheckFailure):
		await ctx.reply(
			"`❌`: Looks like you don't pass the conditions to execute this action..",
			ephemeral=True
		)



	else:
		logger.exception(error)

