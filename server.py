from flask import Flask,request,jsonify,send_file,render_template,send_from_directory
import os
import time
import uuid
import json
import shutil
import random
import logging
import chardet
import psycopg2
import subprocess
from mpmath import mp
from io import BytesIO
from datetime import datetime
app = Flask(__name__)
BASE_DIRECTORY = 'F:/base_server'
import os
import random
import shutil
import logging
import psycopg2
import json
import chardet

log_paths = {
    "server": "F:/base_server/.logs/.server.log",
    "binary": "F:/base_server/.logs/.server_binary.log",
    "hex": "F:/base_server/.logs/.server_hex.log"
}

json_paths = {
    "server": "F:/base_server/.logs/.server.json"
}

DATABASE = {
    'dbname': 'photo_db',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'port': '58690'
}

current_format = {
    "binary": "inline",  # "inline" или "matrix"
    "hex": "inline"      # "inline" или "diagonal"
}

def colored_text(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'orange': '\033[93m',
        'yellow': '\033[93m',
        'reset': '\033[0m'
    }
    return f"{colors[color]}{text}{colors['reset']}"

def read_log(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return random.choice(lines).strip()

@app.get("/logs/{log_type}")
async def get_logs(log_type: str):
    if log_type in log_paths:
        log = read_log(log_paths[log_type])
        return {"log": log}
    else:
        return {"error": "Invalid log type"}, 400

def text_to_binary_matrix(text, format_type):
    binary_message = ''.join(format(ord(char), '08b') for char in text)
    if format_type == "matrix":
        lines = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    else:
        lines = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    return '\n'.join(lines)

def text_to_random_hex_matrix(text, format_type):
    hex_chars = '0123456789ABCDEF'
    hex_message = ''.join(random.choice(hex_chars) + random.choice(hex_chars) for _ in text)
    if format_type == "diagonal":
        lines = [hex_message[i:i+8] for i in range(0, len(hex_message), 8)]
    else:
        lines = [hex_message[i:i+2] + ' ' + hex_message[i+2:i+4] + ' ' + hex_message[i+4:i+6] + ' ' + hex_message[i+6:i+8] for i in range(0, len(hex_message), 8)]
    return '\n'.join(lines)

def log_message_matrix(message, format_type):
    if format_type == 'binary':
        formatted_message = text_to_binary_matrix(message, current_format["binary"])
    elif format_type == 'hex':
        formatted_message = text_to_random_hex_matrix(message, current_format["hex"])
    else:
        return
    log_file = log_paths[format_type]
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(formatted_message + '\n')

def reformat_log_file(file_path, format_type):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    
    with open(file_path, 'r', encoding=encoding) as f:
        content = f.readlines()
    
    formatted_content = []
    for line in content:
        formatted_message = ""
        if format_type == 'binary':
            formatted_message = text_to_binary_matrix(line.strip(), current_format["binary"])
        elif format_type == 'hex':
            formatted_message = text_to_random_hex_matrix(line.strip(), current_format["hex"])
        formatted_content.append(formatted_message)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(formatted_content) + '\n')

def change_log_format(new_format):
    global current_format
    current_format.update(new_format)
    for log_type, path in log_paths.items():
        reformat_log_file(path, log_type)
    for log_type, path in json_paths.items():
        reformat_log_file(path, log_type)

# Настройка логирования
log_dir = os.path.join('F:/base_server', '.logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'server.log')
json_log_file = os.path.join(log_dir, 'server.json')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
    ]
)

logger = logging.getLogger("server")

log_paths = {
    "server": log_file,
    "json": json_log_file,
    "binary": os.path.join(log_dir, 'server_binary.log'),
    "hex": os.path.join(log_dir, 'server_hex.log')
}

json_paths = {
    "server": json_log_file
}

BASE_DIRECTORY = 'F:/base_server'

def track_changes(action):
    logger.info(action)
    log_message_matrix(action, format_type='binary')
    log_message_matrix(action, format_type='hex')

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port']
    )
    track_changes("Подключение к базе данных PostgreSQL")
    return conn

def create_files_if_not_exist():
    if not os.path.exists(os.path.join('F:/base_server', '.logs')):
        os.makedirs(os.path.join('F:/base_server', '.logs'))
        track_changes("Создание директории .logs")
    for path in log_paths.values():
        if not os.path.exists(path):
            open(path, 'w', encoding='utf-8').close()
            track_changes(f"Создание файла лога: {path}")
    for path in json_paths.values():
        if not os.path.exists(path):
            open(path, 'w', encoding='utf-8').close()
            track_changes(f"Создание JSON-файла: {path}")

