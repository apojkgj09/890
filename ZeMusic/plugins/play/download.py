import os
import re
import glob
import random
import config
import aiohttp
import aiofiles
import yt_dlp
from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch

from ZeMusic import app
from ZeMusic.utils.decorators import AdminActual
from ZeMusic.utils.database import is_search_enabled1, enable_search1, disable_search1

lnk = config.CHANNEL_LINK


def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
        

def cookies():
    folder_path = f"{os.getcwd()}/cookies"
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""


@app.on_message(filters.command(["/song", "بحث","يوت"],"") & filters.group)
async def song_downloader(client, message: Message):
    chat_id = message.chat.id 
    if not await is_search_enabled(chat_id):
        return await message.reply_text("<b>⇜ عـذراً عـزيـزي ...✖️\n⇜اليوتيوب معطل من قبل المشرفين 🙅🏻‍♀</b>")
        
    query = " ".join(message.command[1:])
    m = await message.reply_text("<b> جاري البحث ..</b>")
    
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await m.edit("**- لم يتم العثـور على نتائج حاول مجددا**")
            return

        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)  # تنظيف اسم الملف
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title_clean}.jpg"

        # تحميل الصورة المصغرة
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(thumb_name, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        duration = results[0]["duration"]

    except Exception as e:
        await m.edit("**- لم يتم العثـور على نتائج حاول مجددا**")
        print(str(e))
        return
    
    await m.edit("<b>جاري التحميل ♪</b>")
    
    ydl_opts = {
        "format": "bestaudio[ext=m4a]",  # تحديد صيغة M4A
        "keepvideo": False,
        "geo_bypass": True,
        "outtmpl": f"{title_clean}.%(ext)s",  # استخدام اسم نظيف للملف
        "quiet": True,
        "cookiefile": f"{cookies()}",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)  # التنزيل مباشرة
            audio_file = ydl.prepare_filename(info_dict)

        # حساب مدة الأغنية
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(float(dur_arr[i])) * secmul
            secmul *= 60

        # إرسال الصوت
        await message.reply_audio(
            audio=audio_file,
            caption=f"- @{app.username}",
            title=title,
            performer=info_dict.get("uploader", "Unknown"),
            thumb=thumb_name,
            duration=dur,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=config.CHANNEL_NAME, url=lnk),
                    ],
                ]
            ),
        )

        try:
            await app.send_audio(
                chat_id="@ASSUSB",  # معرف القناة التي تريد الإرسال إليها 
                audio=audio_file,
                caption=f"- @{app.username}",
                title=title,
                performer=info_dict.get("uploader", "Unknown"),
                thumb=thumb_name,
                duration=dur,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=config.CHANNEL_NAME, url=lnk),
                        ],
                    ]
                ),
            )
        except:
            pass
        await m.delete()

    except Exception as e:
        await m.edit(f"** حدث خطأ تواصل مع مطور البوت**")
        print(e)

    # حذف الملفات المؤقتة
    try:
        remove_if_exists(audio_file)
        remove_if_exists(thumb_name)
    except Exception as e:
        print(e)


@app.on_message(filters.command(["تعطيل اليوتيوب"],"") & filters.group)
@AdminActual
async def disable_search_command(client, message: Message, _):
    chat_id = message.chat.id
    if not await is_search_enabled(chat_id):
        await message.reply_text("<b>⇜ اليوتيوب .. معطـل مـن قبـل ✅</b>")
        return
    await disable_search(chat_id)
    await message.reply_text("<b>⇜ تم تعطيل  اليوتيوب .. بنجاح ✅</b>")


@app.on_message(filters.command(["تفعيل اليوتيوب"],"") & filters.group)
@AdminActual
async def enable_search_command(client, message: Message, _):
    chat_id = message.chat.id
    if await is_search_enabled(chat_id):
        await message.reply_text("<b>⇜ اليوتيوب .. مفعل مـن قبـل ✅</b>")
        return
    await enable_search(chat_id)
    await message.reply_text("<b>⇜ تم تفعيل اليوتيوب .. بنجاح ✅</b>")
