import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("Google_GenAI")

MAX_PROMPT_CHARS = 800
MAX_OUTPUT_TOKENS = 400


class ChatbotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.user.mentioned_in(message):
            bot_mention = f"<@{self.bot.user.id}>"
            bot_mention_nick = f"<@!{self.bot.user.id}>"
            prompt = (
                message.content
                .replace(bot_mention, "")
                .replace(bot_mention_nick, "")
                .strip()
            )

            if not prompt:
                await message.channel.send(
                    f"Chào {message.author.mention}! Hãy đặt câu hỏi: `@Bot [câu hỏi]`"
                )
                return

            if len(prompt) > MAX_PROMPT_CHARS:
                prompt = prompt[:MAX_PROMPT_CHARS]
                await message.channel.send(
                    f"⚠️ Câu hỏi quá dài, đã cắt xuống {MAX_PROMPT_CHARS} ký tự."
                )

            await message.channel.send(
                f"⏳ *Đang tìm kiếm và xử lý câu hỏi của {message.author.name}...*"
            )

            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "Trả lời ngắn gọn, súc tích. "
                            "Tối đa 3 đoạn văn. Không giải thích dài dòng."
                        ),
                        max_output_tokens=MAX_OUTPUT_TOKENS,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                )

                bot_response = response.text

                try:
                    chunks = response.candidates[0].grounding_metadata.grounding_chunks
                    if chunks:
                        sources = "\n\n**Nguồn tham khảo:**\n" + "\n".join(
                            f"- [{c.web.title}]({c.web.uri})"
                            for c in chunks if c.web
                        )
                        bot_response += sources
                except Exception:
                    pass

                if len(bot_response) > 1900:
                    await message.channel.send(
                        f"⚠️ Câu trả lời quá dài. Dưới đây là phần đầu:"
                    )
                    await message.channel.send(bot_response[:1900] + "\n...(Còn tiếp)...")
                else:
                    await message.channel.send(bot_response)

            except Exception as e:
                print(f"❌ Lỗi Gemini API: {e}")
                await message.channel.send(
                    "😢 Có lỗi khi kết nối Gemini. Thử lại sau nhé!"
                )


async def setup(bot):
    await bot.add_cog(ChatbotCog(bot))