def restore_logs():
    log_files = []
    restored_files = []
    not_restored_files = []
    backup_log_path = log_paths["server"] + ".backup"
    backup_json_path = json_paths["server"] + ".backup"
    
    log_files.append(log_paths["server"])
    if not os.path.exists(log_paths["server"]):
        if os.path.exists(backup_log_path):
            shutil.copy(backup_log_path, log_paths["server"])
            logger.info(f"Данные логирования: Восстановлены | Удаленный файл логирования был восстановлен из резервной копии.")
            log_message_matrix(f"Данные логирования: Восстановлены | Удаленный файл логирования был восстановлен из резервной копии.", format_type='binary')
            log_message_matrix(f"Данные логирования: Восстановлены | Удаленный файл логирования был восстановлен из резервной копии.", format_type='hex')
            restored_files.append(log_paths["server"])
        else:
            open(log_paths["server"], 'w', encoding='utf-8').close()
            logger.info(f"Данные логирования: Файл создан, но потеря данных | Резервная копия файла логирования не найдена.")
            log_message_matrix(f"Данные логирования: Файл создан, но потеря данных | Резервная копия файла логирования не найдена.", format_type='binary')
            log_message_matrix(f"Данные логирования: Файл создан, но потеря данных | Резервная копия файла логирования не найдена.", format_type='hex')
            not_restored_files.append(log_paths["server"])
    
    log_files.append(json_paths["server"])
if not os.path.exists(json_paths["server"]):
    if os.path.exists(backup_json_path):
        shutil.copy(backup_json_path, json_paths["server"])
        logger.info(f"Данные логирования: Восстановлены | Удаленный JSON-файл был восстановлен из резервной копии.")
        log_message_matrix(f"Данные логирования: Восстановлены | Удаленный JSON-файл был восстановлен из резервной копии.", format_type='binary')
        log_message_matrix(f"Данные логирования: Восстановлены | Удаленный JSON-файл был восстановлен из резервной копии.", format_type='hex')
        restored_files.append(json_paths["server"])
    else:
        open(json_paths["server"], 'w', encoding='utf-8').close()
        logger.info(f"Данные логирования: Файл создан, но потеря данных | Резервная копия JSON-файла не найдена.")
        log_message_matrix(f"Данные логирования: Файл создан, но потеря данных | Резервная копия JSON-файла не найдена.", format_type='binary')
        log_message_matrix(f"Данные логирования: Файл создан, но потеря данных | Резервная копия JSON-файла не найдена.", format_type='hex')
        not_restored_files.append(json_paths["server"])

if not restored_files and not not_restored_files:
    logger.info(f"Данные логирования: Восстановление файлов логирования не требуется | Все файлы логов целы и не требуют восстановления.")
    log_message_matrix(f"Данные логирования: Восстановление файлов логирования не требуется | Все файлы логов целы и не требуют восстановления.", format_type='binary')
    log_message_matrix(f"Данные логирования: Восстановление файлов логирования не требуется | Все файлы логов целы и не требуют восстановления.", format_type='hex')
else:
    logger.info(f"Файлы логирования: {log_files}")
    logger.info(f"Восстановленные файлы: {restored_files}")
    logger.info(f"Не восстановленные файлы: {not_restored_files}")
    log_message_matrix(f"Файлы логирования: {log_files}", format_type='binary')
    log_message_matrix(f"Файлы логирования: {log_files}", format_type='hex')
    log_message_matrix(f"Восстановленные файлы: {restored_files}", format_type='binary')
    log_message_matrix(f"Восстановленные файлы: {restored_files}", format_type='hex')
    log_message_matrix(f"Не восстановленные файлы: {not_restored_files}", format_type='binary')
    log_message_matrix(f"Не восстановленные файлы: {not_restored_files}", format_type='hex')

def backup_logs():
    shutil.copy(log_paths["server"], log_paths["server"] + ".backup")
    shutil.copy(json_paths["server"], json_paths["server"] + ".backup")

def log_message(message):
    logger.info(message)
    log_message_matrix(message, format_type='binary')
    log_message_matrix(message, format_type='hex')
    backup_logs()

