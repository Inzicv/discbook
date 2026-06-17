import os
import discord
from discord.ext import commands
from discord import app_commands

from book_search import search_books

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

last_results = {}

emoji_map = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4
}


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Connecté en tant que {bot.user}")


@bot.tree.command(
    name="book",
    description="Recherche un livre"
)
@app_commands.describe(
    recherche="Titre ou auteur"
)
async def book(interaction: discord.Interaction, recherche: str):

    await interaction.response.defer()

    books = search_books(recherche)

    if not books:
        await interaction.followup.send(
            "❌ Aucun résultat trouvé."
        )
        return

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    message = f'📚 Résultats pour "{recherche}"\n\n'

    for i, book in enumerate(books):

        flag = "🇫🇷"

        if "english" in book["language"].lower():
            flag = "🇬🇧"

        message += (
            f'{emojis[i]} {flag} '
            f'{book["title"]} - {book["author"]}\n'
        )

    msg = await interaction.followup.send(message)

    last_results[msg.id] = books

    for emoji in emojis[:len(books)]:
        await msg.add_reaction(emoji)


@bot.event
async def on_reaction_add(reaction, user):

    if user.bot:
        return

    if reaction.message.id not in last_results:
        return

    if str(reaction.emoji) not in emoji_map:
        return

    index = emoji_map[str(reaction.emoji)]

    books = last_results[reaction.message.id]

    if index >= len(books):
        return

    book = books[index]

    embed = discord.Embed(
        title=book["title"],
        description=book["description"][:4000],
        color=0x9b59b6
    )

    embed.add_field(
        name="✍ Auteur",
        value=book["author"],
        inline=False
    )

    embed.add_field(
        name="🌍 Langue",
        value=book["language"],
        inline=False
    )

    embed.add_field(
        name="📥 Télécharger",
        value=book["download"],
        inline=False
    )

    if book["cover"]:
        embed.set_image(url=book["cover"])

    await reaction.message.channel.send(embed=embed)


bot.run(TOKEN)
