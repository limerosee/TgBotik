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
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import ParseMode


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
    await message.reply("Привет, я бот для поиска книг на английском, который поможет вам изучить английский язык на 200%!. \n<b>Для поиска книг введите</b> /search", parse_mode='HTML')

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("/start - Запустить бота\n/help - Показать вспомогательное сообщение\n/search - Искать книги\n/about - Показать информацию о проекте и разработчииках\n:3", parse_mode='HTML')

@dp.message_handler(commands=['about'])
async def cmd_about(message: types.Message):
    await message.reply("Этот проект является <b>полноценным телеграм-ботом</b>, который поможет вам <b>изучить английский с помощью приятного досуга в виде чтения книг</b>, позволяющий находить и читать книги с комфортом, с любого устройства, а главное - все это <b>совершенно бесплатно!</b>", parse_mode='HTML')

@dp.message_handler(commands=['search'])
async def search_command(message: types.Message):
    global search_active
    search_active = True
    await SearchState.waiting_for_query.set()  # Устанавливаем состояние
    await message.answer("Введите название книги, которую хотите найти.")

@dp.message_handler(lambda message: message.chat.type != 'private')
async def private_message_warning(message: types.Message):
    await message.answer("Пожалуйста, используйте личные сообщения для поиска книг.")

@dp.message_handler(state=SearchState.waiting_for_query, content_types=types.ContentTypes.TEXT)
async def search_book(message: types.Message, state: FSMContext):
    global search_active
    if search_active:
        query = message.text
        await state.update_data(search_query=query)  # Сохраняем запрос
        await SearchState.waiting_for_genre.set()  # Переходим к выбору жанра
        await message.answer("Выберите жанр книги:", reply_markup=genres_kb)

# @dp.message_handler(state=SearchState.waiting_for_genre)
# async def select_genre(message: types.Message, state: FSMContext):
#     if message.text in genres.keys():
#         user_data = await state.get_data()  # Получаем сохраненные данные
#         query = user_data.get('search_query')  # Извлекаем запрос
#         genre = genres[message.text]
        
#         if genre == "all":
#             url = f'https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}'
#         else:
#             url = f'https://www.googleapis.com/books/v1/volumes?q={query}+subject:{genre}&key={API_KEY}'

#         # Здесь вы можете добавить логику для получения и отправки результатов пользователю
#         await message.answer(f"Ищу книги по запросу: {query}, жанр: {message.text}")
        
#         # После завершения работы можно сбросить состояние
#         await state.finish()  
#         global search_active
#         search_active = False

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

                # Здесь вы можете добавить логику для получения и отправки результатов пользователю
        # await message.answer(f"Ищу книги по запросу:\n<b>Название:<b> {query}, \n<b>Жанр:<b> {message.text}", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await message.answer(

        f"Ищу книги по запросу:\n<b>Название:</b> {query}, \n<b>Жанр:</b> {message.text}",

        reply_markup=ReplyKeyboardRemove(),

        parse_mode="HTML"

        )



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
                
                linked = str(link)


                response_text = f"<b>Название:</b> {title}\n"

                response_text += f"<b>Авторы:</b> {authors}\n"

                response_text += f"<b>Дата публикации:</b> {published_date}\n"

                response_text += f'<a href="{link}">Читать в Google Books</a>\n'

                response_text += f'<a href="{pdf_link}">Скачать PDF</a>\n' if pdf_link != 'Нет PDF версии' else "PDF версия не доступна для скачивания."


                if thumbnail:
                    await message.answer_photo(photo=thumbnail, caption=response_text, parse_mode='HTML', 
                                               #disable_web_page_preview=True
                                               )
                else:
                    # await message.answer(response_text, parse_mode='Markdown', disable_web_page_preview=True)
                    await message.answer(response_text, parse_mode='HTML', disable_web_page_preview=True)
                    
        else:
            await message.answer("Книги не найдены. Попробуйте ввести другой запрос.")
        
        await state.finish()  # Завершаем состояние после обработки
    else:
        await message.answer("Пожалуйста, выберите жанр из списка.", reply_markup=genres_kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


