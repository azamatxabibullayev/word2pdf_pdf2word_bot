import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from docx import Document
from pdf2docx import Converter
from fpdf import FPDF
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

user_states = {}

LANGUAGES = {
    "uz": "O'zbek",
    "en": "English",
    "ru": "Русский"
}

MESSAGES = {
    "uz": {
        "start": "Ushbu bot sizga Wordni PDFga va PDFni Wordga aylantirishda yordam beradi.\n\nIltimos, tilni tanlang:",
        "choose_conversion": "Qaysi operatsiyani amalga oshirmoqchisiz?",
        "send_file": "Iltimos, faylingizni yuboring.",
        "error_file": "Xato! Iltimos, DOCX yoki PDF fayl yuboring.",
        "converting": "Aylantirilmoqda...",
        "success": "Muvaffaqiyatli yakunlandi! Mana faylingiz:",
        "error": "Xatolik yuz berdi. Iltimos, qayta urinib ko’ring."
    },
    "en": {
        "start": "This bot can help you convert Word to PDF and PDF to Word.\n\nPlease select your language:",
        "choose_conversion": "Which conversion do you want?",
        "send_file": "Please send your file.",
        "error_file": "Error! Please send a DOCX or PDF file.",
        "converting": "Converting...",
        "success": "Conversion completed! Here is your file:",
        "error": "An error occurred. Please try again."
    },
    "ru": {
        "start": "Этот бот поможет вам конвертировать Word в PDF и PDF в Word.\n\nПожалуйста, выберите язык:",
        "choose_conversion": "Какое преобразование вы хотите выполнить?",
        "send_file": "Пожалуйста, отправьте ваш файл.",
        "error_file": "Ошибка! Пожалуйста, отправьте файл DOCX или PDF.",
        "converting": "Конвертация...",
        "success": "Конвертация завершена! Вот ваш файл:",
        "error": "Произошла ошибка. Попробуйте еще раз."
    }
}

lang_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=name)] for name in LANGUAGES.values()],
    resize_keyboard=True
)

convert_keyboard = {
    "uz": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Word ➡ PDF"), KeyboardButton(text="PDF ➡ Word")]],
        resize_keyboard=True
    ),
    "en": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Word ➡ PDF"), KeyboardButton(text="PDF ➡ Word")]],
        resize_keyboard=True
    ),
    "ru": ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Word ➡ PDF"), KeyboardButton(text="PDF ➡ Word")]],
        resize_keyboard=True
    ),
}


@router.message(Command("start"))
async def start(message: types.Message):
    user_states[message.from_user.id] = {}
    await message.answer(MESSAGES["en"]["start"], reply_markup=lang_keyboard)


@router.message()
async def set_language(message: types.Message):
    if message.text in LANGUAGES.values():
        lang_code = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(message.text)]
        user_states[message.from_user.id]["language"] = lang_code
        await message.answer(MESSAGES[lang_code]["choose_conversion"], reply_markup=convert_keyboard[lang_code])
    elif message.text in ["Word ➡ PDF", "PDF ➡ Word"]:
        await set_conversion_type(message)


async def set_conversion_type(message: types.Message):
    user_id = message.from_user.id
    lang = user_states.get(user_id, {}).get("language", "en")
    conversion_type = "word_to_pdf" if "Word ➡ PDF" in message.text else "pdf_to_word"

    user_states[user_id]["conversion"] = conversion_type
    await message.answer(MESSAGES[lang]["send_file"])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(BASE_DIR, "downloads")
os.makedirs(SAVE_PATH, exist_ok=True)


@router.message(lambda message: message.document is not None)
async def handle_document(message: types.Message):
    file_info = await bot.get_file(message.document.file_id)
    file_name = message.document.file_name

    file_path = os.path.join(SAVE_PATH, file_name)

    logging.info(f" Downloading file: {file_name}")
    logging.info(f"Telegram file path: {file_info.file_path}")
    logging.info(f"Saving to: {file_path}")

    try:
        await bot.download_file(file_info.file_path, file_path)
        logging.info(f"File saved successfully: {file_path}")
        await message.answer(f"File successfully saved at: {file_path}")
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        await message.answer(f"Error: {e}")


def convert_docx_to_pdf(input_file, output_path):
    doc = Document(input_file)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for para in doc.paragraphs:
        pdf.multi_cell(190, 10, para.text)

    pdf.output(output_path)


def convert_pdf_to_docx(input_file, output_path):
    converter = Converter(input_file)
    converter.convert(output_path, start=0, end=None)
    converter.close()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
