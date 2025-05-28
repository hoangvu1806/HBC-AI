import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import asyncio
import signal

# Thay thế bằng token của bot bạn nhận từ BotFather
TOKEN = "7685926661:AAG4McyuuYvXxFUz80J3vwxdKwfGxafwrD0"

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Hàm gửi tin nhắn tự động
async def send_auto_message(context):
    chat_id = context.job.context  # Lấy chat_id từ context
    await context.bot.send_message(chat_id=chat_id, text="Đây là tin nhắn tự động từ bot!")

# Hàm xử lý lệnh /start
async def start(update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text("Chào mừng bạn! Bot đã được kích hoạt.")
    
    # Lên lịch gửi tin nhắn tự động (ví dụ: mỗi 60 giây)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_auto_message, 'interval', seconds=60, context=chat_id)
    scheduler.start()
    context.chat_data['scheduler'] = scheduler  # Lưu scheduler để dừng sau này

# Hàm xử lý tin nhắn từ người dùng
async def echo(update, context):
    await update.message.reply_text(f"Bạn vừa nói: {update.message.text}")

# Hàm xử lý lỗi
async def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')

async def run_bot():
    # Khởi tạo Application với token
    application = Application.builder().token(TOKEN).build()

    # Thêm các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error)

    # Khởi động bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    return application

async def stop_bot(application):
    # Dừng bot và scheduler
    for chat_id, scheduler in application.chat_data.items():
        if isinstance(scheduler, AsyncIOScheduler):
            scheduler.shutdown()
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

async def main():
    # Chạy bot
    application = await run_bot()

    # Giữ bot chạy cho đến khi nhận tín hiệu dừng
    try:
        while True:
            await asyncio.sleep(3600)  # Ngủ 1 giờ để giữ bot chạy
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal, stopping bot...")
        await stop_bot(application)

def handle_shutdown(loop, application):
    # Xử lý tín hiệu dừng
    tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    loop.run_until_complete(stop_bot(application))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

if __name__ == '__main__':
    # Lấy hoặc tạo event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Chạy bot
    application = loop.run_until_complete(run_bot())

    # Đăng ký xử lý tín hiệu dừng
    def signal_handler(sig, frame):
        logger.info("Received signal, shutting down...")
        handle_shutdown(loop, application)
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Giữ chương trình chạy
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        handle_shutdown(loop, application)