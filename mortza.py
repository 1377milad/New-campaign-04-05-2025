from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import cv2
import numpy as np
from datetime import datetime
import os
import tempfile
import asyncio

# تنظیمات رنگ‌های هدف (HSV)
target_colors = [
    {'lower': np.array([0, 100, 100]), 'upper': np.array([10, 255, 255])},   # قرمز
    {'lower': np.array([40, 100, 100]), 'upper': np.array([70, 255, 255])},  # سبز
    {'lower': np.array([100, 100, 100]), 'upper': np.array([130, 255, 255])} # آبی
]

# رنگ‌های جایگزین (BGR)
new_colors = [
    (0, 255, 0),    # سبز
    (255, 0, 0),    # آبی
    (0, 0, 255)     # قرمز
]

def process_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    prev_contours = [None] * len(target_colors)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        for i, (target_color, new_color) in enumerate(zip(target_colors, new_colors)):
            mask = cv2.inRange(hsv, target_color['lower'], target_color['upper'])

            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) > 0:
                max_contour = max(contours, key=cv2.contourArea)

                x, y, w, h = cv2.boundingRect(max_contour)
                frame[y:y+h, x:x+w] = new_color
                prev_contours[i] = max_contour

        out.write(frame)

    cap.release()
    out.release()

# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! لطفاً ویدیوی خود را ارسال کنید تا رنگ‌ کاسه‌ها تغییر کند.')

# هندلر ویدیو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if not video:
        await update.message.reply_text("ویدیو معتبر پیدا نشد.")
        return

    await update.message.reply_text("در حال دریافت و پردازش ویدیو...")

    file = await context.bot.get_file(video.file_id)

    with tempfile.TemporaryDirectory() as tmpdirname:
        input_path = os.path.join(tmpdirname, "input.mp4")
        output_path = os.path.join(tmpdirname, "output.mp4")

        await file.download_to_drive(input_path)

        # پردازش ویدیو
        process_video(input_path, output_path)

        # ارسال ویدیو نهایی به کاربر
        with open(output_path, 'rb') as f:
            await update.message.reply_video(f, caption="✅ ویدیو پردازش شد.")

# تابع اصلی
def main():
    app = ApplicationBuilder().token("8183842877:AAF2Qw9T3XMleNcEHPO8GS_CVYR0pY1-C6E").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()




