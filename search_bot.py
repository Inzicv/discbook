```python
import os
import discord
from discord.ext import commands
from discord import app_commands

from book_search import search_books

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Avant le choix de langue
pending_searches = {}

# Après la recherche
last_results = {}

emoji_map = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4
}

language_map = {
    "🇫🇷": "french",
    "🇬🇧": "english"
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

    message = (
        "🌍 Choisis une langue :\n\n"
        "🇫🇷 Français\n"
        "🇬🇧 English"
    )

    await interaction.response.send_message(message)

    msg = await interaction.original_response()

    pending_searches[msg.id] = recherche

    await msg.add_reaction("🇫🇷")
    await msg.add_reaction("🇬🇧")


@bot.event
async def on_reaction_add(reaction, user):

    if user.bot:
        return

    message_id = reaction.message.id
    emoji = str(reaction.emoji)

    # Choix de la langue
    if message_id in pending_searches and emoji in language_map:

        query = pending_searches[message_id]
        language = language_map[emoji]

        books = search_books(query, language)

        if not books:
            await reaction.message.edit(
                content="❌ Aucun résultat trouvé."
            )
            del pending_searches[message_id]
            return

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        content = f'📚 Résultats pour "{query}"\n\n'

        for i, book in enumerate(books):

            content += (
                f'{emojis[i]} '
                f'{book["title"]} - {book["author"]}\n'
            )

        await reaction.message.clear_reactions()
        await reaction.message.edit(content=content)

        last_results[message_id] = books

        del pending_searches[message_id]

        for e in emojis[:len(books)]:
            await reaction.message.add_reaction(e)

        return

    # Sélection d'un livre
    if message_id not in last_results:
        return

    if emoji not in emoji_map:
        return

    index = emoji_map[emoji]

    books = last_results[message_id]

    if index >= len(books):
        return

    book = books[index]

    embed = discord.Embed(
        title=book["title"],
        description=book["description"][:4000],
        color=0x9B59B6
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
```
