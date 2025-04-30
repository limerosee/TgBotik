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
from collections import defaultdict
from googletrans import Translator
from aiogram.types import InputFile


# Вводим в переменную в другом файле личные токены из BotFather'а и google books api
from tokens_api import API_TOKEN, API_KEY

logging.basicConfig(level=logging.INFO)

# Вводим основные переменные, которые будем использовать в работе бота 
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
search_active = False
GENRE_LIMIT = 5  # Установим лимит на количество книг, отображаемых за раз
books_data = defaultdict(list)  # Словарь для хранения книг пользователя
genres = {
    "Художественная литература": "fiction",
    "Научная литература": "science",
    "Фэнтези": "fantasy",
    "Мистика": "mystery",
    "История": "history",
    "Поиск по всем жанрам": "all"
}
translator = Translator()

# Создаем клавиатуру с жанрами
genre_buttons = [KeyboardButton(genre) for genre in genres.keys()]
genres_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*genre_buttons)

# Определяем состояния для FSM
class SearchState(StatesGroup):
    waiting_for_query = State()
    waiting_for_genre = State()

# Создаем обработчик для команды "/start"
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    photo = InputFile('main.png')  # Укажем адресс нашего изображения
    await message.reply_photo(photo=photo, caption="Привет, я бот для поиска книг на английском, который поможет вам изучить английский язык на 200%!. \n<b>Для поиска книг введите</b> /search", parse_mode='HTML')

# Создаем обработчик для команды "/help"
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    photo = InputFile('main.png')  # Укажем адресс нашего изображения
    await message.reply_photo(photo=photo, caption="/start - Запустить бота\n/help - Показать вспомогательное сообщение\n/search - Искать книги\n/about - Показать информацию о проекте и разработчиках\n:3", parse_mode='HTML')

# Создаем обработчик для команды "/about"
@dp.message_handler(commands=['about'])
async def cmd_about(message: types.Message):
    photo = InputFile('main.png')  # Укажем адресс нашего изображения
    await message.reply_photo(photo=photo, caption="Этот проект является <b>полноценным телеграм-ботом</b>, который поможет вам <b>изучить английский с помощью приятного досуга в виде чтения книг</b>, позволяющий находить и читать книги с комфортом, с любого устройства, а главное - все это <b>совершенно бесплатно!</b>", parse_mode='HTML')

# Создаем обработчик для команды "/search"
@dp.message_handler(commands=['search'])
async def search_command(message: types.Message):
    global search_active
    search_active = True
    await SearchState.waiting_for_query.set()  # Устанавливаем состояние
    await message.answer("Введите название книги, которую хотите найти.")

# Проверяем тип чата
@dp.message_handler(lambda message: message.chat.type != 'private')
async def private_message_warning(message: types.Message):
    await message.answer("Пожалуйста, используйте личные сообщения для поиска книг.")

# Создаем функцию обработки запроса
@dp.message_handler(state=SearchState.waiting_for_query, content_types=types.ContentTypes.TEXT)
async def search_book(message: types.Message, state: FSMContext):
    global search_active
    if search_active:
        # Переводим текст запроса на английский
        query = message.text
        if any('\u0400' <= c <= '\u04FF' for c in query):  # Проверка на наличие кириллических символов
            translated = translator.translate(query, src='ru', dest='en')
            query = translated.text
            
        await state.update_data(search_query=query)  # Сохраняем очередь
        await SearchState.waiting_for_genre.set()  # Переходим к выбору жанра
        await message.answer("Выберите жанр книги:", reply_markup=genres_kb)

# Создаем функцию выбора жанра
@dp.message_handler(state=SearchState.waiting_for_genre)
async def select_genre(message: types.Message, state: FSMContext):
    if message.text in genres.keys():
        user_data = await state.get_data()  
        query = user_data.get('search_query')  
        genre = genres[message.text]
        
        if genre == "all":
            url = f'https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}'
        else:
            url = f'https://www.googleapis.com/books/v1/volumes?q={query}+subject:{genre}&key={API_KEY}'
        
        response = requests.get(url)
        data = response.json()
        
        if data.get('items'):
            books = data['items']
            books_data[message.from_user.id] = books  # Сохраняем книги в словаре
            await send_books(message.chat.id, books[:GENRE_LIMIT], 0)
        else:
            await message.answer("Книги не найдены. Попробуйте ввести другой запрос.")
        
        await state.finish()  
    else:
        await message.answer("Пожалуйста, выберите жанр из списка.", reply_markup=genres_kb)

# Создаем функцию отправки книг
async def send_books(chat_id, books, start_index):
    for book in books:
        title = book['volumeInfo'].get('title', 'Без названия')
        authors = ', '.join(book['volumeInfo'].get('authors', ['Неизвестный автор']))
        published_date = book['volumeInfo'].get('publishedDate', 'Дата публикации неизвестна')
        thumbnail = book['volumeInfo'].get('imageLinks', {}).get('thumbnail', None)
        link = book['volumeInfo'].get('previewLink', 'Нет ссылки')
        
        response_text = f"<b>Название:</b> {title}\n"
        response_text += f"<b>Авторы:</b> {authors}\n"
        response_text += f"<b>Дата публикации:</b> {published_date}\n"
        response_text += f'<a href="{link}">Читать в Google Books</a>\n'
        
        if thumbnail:
            await bot.send_photo(chat_id, photo=thumbnail, caption=response_text, parse_mode='HTML')
        else:
            await bot.send_message(chat_id, response_text, parse_mode='HTML')

    # Кнопка для получения следующих книг
    if start_index + GENRE_LIMIT < len(books_data[chat_id]):
        await bot.send_message(chat_id, "Нажмите ниже для загрузки следующих книг.",
                               reply_markup=types.InlineKeyboardMarkup().add(
                                   types.InlineKeyboardButton("Следующие книги", callback_data=f"next_books_{start_index + GENRE_LIMIT}")
                               ))
# Создаем функцию для работы с нашим списком книг
@dp.callback_query_handler(lambda c: c.data.startswith('next_books_'))
async def next_books(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    books = books_data.get(user_id, [])
    
    if not books:
        await bot.answer_callback_query(callback_query.id, text="Список книг пуст.")
        return

    # Извлекаем индекс из callback_data
    start_index = int(callback_query.data.split('_')[2])  

    # Проверяем, есть ли еще книги для показа
    if start_index < len(books):
        await send_books(callback_query.message.chat.id, books[start_index:start_index + GENRE_LIMIT], start_index)
        
        # Проверяем, есть ли еще книги после текущего показа
        if start_index + GENRE_LIMIT < len(books):
            await bot.send_message(callback_query.message.chat.id, "Нажмите ниже, чтобы загрузить следующие книги.",
                                   reply_markup=types.InlineKeyboardMarkup().add(
                                       types.InlineKeyboardButton("Следующие книги", callback_data=f"next_books_{start_index + GENRE_LIMIT}")
                                   ))
        else:
            await bot.send_message(callback_query.message.chat.id, "Вы просмотрели все доступные книги.",
                                   reply_markup=types.InlineKeyboardMarkup().add(
                                       types.InlineKeyboardButton("Начать заново", callback_data="restart")
                                   ))
    else:
        await bot.answer_callback_query(callback_query.id, text="Больше книг нет.")

@dp.callback_query_handler(lambda c: c.data == "restart")
async def restart_search(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Пожалуйста, введите новый запрос на поиск книг.")
    books_data.pop(callback_query.from_user.id, None)  # Удаляем данные о книгах предыдущего поиска

# Запускаем бесконечный цикл опроса нашего бота с диспетчером
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


