import asyncio
import os
import subprocess

import edge_tts
import yt_dlp
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel

from Vidlingua.exceptions import (
    AudioGenerationError,
    DownloadError,
    MergeError,
    TranslationError,
)

VOICE_MAPPING = {
    "en": "en-US-ChristopherNeural",
    "hi": "hi-IN-MadhurNeural",
    "ml": "ml-IN-MidhunNeural",
    "ta": "ta-IN-PallaviNeural",
    "kn": "kn-IN-GaganNeural",
    "te": "te-IN-MohanNeural",
}


def get_youtube_options(format_str, outtmpl):
    """Returns the yt-dlp configuration options."""
    opts = {
        "format": format_str,
        "outtmpl": outtmpl,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    return opts


def download_media(url, temp_dir):
    """
    Downloads both the audio (for transcription)
    and the video without audio (for dubbing).
    """

    audio_opts = get_youtube_options(
        "bestaudio/best", os.path.join(temp_dir, "original_audio.%(ext)s")
    )
    video_opts = get_youtube_options(
        "bestvideo/best", os.path.join(temp_dir, "original_video.%(ext)s")
    )

    try:
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info_dict)

        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)

        return audio_path, video_path
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(f"Failed to download media: {e}")


def speech_to_text(audio_path):
    model = WhisperModel("base", compute_type="int8", cpu_threads=8)

    segments, info = model.transcribe(audio_path, beam_size=1, vad_filter=True)

    text = "".join([segment.text for segment in segments])

    return text.strip()


def translate_text(text, target_lang):
    try:
        translator = GoogleTranslator(source="auto", target=target_lang)

        chunk_size = 4500
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        translated_text = ""
        for i, chunk in enumerate(chunks):
            translated_text += translator.translate(chunk) + " "

        return translated_text.strip()
    except Exception as e:
        raise TranslationError(f"Failed to translate text: {e}")


def text_to_audio(text, lang_code, output_path):
    try:
        voice = VOICE_MAPPING.get(lang_code.lower(), "en-US-ChristopherNeural")

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

        asyncio.run(_generate())

        return output_path
    except Exception as e:
        raise AudioGenerationError(f"Failed to generate audio: {e}")


def merge_audio_video(video_path, audio_path, output_path="final_dubbed_video.mp4"):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]
    try:
        subprocess.run(
            command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return output_path
    except subprocess.CalledProcessError as e:
        raise MergeError("Failed to merge audio and video. Ensure FFmpeg is installed.")
