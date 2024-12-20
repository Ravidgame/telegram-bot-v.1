import os
import re
import telebot
import yt_dlp
import requests
import json
from datetime import datetime
import browser_cookie3  # نیاز به نصب: pip install browser-cookie3
import logging
import random

# تنظیمات اصلی
TOKEN = "7832063480:AAGk56oO-rQ0aftU4LFylQDvN5koWbdAf04"
DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE = 1500 * 1024 * 1024  # 1500 MB (1.5 GB)

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# لیست پراکسی‌ها (شما باید این رو با پراکسی‌های خودتون جایگزین کنید)
# PROXIES = [
#     'http://YOUR_PROXY_1:PORT',
#     'http://YOUR_PROXY_2:PORT',
#     'http://YOUR_PROXY_3:PORT',
# ]

PROXIES = []  # برای تست، لیست پراکسی را خالی کردیم

# ایجاد پوشه دانلود
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    logging.info(f"پوشه {DOWNLOAD_FOLDER} ایجاد شد.")

# راه‌اندازی ربات
bot = telebot.TeleBot(TOKEN)

def create_keyboard():
    """ایجاد کیبورد اینلاین برای منو"""
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("📥 راهنمای دانلود", callback_data="guide"),
        telebot.types.InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")
    )
    return keyboard

def is_instagram_url(url):
    """بررسی انواع لینک‌های اینستاگرام"""
    patterns = {
        'post': r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)',
        'story': r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/([a-zA-Z0-9_.-]+)\/([0-9]+)',
        'highlight': r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/highlights\/([0-9]+)'
    }

    for type_, pattern in patterns.items():
        if re.match(pattern, url):
            return True, type_
    return False, None

