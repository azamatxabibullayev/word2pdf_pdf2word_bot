import logging
import os
import tempfile
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

lang_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for code, name in LANGUAGES.items():
    lang_keyboard.add(KeyboardButton(name))

convert_keyboard = {
    "uz": ReplyKeyboardMarkup(resize_keyboard=True).add("Word ➡ PDF", "PDF ➡ Word"),
    "en": ReplyKeyboardMarkup(resize_keyboard=True).add("Word ➡ PDF", "PDF ➡ Word"),
    "ru": ReplyKeyboardMarkup(resize_keyboard=True).add("Word ➡ PDF", "PDF ➡ Word"),
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


@router.message(lambda message: message.document is not None)
async def handle_document(message: types.Message):
    user_id = message.from_user.id
    lang = user_states.get(user_id, {}).get("language", "en")
    conversion_type = user_states.get(user_id, {}).get("conversion")

    if not conversion_type:
        await message.answer(MESSAGES[lang]["choose_conversion"])
        return

    file_info = await bot.get_file(message.document.file_id)
    file_extension = message.document.file_name.split(".")[-1].lower()

    if conversion_type == "word_to_pdf" and file_extension != "docx":
        await message.answer(MESSAGES[lang]["error_file"])
        return
    if conversion_type == "pdf_to_word" and file_extension != "pdf":
        await message.answer(MESSAGES[lang]["error_file"])
        return

    await message.answer(MESSAGES[lang]["converting"])

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
        await bot.download_file(file_info.file_path, temp_file.name)
        temp_file_path = temp_file.name

    output_file_path = temp_file_path.replace(f".{file_extension}",
                                              ".pdf" if conversion_type == "word_to_pdf" else ".docx")

    try:
        if conversion_type == "word_to_pdf":
            convert_docx_to_pdf(temp_file_path, output_file_path)
        else:
            convert_pdf_to_docx(temp_file_path, output_file_path)

        with open(output_file_path, "rb") as doc:
            await message.answer_document(doc, caption=MESSAGES[lang]["success"])

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(MESSAGES[lang]["error"])

    finally:
        os.remove(temp_file_path)
        os.remove(output_file_path)


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
