from telegram.ext import CommandHandler, run_async
from telegram import Bot, Update
from bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, dispatcher, LOGGER
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.telegram_helper.message_utils import update_all_messages, sendMessage, sendStatusMessage
from .mirror import MirrorListener
from bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
import threading


def _watch(bot: Bot, update, isTar=False):
    mssg = update.message.text
    message_args = mssg.split(' ')
    name_args = mssg.split('|')
    try:
        link = message_args[1]
    except IndexError:
        msg = f"/{BotCommands.WatchCommand} [yt_dl supported link] [quality] |[CustomName] tải nhanh với youtube_dl.\n\n"
        msg += "<b>Note :- Chất lượng và tên tùy chỉnh là tùy chọn</b>\n\nVí dụ về chất lượng :- audio, 144, 240, 360, 480, 720, 1080, 2160."
        msg += "\n\nNếu bạn muốn sử dụng tên tệp tùy chỉnh, vui lòng nhập nó sau |"
        msg += f"\n\nVD :-\n<code>/{BotCommands.WatchCommand} https://youtu.be/UnyLfqpyi94 720 |My video</code>\n\n"
        msg += "Tệp này sẽ được tải xuống ở chất lượng 720p và tên của nó sẽ là <b>My video </b>"
        sendMessage(msg, bot, update)
        return
    try:
      if "|" in mssg:
        mssg = mssg.split("|")
        qual = mssg[0].split(" ")[2]
        if qual == "":
          raise IndexError
      else:
        qual = message_args[2]
      if qual != "audio":
        qual = f'bestvideo[height<={qual}]+bestaudio/best[height<={qual}]'
    except IndexError:
      qual = "bestvideo+bestaudio/best"
    try:
      name = name_args[1]
    except IndexError:
      name = ""
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        tag = reply_to.from_user.username
    else:
        tag = None
    pswd = ""
    listener = MirrorListener(bot, update, pswd, isTar, tag)
    ydl = YoutubeDLHelper(listener)
    threading.Thread(target=ydl.add_download,args=(link, f'{DOWNLOAD_DIR}{listener.uid}', qual, name)).start()
    sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


@run_async
def watchTar(update, context):
    _watch(context.bot, update, True)


def watch(update, context):
    _watch(context.bot, update)


mirror_handler = CommandHandler(BotCommands.WatchCommand, watch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
tar_mirror_handler = CommandHandler(BotCommands.TarWatchCommand, watchTar,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(tar_mirror_handler)
