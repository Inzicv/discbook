import os
import discord
from discord.ext import commands
from discord import app_commands
from zlib import search_books

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

    books = search_books(recherche)

    if not books:
        await interaction.response.send_message(
            "Aucun résultat trouvé."
        )
        return

    message = f'📚 Résultats pour "{recherche}"\n\n'

    for i, url in enumerate(books, start=1):
        message += f"{i}. {url}\n"

    await interaction.response.send_message(message)


bot.run(TOKEN)
