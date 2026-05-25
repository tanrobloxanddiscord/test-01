import os
import discord
from discord.ext import commands
# 1. Import thư viện Google GenAI chính thức
from google import genai

# Cấu hình Intents cho Discord Bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Khởi tạo Gemini Client (Nên lưu API Key trong môi trường hệ thống/file .env)
# Nếu bạn đặt biến môi trường là GEMINI_API_KEY, hàm genai.Client() sẽ tự động nhận diện mà không cần truyền trực tiếp
gemini_client = genai.Client(api_key=os.getenv("Google_GenAI"))

@bot.event
async def on_ready():
    print(f"🤖 Bot Discord + Gemini đã sẵn sàng: {bot.user.name}")

@bot.event
async def on_message(message):
    # Tránh trường hợp bot tự trả lời chính nó
    if message.author.bot:
        return

    # Kiểm tra xem bot có bị tag (mention) hay không
    if bot.user.mentioned_in(message):
        
        # Bóc tách lấy prompt bằng cách xóa phần tag bot
        bot_mention = f"<@{bot.user.id}>"
        bot_mention_nick = f"<@!{bot.user.id}>"
        prompt = message.content.replace(bot_mention, "").replace(bot_mention_nick, "").strip()
        
        if not prompt:
            await message.channel.send(f"Chào {message.author.mention}! Hãy đặt câu hỏi cho tôi theo cú pháp: `@Bot [câu hỏi]`")
            return

        # Thông báo cho người dùng biết bot đang "suy nghĩ"
        await message.channel.send(f"⏳ *{message.author.name} đang hỏi Gemini:* \"{prompt}\"...\n*(Đang xử lý...)*")

        # 3. ĐẶT GOOGLE-GENAI API VÀO ĐÂY
        try:
            # Gọi API Gemini để tạo nội dung trả lời
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash', # Bạn có thể đổi thành gemini-2.5-pro nếu cần xử lý nặng
                contents=prompt,
            )
            
            # Lấy văn bản phản hồi từ kết quả API
            bot_response = response.text
            
            # Discord giới hạn 1 tin nhắn tối đa 2000 ký tự, cần kiểm tra để tránh crash bot
            if len(bot_response) > 2000:
                await message.channel.send(f"⚠️ Câu trả lời quá dài ({len(bot_response)} ký tự). Dưới đây là phần đầu:")
                await message.channel.send(bot_response[:1900] + "\n...(Còn tiếp)...")
            else:
                await message.channel.send(bot_response)
                
        except Exception as e:
            # Xử lý lỗi nếu API gặp sự cố (hết hạn key, nghẽn mạng...)
            print(f"❌ Lỗi API Gemini: {e}")
            await message.channel.send("😢 Xin lỗi, tôi gặp chút sự cố khi kết nối với não bộ Gemini rồi. Hãy thử lại sau nhé!")

    # Bắt buộc để chạy các lệnh command khác (nếu có)
    await bot.process_commands(message)

# Thay Token bot Discord của bạn vào đây
bot.run(os.getenv("DISCORD_TOKEN"))