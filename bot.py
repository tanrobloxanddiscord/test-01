import discord
import os
import re
import json
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime, timezone

# ==========================================
# 1. CẤU HÌNH INTENTS & KHỞI TẠO BOT
# ==========================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Tên file lưu trữ trên Replit
DATA_FILE = "Warnings.json"

# ==========================================
# 2. CÁC HÀM HỖ TRỢ (JSON & TIME)
# ==========================================

def load_json():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_json(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def parse_time(time_str):
    match = re.fullmatch(r"(\d+)(s|min|h|d|m|y)", time_str.strip())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "min":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "m":
        return timedelta(days=value * 30)
    elif unit == "y":
        return timedelta(days=value * 365)
    return None

# ==========================================
# 3. SỰ KIỆN HỆ THỐNG
# ==========================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bạn không có quyền quản trị viên để dùng lệnh này!")

# ==========================================
# 4. CÁC LỆNH CƠ BẢN (PING, SAY, EMBED)
# ==========================================

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


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

# ===== SAY COMMAND =====
@bot.command()
async def say(ctx, *, args):
    try:
        text, channel_input = args.rsplit(" ", 1)
        channel = await ChannelOrID().convert(ctx, channel_input)
        await channel.send(text)
    except Exception as e:
        await ctx.send(f"Sai cú pháp: !say text channel_ID/#channel.")


# ===== EMBEDCREATE COMMAND =====
@bot.command()
async def embedcreate(
    ctx, target_channel: discord.TextChannel = None, *, content: str = None
):
    if target_channel is None or content is None:
        await ctx.send(
            "❌ **Cú pháp sai!**\nVui lòng dùng: `!embedcreate #channel [Author] [Title] [Desc] [Img] [Thumb] [Footer] [FooterIcon] [Color]`"
        )
        return
    try:
        params = re.findall(r"\[(.*?)\]", content)
        if len(params) != 8:
            raise ValueError("Thiếu hoặc thừa tham số")
        author_v, title_v, desc_v, img_v, thumb_v, foot_v, foot_i_v, color_v = params

        def clean(val):
            val = val.strip()
            return None if val == "" else val

        hex_code = clean(color_v)
        final_color = 0x000000
        if hex_code:
            try:
                final_color = int(hex_code.replace("#", ""), 16)
            except:
                pass

        embed = discord.Embed(
            title=clean(title_v), description=clean(desc_v), color=final_color
        )
        if clean(author_v):
            embed.set_author(name=author_v)
        if clean(thumb_v):
            embed.set_thumbnail(url=thumb_v)
        if clean(img_v):
            embed.set_image(url=img_v)
        if clean(foot_v):
            embed.set_footer(text=foot_v, icon_url=clean(foot_i_v))
        await target_channel.send(embed=embed)
        await ctx.send(f"✅ Đã gửi Embed thành công vào kênh {target_channel.mention}")
    except Exception as e:
        await ctx.send(
            f"❌ **Lỗi:** Vui lòng nhập đúng 8 cặp ngoặc vuông `[]`.\nVí dụ: `!embedcreate #general [Admin] [Chào] [Nội dung] [] [] [Footer] [] [#FFFFFF]`"
        )


# ==========================================
# 5. HỆ THỐNG CẢNH CÁO (WARN - LƯU JSON)
# ==========================================

# ===== WARN =====
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member = None, *, reason: str = "Không có lý do"):
    if member is None:
        return await ctx.send("❌ Cú pháp: `!warn @user <lý do>`")

    data = load_json()
    uid = str(member.id)
    if uid not in data:
        data[uid] = []

    data[uid].append(
        {"reason": reason, "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    )
    save_json(data)
    await ctx.send(
        f"⚠️ **Cảnh cáo:** {member.mention}\n**Lý do:** {reason}\n**Tổng số:** {len(data[uid])} lần."
    )


# ===== CHECK WARNS =====
@bot.command()
async def warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_json()
    user_warns = data.get(str(member.id), [])

    if not user_warns:
        return await ctx.send(f"✅ {member.mention} chưa có cảnh cáo nào.")

    embed = discord.Embed(
        title=f"Lịch sử cảnh cáo: {member.display_name}", color=discord.Color.orange()
    )
    for i, item in enumerate(user_warns, 1):
        embed.add_field(
            name=f"Lần {i}",
            value=f"Lý do: {item['reason']}\n*Ngày: {item['time']}*",
            inline=False,
        )
    await ctx.send(embed=embed)


# ===== CLEAR WARN =====
@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarn(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("❌ Cú pháp: `!clearwarn @user`")
    data = load_json()
    data[str(member.id)] = []
    save_json(data)
    await ctx.send(f"✅ Đã xóa toàn bộ lịch sử cảnh cáo của {member.mention}")


# ==========================================
# 6. QUẢN TRỊ SERVER (KICK, BAN, MUTE...)
# ==========================================

# ===== KICK =====
@bot.command()
@commands.has_permissions(administrator=True)
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
@commands.has_permissions(administrator=True)
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
@commands.has_permissions(administrator=True)
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
@commands.has_permissions(administrator=True)
async def timeout(ctx, member: discord.Member = None, time_str: str = None):
    try:
        if member is None or time_str is None:
            raise commands.BadArgument()
        delta = parse_time(time_str)
        if delta is None:
            raise commands.BadArgument()
        if delta > timedelta(days=28):
            delta = timedelta(days=28)
        until = datetime.now(timezone.utc) + delta
        await member.timeout(until)
        await ctx.send(f"✅ Đã timeout {member.mention} trong {time_str}")
    except commands.BadArgument:
        await ctx.send(
            "Sai cú pháp, cú pháp hiện tại: `!timeout @user <time>` (ví dụ: `5s`, `5min`, `5h`, `5d`, `5m`, `5y`)"
        )
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== UNTIMEOUT =====
@bot.command()
@commands.has_permissions(administrator=True)
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

# ===== CLEAR =====
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int = None):
    try:
        if amount is None:
            raise commands.BadArgument()
        if amount < 1 or amount > 100:
            await ctx.send("❌ Số lượng phải từ 1 đến 100.")
            return
        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(f"✅ Đã xóa {len(deleted)} tin nhắn.")
        await msg.delete(delay=3)
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!clear <số>`")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== SLOWMODE =====
@bot.command()
@commands.has_permissions(administrator=True)
async def slowmode(ctx, time_str: str = None):
    try:
        if time_str is None:
            raise commands.BadArgument()
        if time_str in ("0", "off"):
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.send("✅ Đã tắt slowmode.")
            return
        delta = parse_time(time_str)
        if delta is None:
            raise commands.BadArgument()
        seconds = min(int(delta.total_seconds()), 21600)
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"✅ Đã bật slowmode **{time_str}** cho channel này.")
    except commands.BadArgument:
        await ctx.send(
            "Sai cú pháp, cú pháp hiện tại: `!slowmode <time>` hoặc `!slowmode off`"
        )
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== LOCK =====
@bot.command()
@commands.has_permissions(administrator=True)
async def lock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel đã bị khóa.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== UNLOCK =====
@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel đã được mở.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")


# ==========================================
# 7. THÔNG TIN & TIỆN ÍCH
# ==========================================

# ===== USERINFO =====
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    try:
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed = discord.Embed(
            title=f"Thông tin: {member.display_name}", color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Tên", value=str(member), inline=True)
        embed.add_field(
            name="Tham gia server",
            value=member.joined_at.strftime("%d/%m/%Y"),
            inline=True,
        )
        embed.add_field(
            name="Tạo tài khoản",
            value=member.created_at.strftime("%d/%m/%Y"),
            inline=True,
        )
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=" ".join(roles) if roles else "Không có",
            inline=False,
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== SERVERINFO =====
@bot.command()
async def serverinfo(ctx):
    try:
        g = ctx.guild
        owner_mention = g.owner.mention if g.owner else f"ID: {g.owner_id}"

        embed = discord.Embed(
            title=f"🛡️ Thông tin Server: {g.name}", color=discord.Color.blue()
        )
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)

        embed.add_field(name="🆔 Server ID", value=f"`{g.id}`", inline=True)
        embed.add_field(name="👑 Chủ sở hữu", value=owner_mention, inline=True)
        embed.add_field(name="👥 Thành viên", value=f"`{g.member_count}`", inline=True)
        embed.add_field(name="💬 Kênh", value=f"`{len(g.channels)}`", inline=True)
        embed.add_field(name="🎭 Vai trò", value=f"`{len(g.roles)}`", inline=True)
        embed.add_field(
            name="📅 Ngày tạo",
            value=f"<t:{int(g.created_at.timestamp())}:D>",
            inline=True,
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi hệ thống: `{e}`")

# ===== AVATAR =====
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    try:
        member = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar của {member.display_name}", color=discord.Color.blurple()
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")

# ===== POLL =====
@bot.command()
async def poll(ctx, *, question: str = None):
    try:
        if question is None:
            raise commands.BadArgument()
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.gold())
        embed.set_footer(text=f"Tạo bởi {ctx.author.display_name}")
        await ctx.message.delete()
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
    except commands.BadArgument:
        await ctx.send("Sai cú pháp, cú pháp hiện tại: `!poll <câu hỏi>`")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {e}")


# ==========================================
# 8. LỆNH HELP (PHÂN NHÓM)
# ==========================================

COMMAND_LIST = [
    {
        "title": "CÁC LỆNH CƠ BẢN",
        "commands": [
            ("!ping", None, "!ping", "Kiểm tra bot còn hoạt động không."),
            ("!say", None, "!say <text> <#channel|channelID>", "Gửi tin nhắn đến channel chỉ định."),
            ("!embedcreate", None, "!embedcreate #channel [Author] [Title] [Desc] [Img] [Thumb] [Footer] [FooterIcon] [Color]", "Tạo và gửi embed vào channel."),
        ],
    },
    {
        "title": "HỆ THỐNG CẢNH CÁO (ADMIN ONLY)",
        "commands": [
            ("!warn", None, "!warn @user <lý do>", "Cảnh cáo người dùng."),
            ("!warns", None, "!warns @user", "Xem danh sách cảnh cáo của user."),
            ("!clearwarn", None, "!clearwarn @user", "Xóa toàn bộ cảnh cáo của user."),
        ],
    },
    {
        "title": "QUẢN TRỊ SERVER (ADMIN ONLY)",
        "commands": [
            ("!kick", "/kick", "!kick @user", "Đuổi người dùng khỏi server."),
            ("!ban", "/ban", "!ban @user", "Cấm người dùng khỏi server."),
            ("!unban", "/unban", "!unban <userID>", "Gỡ cấm người dùng."),
            ("!timeout", "/timeout", "!timeout @user <time>", "Timeout người dùng (5s, 5min, 5h, 5d, 5m, 5y)."),
            ("!untimeout", "/untimeout", "!untimeout @user", "Gỡ timeout người dùng."),
            ("!clear", None, "!clear <số>", "Xóa hàng loạt tin nhắn (tối đa 100)."),
            ("!slowmode", None, "!slowmode <time> hoặc off", "Bật/tắt slowmode cho channel."),
            ("!lock", None, "!lock", "Khóa channel, không cho user gửi tin."),
            ("!unlock", None, "!unlock", "Mở khóa channel."),
        ],
    },
    {
        "title": "THÔNG TIN & TIỆN ÍCH",
        "commands": [
            ("!userinfo", None, "!userinfo @user", "Xem thông tin của một user."),
            ("!serverinfo", None, "!serverinfo", "Xem thông tin server."),
            ("!avatar", None, "!avatar @user", "Lấy avatar của user."),
            ("!poll", None, "!poll <câu hỏi>", "Tạo poll vote ✅❌."),
        ],
    },
]

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📚 DANH SÁCH LỆNH CỦA BOT",
        description="Dưới đây là chi tiết các lệnh:",
        color=discord.Color.blue(),
    )
    for category in COMMAND_LIST:
        cmd_text = ""
        for cmd, slash, syntax, desc in category["commands"]:
            slash_text = f" | Slash: `{slash}`" if slash else ""
            cmd_text += f"**{syntax}**\n└ *{desc}*{slash_text}\n"
        embed.add_field(name=category["title"], value=cmd_text, inline=False)
    await ctx.send(embed=embed)


# ==========================================
# 9. CÁC LỆNH SLASH
# ==========================================

@bot.tree.command(name="help", description="Xem danh sách các lệnh của bot")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 DANH SÁCH LỆNH CỦA BOT",
        description="Dưới đây là chi tiết các lệnh:",
        color=discord.Color.green(),
    )
    for category in COMMAND_LIST:
        cmd_text = ""
        for cmd, slash, syntax, desc in category["commands"]:
            slash_text = f" | Slash: `{slash}`" if slash else ""
            cmd_text += f"**{syntax}**\n└ *{desc}*{slash_text}\n"
        embed.add_field(name=category["title"], value=cmd_text, inline=False)
    await interaction.response.send_message(embed=embed)

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
        await interaction.response.send_message(
            "❌ Không tìm thấy user hoặc user chưa bị ban."
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="timeout", description="Timeout người dùng")
async def slash_timeout(
    interaction: discord.Interaction, member: discord.Member, time: str
):
    try:
        delta = parse_time(time)
        if delta is None:
            await interaction.response.send_message(
                "❌ Thời gian không hợp lệ. Ví dụ: `5s`, `5min`, `5h`, `5d`, `5m`, `5y`"
            )
            return
        if delta > timedelta(days=28):
            delta = timedelta(days=28)
        until = datetime.now(timezone.utc) + delta
        await member.timeout(until)
        await interaction.response.send_message(
            f"✅ Đã timeout {member.mention} trong {time}"
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")

@bot.tree.command(name="untimeout", description="Gỡ timeout người dùng")
async def slash_untimeout(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None)
        await interaction.response.send_message(
            f"✅ Đã gỡ timeout cho {member.mention}"
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Lỗi: {e}")


# ==========================================
# 10. CHẠY BOT
# ==========================================

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")
bot.run(token)
