import argparse
import os
import sys
import tempfile

from Vidlingua.core import (
    download_media,
    speech_to_text,
    translate_text,
    text_to_audio,
    merge_audio_video,
)
from Vidlingua.exceptions import VidLinguaError


def main():
    parser = argparse.ArgumentParser(
        description="VidLingua: Video Translation and Dubbing"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the translation process")
    run_parser.add_argument("--yt-url", required=True, help="YouTube video URL")
    run_parser.add_argument(
        "--translate-to",
        required=True,
        help="Language code to translate to (e.g., 'en', 'es', 'hi')",
    )
    run_parser.add_argument(
        "--destination",
        default=os.path.expanduser("~/Downloads"),
        help="Directory to save the final dubbed video (defaults to system Downloads folder)",
    )

    args = parser.parse_args()

    if args.command == "run":
        video_url = args.yt_url
        translate_lang = args.translate_to

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_file, video_file = download_media(video_url, temp_dir)
                transcribed_text = speech_to_text(audio_file)

                if translate_lang.strip():
                    lang_code = translate_lang.strip().replace("'", "").replace('"', "")
                    final_translated_text = translate_text(transcribed_text, lang_code)

                    if final_translated_text:
                        temp_audio_path = os.path.join(temp_dir, "translated_audio.mp3")
                        generated_audio_path = text_to_audio(
                            final_translated_text, lang_code, temp_audio_path
                        )
                        if generated_audio_path:
                            os.makedirs(args.destination, exist_ok=True)
                            final_video_path = os.path.join(
                                args.destination, "final_dubbed_video.mp4"
                            )
                            merge_audio_video(video_file, generated_audio_path, final_video_path)
        except VidLinguaError as e:
            print(f"\n[Error] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
