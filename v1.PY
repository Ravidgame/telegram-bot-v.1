import os
import re
import telebot
import yt_dlp
import requests
import json
from datetime import datetime

# تنظیمات اصلی
TOKEN = "7010739576:AAHi23MSwsrrCw1Jvbdmu0NjXtiStQT-LAU"
DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE = 1500 * 1024 * 1024  # 1500 MB (1.5 GB)
CHANNEL_ID = "@samungofficial"  # یوزرنیم کانال شما

# ایجاد پوشه دانلود
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

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
        match = re.match(pattern, url)
        if match:
            return True
    return False

def clean_up_file(file_path):
    """حذف فایل"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"خطا در حذف فایل: {e}")

def is_user_in_channel(user_id):
    """بررسی عضویت کاربر در کانال"""
    try:
        status = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"خطا در بررسی عضویت کاربر: {e}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """پیام خوش‌آمدگویی"""
    user_id = message.from_user.id
    if not is_user_in_channel(user_id):
        bot.send_message(
            message.chat.id,
            f"لطفاً ابتدا به کانال ما بپیوندید: {CHANNEL_ID}\n\nبعد از عضویت، دوباره /start را ارسال کنید.",
            reply_markup=create_keyboard()
        )
        return

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
    user_id = message.from_user.id
    if not is_user_in_channel(user_id):
        bot.send_message(
            message.chat.id,
            f"لطفاً ابتدا به کانال ما بپیوندید: {CHANNEL_ID}\n\nبعد از عضویت، دوباره لینک را ارسال کنید.",
            reply_markup=create_keyboard()
        )
        return

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

        # تنظیمات yt-dlp برای دانلود یوتیوب
        ydl_opts = {
            'format': 'best[ext=mp4]',  # فقط فرمت mp4 با کیفیت بالا
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'youtube_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'no_color': True,
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # پیدا کردن فایل دانلود شده
            file_path = ydl.prepare_filename(info)

            # اگر سایز فایل بیش از حد مجاز باشد
            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                bot.edit_message_text(
                    "⚠️ حجم فایل بیشتر از حد مجاز است (1.5 گیگابایت)",
                    message.chat.id,
                    status_message.message_id
                )
                clean_up_file(file_path)
                return

            # ارسال ویدیو
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

        # حذف فایل بعد از ارسال
        clean_up_file(file_path)

    except Exception as e:
        bot.edit_message_text(
            f"❌ خطا در دانلود ویدیوی یوتیوب: {str(e)}",
            message.chat.id,
            status_message.message_id
        )
        print(f"خطای دقیق دانلود: {e}")

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
                        caption="🎥  @instagramddownload_botدانلود شده توسط ربات",
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

    except yt_dlp.utils.DownloadError:
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
    finally:
        if 'file_path' in locals():
            clean_up_file(file_path)

def main():
    """تابع اصلی"""
    print("🤖 ربات در حال اجراست...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"خطا در اجرای ربات: {e}")

if __name__ == "__main__":
    main()
