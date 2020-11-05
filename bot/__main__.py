import shutil, psutil
import signal
import pickle

from os import execl, path, remove
from sys import executable
import time

from telegram.ext import CommandHandler, run_async
from bot import dispatcher, updater, botStartTime
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, delete


@run_async
def stats(update, context):
    currentTime = get_readable_time((time.time() - botStartTime))
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>Thời gian bot chạy:</b> {currentTime}\n' \
            f'<b>Tổng dung lượng ổ đĩa:</b> {total}\n' \
            f'<b>Đã dùng:</b> {used}  ' \
            f'<b>Còn lại:</b> {free}\n\n' \
            f'📊Dữ liệu đã sử dụng📊\n<b>Tải lên:</b> {sent}\n' \
            f'<b>Tải xuống:</b> {recv}\n\n' \
            f'<b>CPU:</b> {cpuUsage}% ' \
            f'<b>RAM:</b> {memory}% ' \
            f'<b>Ổ đĩa:</b> {disk}%'
    sendMessage(stats, context.bot, update)


@run_async
def start(update, context):
    start_string = f'''
Đây là một máy chủ có thể tải tất cả các liên kết của bạn với Google drive!
Gõ /{BotCommands.HelpCommand} để có được danh sách các lệnh có sẵn
'''
    sendMessage(start_string, context.bot, update)


@run_async
def restart(update, context):
    restart_message = sendMessage("Đang khởi động lại, vui lòng chờ một chút", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    fs_utils.clean_all()
    with open('restart.pickle', 'wb') as status:
        pickle.dump(restart_message, status)
    execl(executable, executable, "-m", "bot")


@run_async
def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


@run_async
def log(update, context):
    sendLogFile(context.bot, update)


@run_async
def bot_help(update, context):
    help_string = f'''
/{BotCommands.HelpCommand}: Để nhận được tin nhắn này

/{BotCommands.MirrorCommand} [download_url][magnet_link]: Bắt đầu tải một link nhanh và tải lên google drive

/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link] : Bắt đầu tải một link nhanh, giải nén và tải lên google drive

/{BotCommands.TarMirrorCommand} [download_url][magnet_link]: Bắt đầu tải một link nhanh và tải lên phiên bản tải xuống đã lưu trữ (.tar)

/{BotCommands.WatchCommand} [youtube-dl supported link]: Tải nhanh thông qua youtube-dl. Click /{BotCommands.WatchCommand} để được biết thêm.

/{BotCommands.TarWatchCommand} [youtube-dl supported link]: Tải nhanh thông qua youtube-dl và nén bằng đuôi .tar sau đó file sẽ được tải lên

/{BotCommands.CancelMirror} : Lệnh này sử dụng kèm theo ID của phiên tải xuống và quá trình tải xuống đó sẽ bị hủy

/{BotCommands.StatusCommand}: Hiển thị trạng thái của tất cả các bản tải xuống

/{BotCommands.ListCommand} [search term]: Tìm kiếm cụm từ tìm kiếm trong google drive, nếu tìm thấy kết quả sẽ được trả về kèm theo liên kết

/{BotCommands.StatsCommand}: Hiển thị thống kê của máy chủ

/{BotCommands.AuthorizeCommand}: Cho phép mở quyền hoặc đóng quyền sử dụng máy chủ ngoài người sở hữu (Chỉ có Admin mới sử dụng được)

/{BotCommands.LogCommand}: Lấy logs của máy chủ

'''
    sendMessage(help_string, context.bot, update)


def main():
    fs_utils.start_cleanup()
    # Check if the bot is restarting
    if path.exists('restart.pickle'):
        with open('restart.pickle', 'rb') as status:
            restart_message = pickle.load(status)
        restart_message.edit_text("Khởi động lại máy chủ thành công!")
        remove('restart.pickle')

    start_handler = CommandHandler(BotCommands.StartCommand, start,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling()
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)


main()
