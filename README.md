# VidLingua

VidLingua is a command-line tool that automates the translation and dubbing of YouTube videos. It downloads the original video, transcribes the audio, translates the text into a target language, generates a new voiceover using neural text-to-speech, and merges the new audio back into the video file.

## Dependencies

- **Python 3.8+**
- **FFmpeg**: Must be installed and accessible in your system's `PATH`.

## Installation

1. Clone or download this repository.
2. Navigate to the `VidLingua` directory.
3. Install the package using `pip`:

```bash
pip install -e .
```

## Usage

```bash
Vidlingua run --yt-url <URL> --translate-to <LANG_CODE> [OPTIONS]
```

### Options

| Option | Description | Default |
| :--- | :--- | :--- |
| `--yt-url` | **(Required)** The YouTube video URL. | |
| `--translate-to` | **(Required)** The target language code (e.g., `en`, `hi`, `ml`). | |
| `--destination` | Directory to save the final video. | `~/Downloads` |

### Examples

Translate to English and save to the default Downloads folder:
```bash
Vidlingua run --yt-url "https://youtube.com/watch?v=..." --translate-to "en"
```

Translate to Hindi and save to a specific directory:
```bash
Vidlingua run --yt-url "https://youtube.com/watch?v=..." --translate-to "hi" --destination "./my_videos"
```

## Supported Languages

VidLingua maps high-quality Neural TTS voices to the following language codes. Other language codes supported by Google Translate will fall back to a default voice.

| Code | Language |
| :--- | :--- |
| `en` | English |
| `hi` | Hindi |
| `ml` | Malayalam |
| `ta` | Tamil |
| `kn` | Kannada |
| `te` | Telugu |
