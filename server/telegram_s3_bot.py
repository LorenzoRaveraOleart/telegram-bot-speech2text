import json
import os
import logging
import boto3
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pydub import AudioSegment
from docx import Document

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# AWS Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
s3_client = boto3.client("s3")
transcribe_client = boto3.client("transcribe")

# Dictionary to track user folders
user_folders = {}


async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    await update.message.reply_text("Send me a folder name to save files in.")


async def set_folder(update: Update, context: CallbackContext) -> None:
    folder_name = update.message.text
    user_folders[update.message.chat_id] = folder_name
    logger.info(f"User {update.message.chat_id} set folder: {folder_name}")
    await update.message.reply_text(f"Folder set to: {folder_name}. Now send me images or audio!")


async def handle_photo(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in user_folders:
        logger.warning(
            f"User {chat_id} tried to send a photo without setting a folder")
        await update.message.reply_text("Please set a folder name first!")
        return

    folder_name = user_folders[chat_id]
    photo = update.message.photo[-1]  # Get the highest quality image
    file = await context.bot.get_file(photo.file_id)
    file_path = f"/tmp/{photo.file_id}.jpg"
    logger.info(f"Downloading image for user {chat_id} to {file_path}")
    await file.download_to_drive(file_path)

    photo_s3_key = f"{folder_name}/{photo.file_id}.jpg"
    try:
        s3_client.upload_file(file_path, S3_BUCKET, photo_s3_key)
        s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{photo_s3_key}"
        logger.info(f"Image uploaded successfully: {s3_url}")
        await update.message.reply_text(f"Image uploaded")
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        await update.message.reply_text("Failed to upload image.")


async def handle_audio(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in user_folders:
        logger.warning(
            f"User {chat_id} tried to send audio without setting a folder")
        await update.message.reply_text("Please set a folder name first!")
        return

    folder_name = user_folders[chat_id]
    audio = update.message.voice or update.message.audio
    file = await context.bot.get_file(audio.file_id)

    ogg_path = f"/tmp/{audio.file_id}.ogg"
    wav_path = f"/tmp/{audio.file_id}.wav"
    logger.info(f"Downloading audio for user {chat_id} to {ogg_path}")
    await file.download_to_drive(custom_path=ogg_path)

    logger.info(f"Converting {ogg_path} to WAV format")
    sound = AudioSegment.from_file(ogg_path, format="ogg")
    sound.export(wav_path, format="wav")

    audio_s3_key = f"{folder_name}/{audio.file_id}.wav"
    logger.info(f"Uploading audio file to S3: {audio_s3_key}")
    s3_client.upload_file(wav_path, S3_BUCKET, audio_s3_key)

    job_name = f"transcription-{audio.file_id}"
    audio_s3_uri = f"s3://{S3_BUCKET}/{audio_s3_key}"
    logger.info(f"Starting transcription job: {job_name}")
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": audio_s3_uri},
        MediaFormat="wav",
        LanguageCode="en-US",
        OutputBucketName=S3_BUCKET
    )

    # Polling for transcription result
    logger.info("Polling for transcription result...")
    while True:
        job = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name)
        if job["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
            break
        await asyncio.sleep(5)

    if job["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
        # Assuming the transcription JSON file is named using the job name
        transcript_key = f"{job_name}.json"
        transcript_file = f"/tmp/{transcript_key}"
        s3_client.download_file(S3_BUCKET, transcript_key, transcript_file)

        with open(transcript_file, 'r') as file:
            transcript_data = json.load(file)
            transcript_text = transcript_data["results"]["transcripts"][0]["transcript"]

        doc_path = f"/tmp/{job_name}.docx"
        logger.info(f"Saving transcript as Word document: {doc_path}")
        doc = Document()
        doc.add_paragraph(transcript_text)
        doc.save(doc_path)

        word_s3_key = f"{folder_name}/{job_name}.docx"
        logger.info(f"Uploading Word document to S3: {word_s3_key}")
        s3_client.upload_file(doc_path, S3_BUCKET, word_s3_key)

        await update.message.reply_text(f"Transcription complete! ")
    else:
        await update.message.reply_text("Transcription failed.")


def main():
    logger.info("Starting Telegram bot...")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, set_folder))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO, handle_audio))
    app.run_polling()


if __name__ == "__main__":
    main()
