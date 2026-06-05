import sys
import subprocess
# Force UTF-8 encoding to support languages like Malayalam, Hindi, etc.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from faster_whisper import WhisperModel
import yt_dlp
import time
from deep_translator import GoogleTranslator
import asyncio
import edge_tts

# Map language codes to high-quality Microsoft Neural voices
VOICE_MAPPING = {
    "en": "en-US-ChristopherNeural",
    "hi": "hi-IN-MadhurNeural",
    "ml": "ml-IN-MidhunNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-KillianNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-MohanNeural",
    "mr": "mr-IN-ManoharNeural"
}

video_url = sys.argv[1]

import os

def get_youtube_options(format_str, outtmpl):
    """Returns the yt-dlp configuration options."""
    opts = {
        "format": format_str,
        "outtmpl": outtmpl,
        # Spoof the client to Android to bypass YouTube's desktop bot-detection
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }
    # Only use the cookie file if the user has manually provided one
    if os.path.exists("cookies.txt"):
        print("-> Found cookies.txt! Using it to bypass YouTube bot detection.")
        opts["cookiefile"] = "cookies.txt"
    return opts

def download_media(url):
    """Downloads both the audio (for transcription) and the video without audio (for dubbing)."""
    print(f"\nPreparing to download media from: {url}")
    
    audio_opts = get_youtube_options("bestaudio/best", "downloads/original_audio.%(ext)s")
    video_opts = get_youtube_options("bestvideo/best", "downloads/original_video.%(ext)s")
    
    try:
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info_dict)
            
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
            
        return audio_path, video_path
    except yt_dlp.utils.DownloadError as e:
        if "Sign in to confirm" in str(e) or "bot" in str(e).lower():
            print("\n" + "="*60)
            print("🚨 YOUTUBE ANTI-BOT TRIGGERED 🚨")
            print("YouTube blocked this download because it suspects you are a bot.")
            print("To fix this, you must provide a 'cookies.txt' file.")
            print("1. Install 'Get cookies.txt LOCALLY' extension in your browser.")
            print("2. Go to YouTube, click the extension, and export.")
            print("3. Save the file as 'cookies.txt' in this folder and try again.")
            print("="*60 + "\n")
            sys.exit(1)
        else:
            print(f"\nAn error occurred while downloading: {e}")
            sys.exit(1)
def speech_to_text(audio_path):
    print("Loading multilingual base Whisper model...")
    # 'base' supports multiple languages and is a good balance of speed and accuracy.
    # compute_type="int8" and cpu_threads=8 force maximum CPU efficiency
    model = WhisperModel("base", compute_type="int8", cpu_threads=8)
    
    print(f"Transcribing audio: {audio_path}...")
    # vad_filter=True removes silence, beam_size=1 skips deep analysis for raw speed
    segments, info = model.transcribe(
        audio_path, 
        beam_size=1, 
        vad_filter=True
    )
    
    print("Audio transcribed successfully.")
    
    text = "".join([segment.text for segment in segments])
    
    return text.strip()

def translate_text(text, target_lang):
    print(f"\nTranslating text to '{target_lang}'...")
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        
        # Google Translate has a 5000 character limit. We need to chunk long text.
        chunk_size = 4500
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        translated_text = ""
        for i, chunk in enumerate(chunks):
            translated_text += translator.translate(chunk) + " "
            time.sleep(1)  # Important for 2-4 hour movies to avoid getting banned
            
        return translated_text.strip()
    except Exception as e:
        print(f"\n[Error] Translation failed: {e}")
        return None

def text_to_audio(text, lang_code, output_path="downloads/translated_audio.mp3"):
    print(f"\nGenerating high-quality neural audio in '{lang_code}'...")
    try:
        # Create downloads folder if it doesn't exist
        os.makedirs("downloads", exist_ok=True)
        
        # Pick the high-quality voice, default to English if code not explicitly mapped
        voice = VOICE_MAPPING.get(lang_code.lower(), "en-US-ChristopherNeural")
        
        # Edge TTS uses asyncio
        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
        asyncio.run(_generate())
        
        print(f"🎉 High-quality audio successfully saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"\n[Error] Failed to generate audio: {e}")
        return None
def merge_audio_video(video_path, audio_path, output_path="downloads/final_dubbed_video.mp4"):
    print("\nMerging translated audio with the original video using FFmpeg...")
    # This command copies the video stream and encodes the audio stream, merging them.
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",  # Take the video stream from the first input (video_path)
        "-map", "1:a:0",  # Take the audio stream from the second input (audio_path)
        "-c:v", "copy",
        "-c:a", "aac",
        # Sometimes original videos have weird audio tracks, so we explicitly overwrite them
        "-shortest", 
        output_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n🎉 SUCCESS! Final dubbed video saved to: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"\n[Error] Failed to merge video and audio: {e}")
        return None

if __name__ == "__main__":
    translate_lang = input("Enter the language code to translate to (e.g., 'en' for English, 'es' for Spanish, 'hi' for Hindi): ")
    
    start_time = time.time()
    audio_file, video_file = download_media(video_url)
    transcribed_text = speech_to_text(audio_file)
    
    if translate_lang.strip():
        # Remove quotes just in case the user types 'ml' instead of ml
        lang_code = translate_lang.strip().replace("'", "").replace('"', "")
        final_translated_text = translate_text(transcribed_text, lang_code)
        
        if final_translated_text:
            generated_audio_path = text_to_audio(final_translated_text, lang_code)
            if generated_audio_path:
                merge_audio_video(video_file, generated_audio_path)
            
    end_time = time.time()
    print(f"\nTotal time taken: {end_time - start_time:.2f} seconds")