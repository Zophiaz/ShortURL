import asyncio
from aiogram import Bot, Dispatcher, types
import random
import string
import motor.motor_asyncio
import os


BOT_TOKEN = os.environ.get("BOT_TOKEN")


async def start_handler(event: types.Message):
    await event.answer(
        f"Hello, {event.from_user.get_mention(as_html=True)}!",
        parse_mode=types.ParseMode.HTML,
    )


async def a1_handler(event: types.Message):
    await event.answer(f"got a1")


async def regexp(event: types.Message):
    await event.answer(event.text)


async def add_url_handler(event: types.Message):
    long_url = event.text
    user_id = event.from_user.id
    client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://root:example'
                                                    f'@{os.environ.get("DB_HOST", "localhost")}:27017')
    db = client['redirecter']
    collection = db['redirects']
    generate_resource_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    await collection.insert_one({
        'long_url': long_url,
        'resource_id': generate_resource_id,
        'user_id': user_id})

    await event.answer(generate_resource_id)


async def get_url_handler(event: types.Message):
    client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://root:example'
                                                    f'@{os.environ.get("DB_HOST", "localhost")}:27017')
    db = client['redirecter']
    collection = db['redirects']
    document = await collection.find_one({'resource_id': event.text})
    if document is None:
        await event.answer("Not found")
    long_url = document['long_url']
    await event.answer(long_url)


async def get_user_urls_handler(event: types.Message):
    user_id = event.from_user.id
    client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://root:example'
                                                    f'@{os.environ.get("DB_HOST", "localhost")}:27017')
    db = client['redirecter']
    collection = db['redirects']
    documents = await collection.find({'user_id': user_id}).to_list(length=100)
    if documents:
        for document in documents:
            await event.answer(document['long_url'])
    else:
        await event.answer("Not found")


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(start_handler, commands={"start", "restart"})
        disp.register_message_handler(add_url_handler, regexp=r'http(s)?://.*')
        disp.register_message_handler(get_user_urls_handler, commands={"get"})
        disp.register_message_handler(get_url_handler, regexp=r'\w+')
        await disp.start_polling()
    finally:
        await bot.close()

asyncio.run(main())