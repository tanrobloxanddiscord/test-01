import discord
from discord.ext import commands
import re

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
            raise commands.BadArgument("Channel không hợp lệ.")

# ====== SAY COMMAND =====
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


# --- EMBEDCREATE COMMAND ---
@bot.command()
async def embedcreate(ctx, target_channel: discord.TextChannel = None, *, content: str = None):
    # 1. Kiểm tra nếu thiếu channel hoặc nội dung
    if target_channel is None or content is None:
        await ctx.send("❌ **Cú pháp sai!**\nVui lòng dùng: `!embedcreate #channel [Author] [Title] [Desc] [Img] [Thumb] [Footer] [FooterIcon] [Color]`")
        return

    try:
        # 2. Dùng Regex để tách 8 nội dung trong các cặp []
        params = re.findall(r'\[(.*?)\]', content)

        # 3. Kiểm tra số lượng tham số (phải đủ 8 cặp ngoặc vuông)
        if len(params) != 8:
            raise ValueError("Thiếu hoặc thừa tham số")

        # Gán biến từ mảng params
        author_v, title_v, desc_v, img_v, thumb_v, foot_v, foot_i_v, color_v = params

        # Hàm xử lý chuỗi trống
        def clean(val):
            val = val.strip()
            return None if val == "" else val

        # 4. Xử lý màu sắc
        hex_code = clean(color_v)
        final_color = 0x000000 
        if hex_code:
            try:
                final_color = int(hex_code.replace("#", ""), 16)
            except:
                pass

        # 5. Khởi tạo Embed
        embed = discord.Embed(
            title=clean(title_v),
            description=clean(desc_v),
            color=final_color
        )

        if clean(author_v):
            embed.set_author(name=author_v)
        
        if clean(thumb_v):
            embed.set_thumbnail(url=thumb_v)
            
        if clean(img_v):
            embed.set_image(url=img_v)

        if clean(foot_v):
            embed.set_footer(text=foot_v, icon_url=clean(foot_i_v))

        # 6. Gửi Embed vào CHANNEL ĐÃ CHỌN
        await target_channel.send(embed=embed)
        
        # Thông báo xác nhận tại kênh hiện tại
        await ctx.send(f"✅ Đã gửi Embed thành công vào kênh {target_channel.mention}")

    except Exception as e:
        # Báo lỗi nếu nhập sai định dạng
        await ctx.send(f"❌ **Lỗi:** Vui lòng nhập đúng 8 cặp ngoặc vuông `[]` sau tên kênh.\nVí dụ: `!embedcreate #general [Admin] [Chào] [Nội dung] [] [] [Footer] [] [#FFFFFF]`")


# 3. Run
bot.run('DISCORD_TOKEN')
