import telebot
import requests
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

bot = telebot.TeleBot('7453464704:AAHMk2G38eV72rBZL_8dXc3LWRhxAOn2GfI')

# Твой API-ключ от TMDb
API_KEY = 'fa1c200dad02012b2c0c58a74376288e'

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        language_code TEXT,
        first_interaction TEXT,
        last_interaction TEXT
    )
''')
conn.commit()
conn.close()

# Маппинг настроения на жанры TMDb
MOOD_TO_GENRE = {
    "Веселое 😊": 35,       # Комедия
    "Грустное 😢": 18,      # Драма
    "Напряженное 😱": 53,   # Триллер
    "Романтичное ❤️": 10749, # Романтика
    "Приключенческое 🌍": 12 # Приключения
}
def save_user(user):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    language_code = user.language_code
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Проверяем, существует ли уже такой пользователь в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Обновляем время последнего взаимодействия
        cursor.execute("UPDATE users SET last_interaction = ? WHERE user_id = ?", (current_time, user_id))
    else:
        # Добавляем нового пользователя
        cursor.execute("INSERT INTO users (user_id, username, first_name, last_name, language_code, first_interaction, last_interaction) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (user_id, username, first_name, last_name, language_code, current_time, current_time))

    conn.commit()
    conn.close()

# Хранилище состояний пользователей
user_states = {}

# Функция для получения фильмов по жанру на русском языке
def get_movies_by_genre(genre_id):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=ru-RU&sort_by=popularity.desc&with_genres={genre_id}'
    response = requests.get(url)
    data = response.json()
    
    if 'results' in data:
        movies = []
        for movie in data['results'][:10]:  # Берем только первые 10 фильмов
            title = movie.get('title')
            if not title:  # Если название на русском отсутствует, берем оригинальное название
                title = get_original_title(movie['id'])
            movie['title'] = title
            movies.append(movie)
        return movies
    return []

# Функция для получения оригинального названия фильма, если русского нет
def get_original_title(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    response = requests.get(url)
    data = response.json()
    return data.get('title', 'Название недоступно')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Сохраняем пользователя в базе данных
    save_user(message.from_user)
    # Новое приветственное сообщение
    text = (
        "🎬 *Добро пожаловать в КиноБот!*\n\n"
        "Я здесь, чтобы помочь вам найти идеальный фильм для любого настроения! Хотите расслабиться с комедией, погрузиться в романтику или испытать острые ощущения от триллера? Я подберу для вас лучшие рекомендации! 💥\n\n"
        "📌 *Как это работает?*\n"
        "1️⃣ *Выберите своё настроение* — просто скажите мне, что вам хочется, и я предложу фильмы, которые вам подойдут.\n\n"
        "2️⃣ *Смотрите трейлеры и читайте описания* — каждый фильм сопровождается рейтингом и кратким описанием, чтобы вам было легче выбрать.\n\n"
        "3️⃣ *Наслаждайтесь просмотром!* 🍿 — найдите идеальный фильм для уютного вечера или захватывающего киносеанса.\n\n"
        "Нажмите /mood, чтобы выбрать своё настроение и найти фильм, который подарит вам идеальные эмоции!"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def list_users(message):
    users = get_users()
    total_users = count_users()
    
    # Формируем список пользователей
    user_list = "\n".join([f"ID: {user[0]}, Username: {user[1]}, Name: {user[2]} {user[3]}, Language: {user[4]}" for user in users])
    
    response = f"Общее количество пользователей: {total_users}\n\nСписок пользователей:\n{user_list}" if user_list else "Пользователи не найдены."
    MAX_MESSAGE_LENGTH = 4096  # Максимальная длина сообщения Telegram
    if len(response) > MAX_MESSAGE_LENGTH:
        # Разбиваем на части
        chunks = [response[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(response), MAX_MESSAGE_LENGTH)]
        
        # Отправляем каждую часть по очереди
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk)
    else:
        # Отправляем всё сразу, если длина меньше ограничения
        bot.send_message(message.chat.id, response)
    

def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, username, first_name, last_name, language_code FROM users")
    users = cursor.fetchall()   
    
    conn.close()
    
    return users

# Функция для подсчета количества пользователей
def count_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    conn.close()

    return user_count

# Обработчик команды /mood
@bot.message_handler(commands=['mood'])
def choose_mood(message):
    markup = InlineKeyboardMarkup()
    for mood in MOOD_TO_GENRE.keys():
        button = InlineKeyboardButton(text=mood, callback_data=f"mood_{mood}")
        markup.add(button)
    bot.send_message(message.chat.id, "Выбери свое настроение:", reply_markup=markup)

# Обработчик нажатия кнопки настроения
@bot.callback_query_handler(func=lambda call: call.data.startswith("mood_"))
def mood_selected(call):
    mood = call.data.split("_")[1]
    genre_id = MOOD_TO_GENRE.get(mood)
    
    if genre_id:
        movies = get_movies_by_genre(genre_id)
        user_states[call.message.chat.id] = {
            'mood': mood,
            'movies': movies
        }
        
        if movies:
            show_movies_list(call.message.chat.id, mood, movies)
        else:
            bot.send_message(call.message.chat.id, f"Не удалось найти фильмы для настроения *{mood}*.", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "Извините, не могу обработать выбранное настроение.")

# Функция для отображения списка фильмов с кнопкой "Назад" к выбору настроения
def show_movies_list(chat_id, mood, movies):
    markup = InlineKeyboardMarkup()
    movie_list = ""
    for index, movie in enumerate(movies, start=1):
        title = movie['title']
        rating = movie['vote_average']
        movie_list += f"{index}. {title} (Рейтинг: {rating})\n"
        
        # Кнопка для каждого фильма
        button = InlineKeyboardButton(
            text=f"{index}. {title}",
            callback_data=f"movie_{movie['id']}"
        )
        markup.add(button)
    
    # Добавляем кнопку "Назад" к выбору настроения
    back_button = InlineKeyboardButton("⬅️ Назад ", callback_data="back_to_mood")
    markup.add(back_button)
    
    bot.send_message(chat_id, f"Фильмы для настроения *{mood}*:\n\n{movie_list}", parse_mode="Markdown", reply_markup=markup)

# Функция для получения трейлера фильма
def get_movie_trailer(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}&language=ru-RU'
    response = requests.get(url)
    data = response.json()

    if 'results' in data:
        for video in data['results']:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"
    return None

# Обработчик нажатия кнопки фильма
@bot.callback_query_handler(func=lambda call: call.data.startswith("movie_"))
def movie_details(call):
    movie_id = call.data.split("_")[1]
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=ru-RU'
    response = requests.get(url)
    movie = response.json()

    if movie:
        title = movie.get('title', get_original_title(movie_id))
        overview = movie.get('overview', 'Описание недоступно.')
        rating = movie.get('vote_average', 'N/A')
        release_date = movie.get('release_date', 'Неизвестно')
        
        # Получаем трейлер
        trailer_url = get_movie_trailer(movie_id)
        trailer_text = f"\n🎥 [Смотреть трейлер]({trailer_url})" if trailer_url else "\nТрейлер недоступен."
        
        # Формируем ответ с подробностями о фильме
        movie_info = (f"🎬 *{title}*\n\n"
                      f"📅 Дата выхода: {release_date}\n"
                      f"⭐ Рейтинг: {rating}\n\n"
                      f"📖 Описание: {overview}"
                      f"{trailer_text}")

        # Добавляем кнопку "Назад" к списку фильмов
        markup = InlineKeyboardMarkup()
        back_button = InlineKeyboardButton("⬅️ Назад ", callback_data="back_to_movies")
        markup.add(back_button)
        
        bot.send_message(call.message.chat.id, movie_info, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Информация о фильме не найдена.")

# Обработчик кнопки "Назад к списку фильмов"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_movies")
def back_to_movies(call):
    user_data = user_states.get(call.message.chat.id)
    
    if user_data:
        mood = user_data['mood']
        movies = user_data['movies']
        show_movies_list(call.message.chat.id, mood, movies)
    else:
        bot.send_message(call.message.chat.id, "Не удалось вернуться к списку фильмов.")

# Обработчик кнопки "Назад к выбору настроения"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_mood")
def back_to_mood(call):
    choose_mood(call.message)  # Возвращаемся к выбору настроения
bot.polling()
