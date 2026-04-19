import discord
import os
import re
from discord.ext import commands
from discord.ext import app_commands
from datetime import timedelta, datetime, timezone

# 1. Setup Intents
intents = discord.Intents.default()
intents.message_content = True

# 2. Initialize Bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
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


# ===== HÀM PARSE TIME =====
def parse_time(time_str):
    match = re.fullmatch(r'(\d+)(s|min|h|d|m|y)', time_str.strip())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'min':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'm':
        return timedelta(days=value * 30)
    elif unit == 'y':
        return timedelta(days=value * 365)
    return None

# ===== KICK =====
@bot.command()
async def kick(ctx, member: discord.Member = None):
    try:
        if member is None:
            raise commands.BadArgument()
        await member.kick()
        await ctx.send(f"✅ Đã kick {member.mention}")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!kick @user`")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== BAN =====
@bot.command()
async def ban(ctx, member: discord.Member = None):
    try:
        if member is None:
            raise commands.BadArgument()
        await member.ban()
        await ctx.send(f"✅ Đã ban {member.mention}")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!ban @user`")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

        # ===== UNBAN =====
@bot.command()
async def unban(ctx, user_id: int = None):
    try:
        if user_id is None:
            raise commands.BadArgument()
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Đã unban user ID `{user_id}`")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!unban <userID>`")
    except discord.NotFound:
        await ctx.send("❌ Không tìm thấy user hoặc user chưa bị ban.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== TIMEOUT =====
@bot.command()
async def timeout(ctx, member: discord.Member = None, time_str: str = None):
    try:
        if member is None or time_str is None:
            raise commands.BadArgument()
        delta = parse_time(time_str)
        if delta is None:
            raise commands.BadArgument()
        # Discord giới hạn tối đa 28 ngày
        if delta > timedelta(days=28):
            delta = timedelta(days=28)
        until = datetime.now(timezone.utc) + delta
        await member.timeout(until)
        await ctx.send(f"✅ Đã timeout {member.mention} trong {time_str}")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!timeout @user <time>` (ví dụ: `5s`, `5min`, `5h`, `5d`, `5m`, `5y`)")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

        # ===== UNTIMEOUT =====
@bot.command()
async def untimeout(ctx, member: discord.Member = None):
    try:
        if member is None:
            raise commands.BadArgument()
        await member.timeout(None)
        await ctx.send(f"✅ Đã gỡ timeout cho {member.mention}")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!untimeout @user`")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== HELP =====
COMMANDS = [
    ("!ping", None, "!ping", "Kiểm tra bot còn hoạt động không."),
    ("!say", None, "!say <text> <#channel|channelID>", "Gửi tin nhắn đến channel chỉ định."),
    ("!embedcreate", None, "!embedcreate #channel [Author] [Title] [Desc] [Img] [Thumb] [Footer] [FooterIcon] [Color]", "Tạo và gửi embed vào channel."),
    ("!kick", "/kick", "!kick @user", "Đuổi người dùng khỏi server."),
    ("!ban", "/ban", "!ban @user", "Cấm người dùng khỏi server."),
    ("!unban", "/unban", "!unban <userID>", "Gỡ cấm người dùng."),
    ("!timeout", "/timeout", "!timeout @user <time>", "Timeout người dùng (5s, 5min, 5h, 5d, 5m, 5y)."),
    ("!untimeout", "/untimeout", "!untimeout @user", "Gỡ timeout người dùng."),
]

@bot.command(name="help")
async def help_command(ctx):
    lines = [f"📋 **Tổng cộng: {len(COMMANDS)} lệnh**"]
    for cmd, slash, syntax, desc in COMMANDS:
        name = f"{cmd} ({slash})" if slash else cmd
        lines.append(f"`{name}` - `{syntax}` - {desc}")
    await ctx.send("\n".join(lines))

@bot.tree.command(name="help", description="Hiển thị danh sách lệnh")
async def slash_help(interaction: discord.Interaction):
    lines = [f"📋 **Tổng cộng: {len(COMMANDS)} lệnh**"]
    for cmd, slash, syntax, desc in COMMANDS:
        name = f"{cmd} ({slash})" if slash else cmd
        lines.append(f"`{name}` - `{syntax}` - {desc}")
    await interaction.response.send_message("\n".join(lines))

# ===== SLASH MODERATION =====
@bot.tree.command(name="kick", description="Đuổi người dùng khỏi server")
async def slash_kick(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.kick()
        await interaction.response.send_message(f"✅ Đã kick {member.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="ban", description="Cấm người dùng khỏi server")
async def slash_ban(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.ban()
        await interaction.response.send_message(f"✅ Đã ban {member.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="unban", description="Gỡ cấm người dùng")
async def slash_unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ Đã unban user ID `{user_id}`")
    except discord.NotFound:
        await interaction.response.send_message("❌ Không tìm thấy user hoặc user chưa bị ban.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="timeout", description="Timeout người dùng")
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, time: str):
    try:
        delta = parse_time(time)
        if delta is None:
            await interaction.response.send_message("❌ Thời gian không hợp lệ. Ví dụ: `5s`, `5min`, `5h`, `5d`, `5m`, `5y`")
            return
        if delta > timedelta(days=28):
            delta = timedelta(days=28)
        until = datetime.now(timezone.utc) + delta
        await member.timeout(until)
        await interaction.response.send_message(f"✅ Đã timeout {member.mention} trong {time}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="untimeout", description="Gỡ timeout người dùng")
async def slash_untimeout(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None)
        await interaction.response.send_message(f"✅ Đã gỡ timeout cho {member.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")


# 3. Run
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