def is_youtube_url(url):
    """بررسی لینک‌های یوتیوب"""
    youtube_patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([\w-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([\w-]{11})'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False

def clean_up_file(file_path):
    """حذف فایل"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"فایل {file_path} حذف شد.")
    except Exception as e:
        logging.error(f"خطا در حذف فایل {file_path}: {e}")

def get_random_proxy():
    """انتخاب یک پراکسی به صورت رندوم"""
    if PROXIES:
        return random.choice(PROXIES)
    else:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """پیام خوش‌آمدگویی"""
    welcome_text = """
🌟 به ربات دانلود اینستاگرام و یوتیوب خوش آمدید!

این ربات می‌تواند:
• دانلود پست‌های ویدیویی اینستاگرام 🎥
• دانلود ریلز 🎬
• دانلود ویدیوهای یوتیوب 📺
• دانلود IGTV (بزودی) 📱
• دانلود استوری (بزودی) 📱

برای شروع، لینک مورد نظر خود را ارسال کنید.
    """
    bot.reply_to(message, welcome_text, reply_markup=create_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    """مدیریت دکمه‌های اینلاین"""
    if call.data == "guide":
        guide_text = """
📖 راهنمای دانلود:

1️⃣ وارد اینستاگرام یا یوتیوب شوید
2️⃣ پست مورد نظر را پیدا کنید
3️⃣ روی دکمه "..." کلیک کنید
4️⃣ گزینه "Copy Link" را بزنید
5️⃣ لینک را در ربات paste کنید
6️⃣ منتظر دانلود بمانید

⚠️ نکات مهم:
• حداکثر حجم فایل: 1.5GB
• حتماً از لینک معتبر استفاده کنید
• در صورت خطا، کمی صبر کرده و دوباره تلاش کنید
        """
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            guide_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_keyboard()
        )

    elif call.data == "about":
        about_text = """
ℹ️ درباره ربات:

🤖 نام: دانلودر اینستاگرام و یوتیوب
👨‍💻 نسخه: 3.0
📅 آخرین بروزرسانی: {}

قابلیت‌ها:
• دانلود ویدیو با بهترین کیفیت
• پشتیبانی از اینستاگرام و یوتیوب
• سرعت بالای دانلود
• رایگان و بدون تبلیغات

🔜 قابلیت‌های آینده:
• دانلود استوری
• دانلود هایلایت
• دانلود IGTV
        """.format(datetime.now().strftime("%Y/%m/%d"))

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            about_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_keyboard()
        )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """مدیریت پیام‌های ورودی و دانلود"""
    url = message.text.strip()
    is_valid_instagram, content_type = is_instagram_url(url)
    is_valid_youtube = is_youtube_url(url)

    if not (is_valid_instagram or is_valid_youtube):
        bot.reply_to(message, "❌ لطفاً یک لینک معتبر اینستاگرام یا یوتیوب ارسال کنید.")
        return

    status_message = bot.reply_to(message, "⏳ در حال پردازش درخواست...")

    try:
        if is_valid_instagram and content_type in ['post', 'reel']:
            download_media(message, url, status_message)
        elif is_valid_instagram and content_type == 'story':
             bot.edit_message_text(
                "⚠️ دانلود استوری فعلاً در دسترس نیست. بزودی اضافه خواهد شد.",
                message.chat.id,
                status_message.message_id
            )
        elif is_valid_instagram and content_type == 'highlight':
             bot.edit_message_text(
                "⚠️ دانلود هایلایت فعلاً در دسترس نیست. بزودی اضافه خواهد شد.",
                message.chat.id,
                status_message.message_id
            )
        elif is_valid_youtube:
            download_youtube_video(message, url, status_message)
    except Exception as e:
        bot.edit_message_text(
            f"❌ خطای غیرمنتظره: {str(e)}",
            message.chat.id,
            status_message.message_id
        )

def download_youtube_video(message, url, status_message):
    """دانلود و ارسال ویدیوی یوتیوب"""
    try:
        bot.edit_message_text(
            "⏳ در حال دانلود ویدیوی یوتیوب، لطفاً صبر کنید...",
            message.chat.id,
            status_message.message_id
        )
        
        proxy = get_random_proxy()
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # انعطاف‌پذیری بیشتر در انتخاب فرمت
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'youtube_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'no_color': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'retry_sleep': lambda n: 5 * (n + 1),
            'extractor_retries': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Keep-Alive': '115',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
            },
            'nocheckcertificate': True,
        }

        if proxy:
            ydl_opts['proxy'] = proxy
            logging.info(f"استفاده از پراکسی: {proxy}")
        else:
            logging.warning("لیست پراکسی خالی است، دانلود بدون پراکسی انجام می‌شود.")
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if info.get('age_limit', 0) > 0:
                   bot.edit_message_text(
                        "⚠️ این ویدیو دارای محدودیت سنی است و نیاز به ورود به حساب کاربری دارد.",
                       message.chat.id,
                       status_message.message_id
                   )
                   return
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    bot.edit_message_text(
                        "⚠️ حجم فایل بیشتر از حد مجاز است (1.5 گیگابایت)",
                        message.chat.id,
                        status_message.message_id
                    )
                    clean_up_file(file_path)
                    return
                
                with open(file_path, 'rb') as media_file:
                   bot.send_video(
                      message.chat.id,
                        media_file,
                        caption=f"🎥 {info.get('title', 'ویدیوی یوتیوب')}\n\n دانلود شده توسط ربات",
                        reply_to_message_id=message.message_id
                   )
                
                bot.edit_message_text(
                    "✅ فایل با موفقیت ارسال شد!",
                    message.chat.id,
                    status_message.message_id
                )
                
                clean_up_file(file_path)
            except yt_dlp.utils.ExtractorError:
                bot.edit_message_text(
                    "❌ خطا: امکان استخراج اطلاعات ویدیو وجود ندارد. لطفاً لینک را بررسی کنید.",
                    message.chat.id,
                    status_message.message_id
                )
            except yt_dlp.utils.DownloadError as e:
                error_message = str(e).lower()
                if "private video" in error_message:
                    bot.edit_message_text(
                        "❌ این ویدیو خصوصی است و قابل دانلود نیست.",
                        message.chat.id,
                        status_message.message_id
                    )
                elif "sign in" in error_message:
                    bot.edit_message_text(
                        "❌ این ویدیو نیاز به ورود به حساب کاربری دارد.",
                        message.chat.id,
                        status_message.message_id
                    )
                else:
                    bot.edit_message_text(
                        f"❌ خطا در دانلود ویدیو: {str(e)}",
                        message.chat.id,
                        status_message.message_id
                    )
    except Exception as e:
        bot.edit_message_text(
            f"❌ خطای غیرمنتظره: {str(e)}",
            message.chat.id,
            status_message.message_id
        )
        logging.error(f"خطای دقیق دانلود: {e}")

def download_media(message, url, status_message):
    """دانلود و ارسال مدیا"""
    try:
        bot.edit_message_text(
            "⏳ در حال دانلود، لطفاً صبر کنید...",
            message.chat.id,
            status_message.message_id
        )
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{info['id']}.{info['ext']}")
            
            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                bot.edit_message_text(
                    "⚠️ حجم فایل بیشتر از حد مجاز است (1.5 گیگابایت)",
                    message.chat.id,
                    status_message.message_id
                )
                clean_up_file(file_path)
                return
            
            with open(file_path, 'rb') as media_file:
                if info['ext'] in ['mp4', 'mov']:
                    bot.send_video(
                        message.chat.id,
                        media_file,
                        caption="🎥 @CAA_DownloaderBot دانلود شده توسط ربات",
                        reply_to_message_id=message.message_id
                    )
                else:
                    bot.send_document(
                        message.chat.id,
                        media_file,
                        caption="📎 دانلود شده توسط ربات",
                        reply_to_message_id=message.message_id
                    )
            
            bot.edit_message_text(
                "✅ فایل با موفقیت ارسال شد!",
                message.chat.id,
                status_message.message_id
            )
            
            clean_up_file(file_path)
    except yt_dlp.utils.DownloadError as e:
        error_message = str(e)
        if "Sign in to confirm you're not a bot" in error_message:
            bot.edit_message_text(
                "❌ خطا: نیاز به احراز هویت\n"
                "لطفاً مطمئن شوید که:\n"
                "1. لینک معتبر است\n"
                "2. پست خصوصی نیست",
                message.chat.id,
                status_message.message_id
            )
        else:
            bot.edit_message_text(
                "❌ خطا در دانلود. لطفاً لینک را بررسی کنید یا بعداً تلاش کنید.",
                message.chat.id,
                status_message.message_id
            )
    except Exception as e:
         bot.edit_message_text(
            f"❌ خطای غیرمنتظره: {str(e)}",
            message.chat.id,
            status_message.message_id
         )
         logging.error(f"خطای دقیق دانلود: {e}")
    finally:
        if 'file_path' in locals():
            clean_up_file(file_path)

def main():
    """تابع اصلی"""
    logging.info("ربات در حال اجراست...")
    
    # ایجاد پوشه دانلود اگر وجود نداشته باشد
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        logging.info(f"پوشه {DOWNLOAD_FOLDER} ایجاد شد.")
    
    try:
        logging.info("اتصال به تلگرام برقرار شد")
        logging.info("در حال گوش دادن به پیام‌ها...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logging.error(f"خطا در اجرای ربات: {e}")
    finally:
        logging.info("تلاش برای اتصال مجدد...")
        main()  # تلاش مجدد در صورت قطع شدن

if __name__ == "__main__":
    main()
