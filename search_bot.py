import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Connecté en tant que {bot.user}")

@bot.tree.command(name="book", description="Recherche un livre")
@app_commands.describe(recherche="Titre ou auteur")
async def book(interaction: discord.Interaction, recherche: str):
    await interaction.response.send_message(
        f"Recherche demandée : {recherche}"
    )

bot.run(TOKEN)
