import discord
import json
import os
from discord.ext import commands
from datetime import datetime, timezone

LOG_CHANNEL_NAME = "logs"
LOGS_FILE = "Logs.json"


# ==========================================
# HÀM XỬ LÝ LOGS.JSON
# ==========================================


def load_logs():
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"next_id": "00000000000000000000", "logs": {}}
    except:
        return {"next_id": "00000000000000000000", "logs": {}}


def save_logs(data):
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ==========================================
# COG CHÍNH
# ==========================================


class LogEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_event(
        self,
        guild: discord.Guild,
        embed: discord.Embed,
        log_type: str,
        description: str,
        extra: dict = None,
    ):
        """Gửi embed vào kênh Discord VÀ ghi vào Logs.json"""

        # 1. Lấy ID cho log này, tăng next_id lên 1
        data = load_logs()
        log_id = data["next_id"]
        next_val = int(log_id, 16) + 1
        data["next_id"] = format(next_val, "020X")

        # 2. Ghi vào Logs.json
        entry = {
            "type": log_type,
            "description": description,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        if extra:
            entry.update(extra)
        data["logs"][log_id] = entry
        save_logs(data)

        # 3. Thêm log ID vào footer embed
        existing_footer = embed.footer.text or ""
        embed.set_footer(
            text=f"Log ID: {log_id}"
            + (f" | {existing_footer}" if existing_footer else "")
        )

        # 4. Gửi lên kênh Discord
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if channel:
            await channel.send(embed=embed)

    # ==========================================
    # LỆNH !logs <log_id>
    # ==========================================

    @commands.command(name="logs")
    async def fetch_log(self, ctx, log_id: str = None):
        if log_id is None:
            return await ctx.send(
                "❌ Cú pháp: `!logs <log_id>`\nVí dụ: `!logs 00000000000000000000`"
            )

        # Chuẩn hoá: uppercase, pad về 20 ký tự
        log_id = log_id.strip().upper().zfill(20)

        # Kiểm tra đúng định dạng hex 20 ký tự
        try:
            int(log_id, 16)
            if len(log_id) != 20:
                raise ValueError
        except ValueError:
            return await ctx.send(
                "❌ Log ID không hợp lệ. Phải là chuỗi hex 20 ký tự.\nVí dụ: `00000000000000000000`"
            )

        data = load_logs()

        if log_id not in data["logs"]:
            return await ctx.send(f"❌ Không tìm thấy log với ID `{log_id}`")

        entry = data["logs"][log_id]
        embed = discord.Embed(
            title=f"📋 Log #{log_id}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Loại sự kiện", value=entry.get("type", "?"), inline=True)
        embed.add_field(
            name="Thời gian", value=entry.get("timestamp", "?"), inline=True
        )
        embed.add_field(name="Mô tả", value=entry.get("description", "?"), inline=False)

        # Các field phụ (user, channel, v.v.)
        skip = {"type", "description", "timestamp"}
        for key, val in entry.items():
            if key not in skip:
                embed.add_field(name=key.capitalize(), value=str(val), inline=True)

        await ctx.send(embed=embed)

    # ==========================================
    # EVENTS
    # ==========================================

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="📥 Thành viên mới tham gia",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Tên", value=str(member), inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(
            name="Tài khoản tạo",
            value=member.created_at.strftime("%d/%m/%Y"),
            inline=True,
        )
        await self.log_event(
            guild=member.guild,
            embed=embed,
            log_type="member_join",
            description=f"{member} tham gia server",
            extra={"user": str(member), "user_id": str(member.id)},
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="📤 Thành viên rời server",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Tên", value=str(member), inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        await self.log_event(
            guild=member.guild,
            embed=embed,
            log_type="member_leave",
            description=f"{member} rời server",
            extra={"user": str(member), "user_id": str(member.id)},
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            embed = discord.Embed(
                title="✏️ Đổi nickname",
                color=discord.Color.yellow(),
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(name="Thành viên", value=after.mention, inline=False)
            embed.add_field(name="Trước", value=before.nick or before.name, inline=True)
            embed.add_field(name="Sau", value=after.nick or after.name, inline=True)
            await self.log_event(
                guild=after.guild,
                embed=embed,
                log_type="nick_change",
                description=f"{after} đổi nickname",
                extra={
                    "before": before.nick or before.name,
                    "after": after.nick or after.name,
                },
            )

        if before.roles != after.roles:
            added = [r.name for r in after.roles if r not in before.roles]
            removed = [r.name for r in before.roles if r not in after.roles]
            if added or removed:
                embed = discord.Embed(
                    title="🎭 Thay đổi Role",
                    color=discord.Color.blurple(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed.add_field(name="Thành viên", value=after.mention, inline=False)
                if added:
                    embed.add_field(name="➕ Thêm", value=", ".join(added), inline=True)
                if removed:
                    embed.add_field(name="➖ Bỏ", value=", ".join(removed), inline=True)
                await self.log_event(
                    guild=after.guild,
                    embed=embed,
                    log_type="role_update",
                    description=f"{after} thay đổi role",
                    extra={"roles_added": added, "roles_removed": removed},
                )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        embed = discord.Embed(
            title="🗑️ Tin nhắn bị xóa",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tác giả", value=message.author.mention, inline=True)
        embed.add_field(name="Kênh", value=message.channel.mention, inline=True)
        embed.add_field(
            name="Nội dung", value=message.content or "*[không có text]*", inline=False
        )
        await self.log_event(
            guild=message.guild,
            embed=embed,
            log_type="message_delete",
            description=f"Tin nhắn của {message.author} bị xóa trong #{message.channel.name}",
            extra={
                "user": str(message.author),
                "channel": message.channel.name,
                "content": message.content,
            },
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        embed = discord.Embed(
            title="✏️ Tin nhắn bị sửa",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tác giả", value=before.author.mention, inline=True)
        embed.add_field(name="Kênh", value=before.channel.mention, inline=True)
        embed.add_field(name="Trước", value=before.content or "*trống*", inline=False)
        embed.add_field(name="Sau", value=after.content or "*trống*", inline=False)
        embed.add_field(
            name="🔗 Link", value=f"[Xem tin nhắn]({after.jump_url})", inline=False
        )
        await self.log_event(
            guild=before.guild,
            embed=embed,
            log_type="message_edit",
            description=f"Tin nhắn của {before.author} bị sửa trong #{before.channel.name}",
            extra={
                "user": str(before.author),
                "channel": before.channel.name,
                "before": before.content,
                "after": after.content,
            },
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Thành viên bị ban",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Người dùng", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        await self.log_event(
            guild=guild,
            embed=embed,
            log_type="member_ban",
            description=f"{user} bị ban khỏi server",
            extra={"user": str(user), "user_id": str(user.id)},
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="✅ Thành viên được unban",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Người dùng", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        await self.log_event(
            guild=guild,
            embed=embed,
            log_type="member_unban",
            description=f"{user} được unban",
            extra={"user": str(user), "user_id": str(user.id)},
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if after.channel and not before.channel:
            desc = f"➡️ Vào **{after.channel.name}**"
            color = discord.Color.green()
            extra = {"action": "join", "channel": after.channel.name}
        elif before.channel and not after.channel:
            desc = f"⬅️ Rời **{before.channel.name}**"
            color = discord.Color.red()
            extra = {"action": "leave", "channel": before.channel.name}
        else:
            desc = f"🔀 **{before.channel.name}** → **{after.channel.name}**"
            color = discord.Color.yellow()
            extra = {
                "action": "move",
                "from": before.channel.name,
                "to": after.channel.name,
            }
        embed = discord.Embed(
            title="🎙️ Voice",
            description=desc,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Thành viên", value=member.mention, inline=True)
        await self.log_event(
            guild=member.guild,
            embed=embed,
            log_type="voice_update",
            description=f"{member} {desc}",
            extra={"user": str(member), **extra},
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="📢 Kênh mới được tạo",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tên", value=channel.name, inline=True)
        embed.add_field(name="Loại", value=str(channel.type), inline=True)
        await self.log_event(
            guild=channel.guild,
            embed=embed,
            log_type="channel_create",
            description=f"Kênh #{channel.name} được tạo",
            extra={"channel": channel.name, "type": str(channel.type)},
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="🗑️ Kênh bị xóa",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tên", value=channel.name, inline=True)
        embed.add_field(name="Loại", value=str(channel.type), inline=True)
        await self.log_event(
            guild=channel.guild,
            embed=embed,
            log_type="channel_delete",
            description=f"Kênh #{channel.name} bị xóa",
            extra={"channel": channel.name, "type": str(channel.type)},
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(
            title="🎭 Role mới được tạo",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tên", value=role.name, inline=True)
        await self.log_event(
            guild=role.guild,
            embed=embed,
            log_type="role_create",
            description=f"Role @{role.name} được tạo",
            extra={"role": role.name},
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(
            title="🎭 Role bị xóa",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Tên", value=role.name, inline=True)
        await self.log_event(
            guild=role.guild,
            embed=embed,
            log_type="role_delete",
            description=f"Role @{role.name} bị xóa",
            extra={"role": role.name},
        )

    @commands.Cog.listener()
    async def on_command(self, ctx):
        embed = discord.Embed(
            title="🤖 Lệnh được dùng",
            color=discord.Color.dark_gray(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Người dùng", value=ctx.author.mention, inline=True)
        embed.add_field(name="Kênh", value=ctx.channel.mention, inline=True)
        embed.add_field(name="Lệnh", value=ctx.message.content, inline=False)
        await self.log_event(
            guild=ctx.guild,
            embed=embed,
            log_type="command_used",
            description=f"{ctx.author} dùng lệnh: {ctx.message.content}",
            extra={
                "user": str(ctx.author),
                "channel": ctx.channel.name,
                "command": ctx.message.content,
            },
        )


async def setup(bot):
    await bot.add_cog(LogEvents(bot))
