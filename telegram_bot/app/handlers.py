"""
Обработчики команд и сообщений Telegram бота
"""
import json
import logging
import os
import tempfile
from io import BytesIO
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from .config import settings
from .services import PDFProcessorService

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "Сервис распознавания платежных счетов.\n\n"
        "Отправьте PDF-файл со сканом платежного счета. "
        "Сервис извлечет из него структурированные данные.\n\n"
        "Используйте /help для получения дополнительной информации."
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "Справка по использованию бота:\n\n"
        "1. Отправьте PDF-файл со сканом платежного счета\n"
        "2. Дождитесь обработки файла\n"
        "3. Получите структурированные данные в формате JSON\n\n"
        "Ограничения:\n"
        f"• Максимальный размер файла: {settings.MAX_FILE_SIZE / (1024 * 1024):.0f} МБ\n"
        "• Поддерживается только формат PDF\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку"
    )
    await message.answer(help_text)


@router.message(F.document)
async def handle_document(message: Message):
    """Обработчик загрузки документа"""
    document = message.document
    
    # Проверка типа файла
    if not document.file_name or not document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "Пожалуйста, отправьте файл в формате PDF."
        )
        return
    
    # Проверка размера файла
    if document.file_size and document.file_size > settings.MAX_FILE_SIZE:
        await message.answer(
            f"Файл слишком большой. Максимальный размер: "
            f"{settings.MAX_FILE_SIZE / (1024 * 1024):.0f} МБ"
        )
        return
    
    # Отправка сообщения о начале обработки
    processing_msg = await message.answer("Файл обрабатывается.")
    
    try:
        # Скачивание файла
        file = await message.bot.get_file(document.file_id)
        file_bytes = BytesIO()
        await message.bot.download_file(file.file_path, destination=file_bytes)
        file_bytes.seek(0)
        
        # Обработка через сервис
        processor = PDFProcessorService(settings.BACKEND_URL)
        result = await processor.process_pdf(
            file_bytes, 
            document.file_name
        )
        
        # Удаление сообщения о обработке
        await processing_msg.delete()
        
        # Отправка результата
        if result["success"]:
            await send_success_response(message, result["data"])
        else:
            await send_error_response(message, result["status_code"], result.get("message"))
            
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}", exc_info=True)
        await processing_msg.delete()
        await message.answer(
            "Произошла ошибка при обработке файла. Попробуйте позже."
        )


@router.message(F.photo)
async def handle_photo(message: Message):
    """Обработчик загрузки фото (не поддерживается)"""
    await message.answer(
        "Пожалуйста, отправьте PDF-файл, а не изображение. "
        "Для обработки изображений сначала конвертируйте их в PDF."
    )


async def send_success_response(message: Message, data: dict):
    """Отправка успешного ответа с форматированным JSON"""
    try:
        # Форматирование JSON для читаемости
        formatted_json = json.dumps(
            data, 
            ensure_ascii=False, 
            indent=2
        )
        
        # Если JSON слишком большой, отправляем как файл
        if len(formatted_json) > 4000:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(formatted_json)
                tmp_path = tmp_file.name
            
            try:
                await message.answer_document(
                    FSInputFile(tmp_path, filename="result.json"),
                    caption="Данные успешно извлечены из платежного счета"
                )
            finally:
                os.unlink(tmp_path)
        else:
            # Отправка как код для лучшей читаемости
            response_text = (
                "Данные успешно извлечены из платежного счета:\n\n"
                f"```json\n{formatted_json}\n```"
            )
            await message.answer(response_text, parse_mode="Markdown")
            
    except TelegramBadRequest as e:
        # Если сообщение слишком длинное, отправляем как файл
        logger.warning(f"Сообщение слишком длинное, отправляю как файл: {e}")
        formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(formatted_json)
            tmp_path = tmp_file.name
        
        try:
            await message.answer_document(
                FSInputFile(tmp_path, filename="result.json"),
                caption="Данные успешно извлечены из платежного счета"
            )
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}", exc_info=True)
        await message.answer("Обработка завершена, но произошла ошибка при отправке результата.")


async def send_error_response(message: Message, status_code: int, error_message: Optional[str] = None):
    """Отправка ответа об ошибке"""
    if status_code >= 500:
        # Ошибка сервера (5xx)
        response_text = settings.ERROR_5XX_PHRASE
    elif status_code >= 400:
        # Ошибка клиента (4xx)
        status_str = str(status_code)
        response_text = settings.ERROR_4XX_PHRASES.get(
            status_str, 
            f"Ошибка запроса (код {status_code}). {error_message or ''}"
        )
    else:
        response_text = "Произошла неизвестная ошибка."
    
    await message.answer(response_text)

