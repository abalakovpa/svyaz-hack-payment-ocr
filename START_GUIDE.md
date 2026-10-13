# Пошаговая инструкция по запуску сервиса

## Способ 1: Запуск через Docker Compose (рекомендуется)

Это самый простой способ запустить все сервисы одной командой.

### Шаг 1: Подготовка окружения

```bash
# Убедитесь, что вы в корневой директории проекта
cd svyaz-hack-payment-ocr-1

# Создайте файл .env в корне проекта
# Скопируйте содержимое из .env.example или создайте вручную
```

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=ваш_токен_здесь

# Backend API URL (для локальной разработки)
BACKEND_URL=http://localhost:8000
```

### Шаг 2: Получение токена Telegram бота

1. Откройте Telegram
2. Найдите бота [@BotFather](https://t.me/BotFather)
3. Отправьте команду `/newbot`
4. Следуйте инструкциям:
   - Введите имя бота (например: "Payment OCR Bot")
   - Введите username бота (например: "payment_ocr_bot")
5. Скопируйте полученный токен (выглядит как: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Вставьте токен в файл `.env` вместо `ваш_токен_здесь`

### Шаг 3: Запуск сервисов

```bash
# Запустить все сервисы (с пересборкой образов)
docker-compose up --build

# ИЛИ запустить в фоновом режиме
docker-compose up -d --build
```

### Шаг 4: Проверка работы

Откройте в браузере:

- **API документация**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health
- **Метрики**: http://localhost:8000/api/v1/performance

### Шаг 5: Использование бота

1. Найдите вашего бота в Telegram (по username, который вы указали)
2. Отправьте команду `/start`
3. Отправьте PDF файл со сканом платежного счета
4. Получите структурированные данные в формате JSON

### Остановка сервисов

```bash
# Остановить все контейнеры
docker-compose down

# Остановить и удалить volumes
docker-compose down -v
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только telegram-bot
docker-compose logs -f telegram-bot
```

---

## Способ 2: Локальная разработка (без Docker)

Если вы хотите запустить сервисы локально для разработки.

### Backend API

```bash
# Перейти в директорию backend
cd backend

# Создать виртуальное окружение (рекомендуется)
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Установить Tesseract OCR:
# Windows: Скачайте установщик с https://github.com/UB-Mannheim/tesseract/wiki
# Установите и добавьте в PATH
# Linux:   sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
# macOS:   brew install tesseract tesseract-lang

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен по адресу: http://localhost:8000

### Telegram Bot

Откройте **новый терминал**:

```bash
# Перейти в директорию telegram_bot
cd telegram_bot

# Активировать виртуальное окружение (если используете)
# Windows:
..\backend\venv\Scripts\activate
# Linux/macOS:
source ../backend/venv/bin/activate

# Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# Создать .env файл
# Windows:
copy env.example .env
# Linux/macOS:
cp env.example .env

# Отредактировать .env и добавить токен бота
# TELEGRAM_BOT_TOKEN=ваш_токен_здесь
# BACKEND_URL=http://localhost:8000

# Запустить бота
python -m app.bot
```

---

## Проверка работы

### 1. Проверка Backend API

```bash
# Health check
curl http://localhost:8000/health

# Или откройте в браузере
# http://localhost:8000/health
```

Ожидаемый ответ:
```json
{"status": "healthy"}
```

### 2. Тестирование обработки PDF

```bash
# Через curl
curl -X POST "http://localhost:8000/api/v1/process-pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@путь/к/вашему/файлу.pdf"
```

Или через Python:

```python
import requests

url = "http://localhost:8000/api/v1/process-pdf"
files = {"file": open("путь/к/файлу.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### 3. Проверка метрик

```bash
curl http://localhost:8000/api/v1/performance
```

### 4. Проверка Telegram бота

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start` - должно прийти приветственное сообщение
4. Отправьте PDF файл - должен прийти ответ с данными

---

## Устранение проблем

### Проблема: Backend не запускается

**Решение:**

1. Проверьте, что порт 8000 свободен:
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/macOS
   lsof -i :8000
   ```

2. Если порт занят, измените порт в `docker-compose.yml` или используйте другой порт:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

3. Проверьте логи:
   ```bash
   docker-compose logs backend
   ```

### Проблема: Telegram бот не отвечает

**Решение:**

1. Проверьте токен в `.env` файле
2. Убедитесь, что backend запущен и доступен
3. Проверьте логи:
   ```bash
   docker-compose logs telegram-bot
   ```

4. Проверьте, что бот запущен (для локального запуска):
   ```bash
   # Должен быть запущен процесс python -m app.bot
   ```

### Проблема: OCR не работает

**Решение:**

1. Убедитесь, что Tesseract установлен:
   ```bash
   tesseract --version
   ```

2. Проверьте языковые пакеты:
   ```bash
   tesseract --list-langs
   # Должны быть: rus, eng
   ```

3. Для Docker: языковые пакеты устанавливаются автоматически в Dockerfile

### Проблема: Ошибка при обработке PDF

**Решение:**

1. Проверьте формат файла (должен быть PDF)
2. Проверьте размер файла (максимум 20 МБ)
3. Проверьте логи backend:
   ```bash
   docker-compose logs backend
   ```

---

## Быстрая проверка всех компонентов

```bash
# 1. Проверить статус контейнеров
docker-compose ps

# 2. Проверить health backend
curl http://localhost:8000/health

# 3. Проверить метрики
curl http://localhost:8000/api/v1/performance

# 4. Проверить логи
docker-compose logs --tail=50
```

---

## Полезные команды

```bash
# Перезапустить все сервисы
docker-compose restart

# Пересобрать и перезапустить
docker-compose up --build -d

# Остановить все
docker-compose stop

# Удалить все контейнеры и volumes
docker-compose down -v

# Просмотр использования ресурсов
docker stats

# Войти в контейнер backend
docker exec -it payment-ocr-backend bash

# Войти в контейнер telegram-bot
docker exec -it payment-ocr-telegram-bot bash
```

---

## Следующие шаги

После успешного запуска:

1. Протестируйте бота, отправив PDF файл
2. Проверьте API через документацию: http://localhost:8000/docs
3. Изучите метрики производительности
4. Попробуйте обучить модель через API или notebook
