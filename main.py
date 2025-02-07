import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import google_books_api
import requests
import time
import os
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import CantParseEntities
from aiogram.types import InputMediaPhoto

API_TOKEN = '7936986251:AAG-lHYz8CRd5yRGYWskdqMZ5dmtO_Rqowk'
API_KEY = 'AIzaSyDdIv6Lsjmgo9y1d1_yj-YpWRT6CgNA5xU'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
search_active = False

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привеет, я бот для поиска книг на английском, который поможет вам изучить английский язык на 200%!. \nДля поиска книг введите /search")

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("/start - Запустить бота\n/help - Показать вспомогательное сообщение\n/search - Искать книги\n:3")

@dp.message_handler(commands=['about'])
async def cmd_about(message: types.Message):
    await message.reply("Я полноценный телеграм-бот, который поможет вам изучить английский с помощью приятного досуга в виде чтения книг, а главное - все это бесплатно!")

@dp.message_handler(commands=['search'])
async def search_command(message: types.Message):
    global search_active
    search_active = True
    await message.answer("Введите название книги, которую хотите найти.")
    

@dp.message_handler(lambda message: message.chat.type != 'private')
async def private_message_warning(message: types.Message):
    await message.answer("Пожалуйста, используйте личные сообщения для поиска книг.")

@dp.message_handler(lambda message: search_active and message.chat.type == 'private' and message.text!='/start' and message.text!='/help' and message.text!='/about')
async def search_book(message: types.Message):
    if search_active == False:
        exit()
    else:
            
        query = message.text
        url = f'https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}'
        
        response = requests.get(url)
        data = response.json()
        if (message == '/start') or (message == '/help') or (message == '/echo'):
            exit()
            
        else:
            if 'items' in data:
                books = data['items']
                responses = []
                
                for book in books[:5]:  # Ограничим результат до 5 книг
                    title = book['volumeInfo'].get('title')
                    authors = ', '.join(book['volumeInfo'].get('authors', ['Неизвестный автор']))
                    published_date = book['volumeInfo'].get('publishedDate', 'Дата публикации неизвестна')
                    thumbnail = book['volumeInfo'].get('imageLinks', {}).get('thumbnail', 'Нет изображения')
                    pdf_link = book['accessInfo'].get('pdf', {}).get('downloadLink', 'Нет PDF версии')
                    link = book['volumeInfo'].get('previewLink', 'Нет ссылки')
                    
                    response = f"**{title}**\n"
                    response += f"Авторы: {authors}\n"
                    response += f"Дата публикации: {published_date}\n"
                    response += f"[Читать в Google Books]({link})\n"
                    response += f"[Скачать PDF]({pdf_link})" if pdf_link != 'Нет PDF версии' else "PDF версия не доступна для скачивания."
                
                    responses.append((response, thumbnail))
                
                for resp, img in responses:
                    await message.answer(resp, parse_mode='Markdown', disable_web_page_preview=True)
                    if img != 'Нет изображения':
                        await message.answer_photo(img)
            else:
                await message.answer("Книги не найдены. Попробуйте ввести другой запрос.")




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