def write_to_json(data, json_path):
    with open(json_path, "w", encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    log_message_matrix(json.dumps(data, ensure_ascii=False, indent=4), format_type='binary')
    log_message_matrix(json.dumps(data, ensure_ascii=False, indent=4), format_type='hex')
    backup_logs()

# Пример вызова write_to_json для записи данных в формат JSON
sample_data = {
    "timestamp": "2025-02-09T12:34:56Z",
    "event": "Подключение к базе данных",
    "status": "success"
}

write_to_json(sample_data, json_paths["server"])

# Пример изменения стиля логирования
new_format = {
    "binary": "matrix",  # изменим стиль логирования на "matrix"
    "hex": "diagonal"    # изменим стиль логирования на "diagonal"
}

change_log_format(new_format)

# Платформа VPage
@app.route('/')
def home():
    log_message("Главная страница запущена")
    return send_from_directory(os.path.join(BASE_DIRECTORY, 'platforms', 'VPage'), '.home_platform.html')
@app.route('/upload_page')
def upload():
    log_message("Страница загрузки видео запущена")
    return send_from_directory(os.path.join(BASE_DIRECTORY, 'platforms', 'VPage'), '.upload_video.html')
@app.route('/host', methods=['POST'])
def host_app():
    app_name = request.form['app_name']
    app_path = os.path.join(BASE_DIRECTORY, app_name)
    if not os.path.exists(app_path):
        os.makedirs(app_path)
        log_message(f"Приложение {app_name} размещено.")
        return jsonify({"message": f"Приложение {app_name} размещено."})
    else:
        log_message(f"Приложение {app_name} уже существует.")
        return jsonify({"message": f"Приложение {app_name} уже существует."})
@app.route('/update', methods=['POST'])
def update():
    app_name = request.form['app_name']
    update_data = request.form['update_data']
    app_path = os.path.join(BASE_DIRECTORY, app_name)
    if os.path.exists(app_path):
        with open(os.path.join(app_path, 'update.txt'), 'w', encoding='utf-8') as f:
            f.write(update_data)
        log_message(f"Приложение {app_name} обновлено.")
        return jsonify({"message": f"Приложение {app_name} обновлено."})
    else:
        log_message(f"Приложение {app_name} не найдено.")
        return jsonify({"message": f"Приложение {app_name} не найдено."})
@app.route('/upload', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({"message": "Нет файла в запросе"}), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"message": "Не выбран файл для загрузки"}), 400
    filename = file.filename
    data = file.read()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO photos (filename, data) VALUES (%s, %s)", (filename, psycopg2.Binary(data)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Файл {filename} успешно загружен"}), 200
@app.route('/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT filename, data FROM photos WHERE id = %s", (photo_id,))
    photo = cur.fetchone()
    cur.close()
    conn.close()
    if photo is None:
        return jsonify({"message": "Фото не найдено"}), 404
    filename, data = photo
    return send_file(BytesIO(data), attachment_filename=filename)
@app.route('/images', methods=['GET'])
def get_all_photos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filename FROM photos")
    photos = cur.fetchall()
    cur.close()
    conn.close()
    photo_list = [{"id": photo[0], "filename": photo[1]} for photo in photos]
    return jsonify(photo_list)
# Хостинг изображений сервера
@app.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    image_dir = os.path.join(BASE_DIRECTORY, 'images')
    return send_from_directory(image_dir, filename)
# Отображение видео по названию файла (JSON)
@app.route('/videos/<filename>', methods=['GET'])
def serve_video(filename):
    upload_dir = os.path.join(BASE_DIRECTORY, 'platforms', 'VPage', 'uploads')
    video_file_path = os.path.join(upload_dir, filename + '.json')
    if os.path.exists(video_file_path):
        with open(video_file_path, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        return jsonify(video_data)
    else:
        return jsonify({"message": "Видео файл не найден"}), 404
# Хостинг страницы загрузки видео
@app.route('/upload_video', methods=['GET'])
def upload_video_page():
    log_message("Страница загрузки видео открыта")
    return send_from_directory(os.path.join(BASE_DIRECTORY, 'platforms', 'VPage'), '.upload_video.html')
# Загрузка видео на платформу
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"message": "Нет файла в запросе"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"message": "Не выбран файл для загрузки"}), 400
    filename = file.filename
    title = request.form['title']
    description = request.form['description']
    video_id = str(uuid.uuid4())
    video_data = {
        "id": video_id,
        "filename": filename,
        "title": title,
        "description": description
    }
    # Сохранение видео файла
    upload_dir = os.path.join(BASE_DIRECTORY, 'platforms', 'VPage', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file.save(os.path.join(upload_dir, filename))
    # Сохранение JSON файла с метаданными
    with open(os.path.join(upload_dir, video_id + '.json'), 'w', encoding='utf-8') as json_file:
        json.dump(video_data, json_file)
    log_message(f"Видео {title} успешно загружено")
    return jsonify({"message": f"Видео {title} успешно загружено", "id": video_id}), 200
@app.route('/matrix', methods=['GET'])
def upload_vi():
    log_message("Страница матрицы открыта")
    return send_from_directory(os.path.join(BASE_DIRECTORY, 'base_server'), 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=58690, debug=True)