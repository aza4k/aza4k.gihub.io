from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import hashlib
import hmac
from urllib.parse import parse_qs
from aiohttp import web

# O'zingizning bot tokeningizni BotFather'dan oling va shu yerga qo'ying
BOT_TOKEN = '7769026082:AAEv4dX2kdcz7oTtvOEY63vRN64rictToPI'

# Veb-ilovangiz joylashtirilgan HTTPS manzilni shu yerga qo'ying
# Muhim: Manzil HTTPS bo'lishi shart!
WEB_APP_URL = 'https://foydalanuvchi_nomi.github.io/repo_nomi/'  # O'zingizning hosting manzilingizni yozing

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

print("Bot ishga tushdi...")

def verify_telegram_web_app_signature(init_data):
    try:
        parsed_data = parse_qs(init_data)
        hash_value = parsed_data.get('hash', [None])[0]
        if not hash_value:
            return False

        data_check_string = "\n".join(f"{key}={value[0]}" for key, value in sorted(parsed_data.items()) if key != 'hash')

        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        return calculated_hash == hash_value
    except Exception as e:
        print(f"Imzoni tekshirishda xatolik: {e}")
        return False

async def handle_verify(request):
    data = await request.post()
    init_data = data.get('initData')
    if not init_data:
        return web.json_response({'error': 'initData is required'}, status=400)

    if verify_telegram_web_app_signature(init_data):
        return web.json_response({'status': 'ok'})
    else:
        return web.json_response({'status': 'error', 'message': 'Signature is invalid'}, status=401)

async def main_server():
    app = web.Application()
    app.add_routes([web.post('/verify_signature', handle_verify)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)  # Veb-ilovangizga moslang
    await site.start()
    print("Veb-server ishga tushdi...")
    # await asyncio.Future()  # Bu yerda kerak emas, chunki bot ham ishlaydi

@dp.message(commands=['start'])
async def send_welcome(message: types.Message):
    # Veb-ilovani ochish uchun tugma yaratish
    builder = InlineKeyboardBuilder()
    web_app_info = types.WebAppInfo(url=WEB_APP_URL)
    button = types.InlineKeyboardButton(
        text="O'yinni boshlash \U0001F439",
        web_app=web_app_info
    )
    builder.add(button)
    markup = builder.as_markup()

    # Foydalanuvchiga xush kelibsiz xabari va tugmani yuborish
    await message.answer(
        f"Salom, {message.from_user.first_name}! \U0001F44B\n\n"
        "Hamster Kombatga o'xshash o'yinimizga xush kelibsiz! \n"
        "O'yinni boshlash uchun quyidagi tugmani bosing:",
        reply_markup=markup
    )

async def main():
    # Ikkala asenkron vazifani bir vaqtda ishga tushirish
    await asyncio.gather(dp.start_polling(bot), main_server())

if __name__ == '__main__':
    asyncio.run(main())