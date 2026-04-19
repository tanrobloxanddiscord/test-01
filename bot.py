import discord
from discord.ext import commands

# 1. Setup Intents
intents = discord.Intents.default()
intents.message_content = True

# 2. Initialize Bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')


@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')


# ===== CONVERTER =====
class ChannelOrID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            pass

        try:
            return await ctx.bot.fetch_channel(int(argument))
        except:
            raise commands.BadArgument("Channel không hợp lệ 😐")

# ====== COMMAND =====
@bot.command()
async def say(ctx, *, args):
    try:
        # tách phần cuối là channel
        text, channel_input = args.rsplit(" ", 1)

        # convert channel
        channel = await ChannelOrID().convert(ctx, channel_input)

        await channel.send(text)

    except Exception as e:
        await ctx.send(f"Sai cú pháp: !say text channel_ID/#channel.")


# 3. Run
bot.run(os.getenv("TOKEN"))
