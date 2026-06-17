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

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

for i, book in enumerate(books):

    flag = "🇫🇷"

    if book["language"] == "English":
        flag = "🇬🇧"

    message += (
        f'{emojis[i]} '
        f'{flag} '
        f'{book["title"]} - {book["author"]}\n\n'
    )

message += (
    "\nRéagis avec 1️⃣ 2️⃣ 3️⃣ 4️⃣ ou 5️⃣ "
    "pour afficher la fiche complète."
)
        await interaction.followup.send(message)

    except Exception as e:
        await interaction.followup.send(
            f"❌ Erreur : {e}"
        )
        print(e)


bot.run(TOKEN)
