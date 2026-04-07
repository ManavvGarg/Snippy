# Snippy

**A highly customizable short-form (brainrot) video generator with a web UI.**
Create dynamic, meme-style videos with custom characters, background music, AI voices, animated subtitles, and auto-generated context-relevant images.

## Generated video examples

https://github.com/user-attachments/assets/9822470a-cbad-4848-b7bd-66891ef280f0

## Features

### Video Generation Modes
- **Monologue mode** -- single character narrates a script with animated positioning (flips sides halfway through)
- **Dialogue mode** -- two characters take turns speaking, each with their own voice, subtitle color, and on-screen position

### AI Script Generation
- Write scripts manually or generate them with AI directly from the UI
- Supports **OpenAI (GPT)** and **Google Gemini** as script generation providers
- AI-generated metadata (title, description, tags) for publishing

### Text-to-Speech
- **Edge TTS** -- completely free, powered by Microsoft's multilingual neural voices
- **ElevenLabs** -- premium high-quality voices with multilingual v2 model support
- Per-character voice assignment for dialogue videos

### Animated Subtitles
- Word-by-word pop-in animation with scale effect
- Customizable subtitle colors per character via `config.yaml`
- Custom font support (ships with Rubik Black)

### Context-Relevant Image Overlays
- Automatically generates search queries from your script using **Groq (Llama 3.3 70B)**
- Fetches relevant images via **Google Programmable Search API**
- Overlays images at the correct timestamps during the video

### Audio Transcription
- Uses **OpenAI Whisper** for word-level timestamp transcription
- Sentence chunking with **spaCy NLP** for intelligent text segmentation

### Video Compositing
- Looping background videos (ships with Minecraft gameplay and more)
- Optional background music with auto-looping and volume ducking
- Anime-style character overlays with auto-mirroring (ships with Goku, Vegeta, Rem, Subaru, Fuu, Yui)
- 1080x1920 vertical format, optimized for YouTube Shorts / TikTok / Reels

### Publishing
- Publish generated videos directly to **YouTube** via the upload-post.com API
- Set title, description, and tags from the publish page

### Web Interface
- Clean Flask-based UI with monologue and dialogue pages
- Real-time progress tracking via Server-Sent Events (SSE)
- Video gallery to preview and manage generated videos
- Delete videos directly from the UI

## Installation

Use Python 3.10 or lower in your virtual environment, newer versions might break the install.

```bash
git clone https://github.com/manavc7/snippy.git
cd snippy
pip install -r requirements.txt
python app.py
```

## Configuration

Edit `config.yaml` to customize:

| Setting | Description |
|---|---|
| `tts-model` | TTS engine (`edge-tts` or `eleven-labs`) |
| `tts-voice-name-1/2` | Edge TTS voice names (run `edge-tts --list-voices` to see options) |
| `eleven-labs-api-key` | ElevenLabs API key |
| `tts-voice-id-1/2` | ElevenLabs voice IDs |
| `character-1/2-subtitles-color` | Subtitle color per character |
| `google-search-api-key` | Google Programmable Search API key (for image overlays) |
| `google-search-engine-id` | Custom Search Engine ID |
| `groq-api-key` | Groq API key (for AI-powered image search queries) |

## Tech Stack

- **Backend:** Flask, MoviePy, Pillow, pydub
- **TTS:** Edge TTS, ElevenLabs
- **Transcription:** OpenAI Whisper
- **NLP:** spaCy
- **AI Providers:** OpenAI, Google Gemini, Groq
- **Frontend:** HTML/CSS with vanilla JavaScript, SSE for real-time progress
