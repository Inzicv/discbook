import os
import discord
from discord.ext import commands
from discord import app_commands

from book_search import search_books

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commande(s) synchronisée(s)")
    except Exception as e:
        print(e)

    print(f"Connecté en tant que {bot.user}")


@bot.tree.command(
    name="book",
    description="Recherche un livre sur Z-Library"
)
@app_commands.describe(
    recherche="Titre, auteur ou mots-clés"
)
async def book(interaction: discord.Interaction, recherche: str):

    # On prévient Discord qu'on travaille
    await interaction.response.defer()

    try:
        books = search_books(recherche)

        if not books:
            await interaction.followup.send(
                "❌ Aucun résultat trouvé."
            )
            return

        message = f'📚 Résultats pour "{recherche}"\n\n'

        for i, url in enumerate(books, start=1):
            message += f"{i}. {url}\n"

        await interaction.followup.send(message)

    except Exception as e:
        await interaction.followup.send(
            f"❌ Erreur : {e}"
        )
        print(e)


bot.run(TOKEN)
