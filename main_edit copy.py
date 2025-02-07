import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram import executor
import google_books_api
import time
import os
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import CantParseEntities
from aiogram.types import InputMediaPhoto
from aiogram import executor
import requests
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
# from aiogram.dispatcher.filters.state import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, executor


API_TOKEN = '7936986251:AAG-lHYz8CRd5yRGYWskdqMZ5dmtO_Rqowk'
API_KEY = 'AIzaSyDdIv6Lsjmgo9y1d1_yj-YpWRT6CgNA5xU'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
search_active = False

genres = {
    "Художественная литература": "fiction",
    "Научная литература": "science",
    "Фэнтези": "fantasy",
    "Мистика": "mystery",
    "История": "history",
    "Поиск по всем жанрам": "all"
}


# Создаем клавиатуру с жанрами
genre_buttons = [KeyboardButton(genre) for genre in genres.keys()]
genres_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*genre_buttons)

# Определяем состояния для FSM
class SearchState(StatesGroup):
    waiting_for_query = State()
    waiting_for_genre = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привеет, я бот для поиска книг на английском, который поможет вам изучить английский язык на 200%!. \nДля поиска книг введите /search")

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("/start - Запустить бота\n/help - Показать вспомогательное сообщение\n/search - Искать книги\n:3")

@dp.message_handler(commands=['about'])
async def cmd_about(message: types.Message):
    await message.reply("Я - полноценный телеграм-бот, который поможет вам изучить английский с помощью приятного досуга в виде чтения книг, а главное - все это совершенно бесплатно!")

@dp.message_handler(commands=['search'])
async def search_command(message: types.Message):
    global search_active
    search_active = True
    await message.answer("Введите название книги, которую хотите найти.")
    

@dp.message_handler(lambda message: message.chat.type != 'private')
async def private_message_warning(message: types.Message):
    await message.answer("Пожалуйста, используйте личные сообщения для поиска книг.")

@dp.message_handler(lambda message: search_active and message.chat.type == 'private' and message.text not in ['/start', '/help', '/about'])
async def search_book(message: types.Message):
    if not search_active:
        return  # Не завершать работу, просто выйти из функции
    query = message.text
    await message.answer("Выберите жанр книги:", reply_markup=genres_kb)

@dp.message_handler(state=SearchState.waiting_for_genre)
async def select_genre(message: types.Message, state: FSMContext):
    if message.text in genres.keys():
        user_data = await state.get_data()  # Получаем сохраненные данные
        query = user_data.get('search_query')  # Извлекаем запрос
        genre = genres[message.text]
        
        if genre == "all":
            url = f'https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}'
        else:
            url = f'https://www.googleapis.com/books/v1/volumes?q={query}+subject:{genre}&key={API_KEY}'

        response = requests.get(url)
        data = response.json()
        
        if data.get('items'):
            books = data['items']
            
            for book in books[:5]:  # Ограничим результат до 5 книг
                title = book['volumeInfo'].get('title', 'Без названия')
                authors = ', '.join(book['volumeInfo'].get('authors', ['Неизвестный автор']))
                published_date = book['volumeInfo'].get('publishedDate', 'Дата публикации неизвестна')
                thumbnail = book['volumeInfo'].get('imageLinks', {}).get('thumbnail', None)
                pdf_link = book['accessInfo'].get('pdf', {}).get('downloadLink', 'Нет PDF версии')
                link = book['volumeInfo'].get('previewLink', 'Нет ссылки')
                
                response_text = f"**{title}**\n"
                response_text += f"Авторы: {authors}\n"
                response_text += f"Дата публикации: {published_date}\n"
                response_text += f"[Читать в Google Books]({link})\n"
                response_text += f"[Скачать PDF]({pdf_link})" if pdf_link != 'Нет PDF версии' else "PDF версия не доступна для скачивания."
                
                if thumbnail:
                    await message.answer_photo(photo=thumbnail, caption=response_text, parse_mode='Markdown', disable_web_page_preview=True)
                else:
                    await message.answer(response_text, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await message.answer("Книги не найдены. Попробуйте ввести другой запрос.")
        
        await state.finish()  # Завершаем состояние после обработки
    else:
        await message.answer("Пожалуйста, выберите жанр из списка.", reply_markup=genres_kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

