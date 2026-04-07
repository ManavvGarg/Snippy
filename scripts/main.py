from .voice_generator import text_to_speech
from .transcriber import transcribe, create_subtitles
from .editor import edit
from . import progress
import asyncio
import yaml
import re

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# defaults from config (used as fallback if UI doesn't provide them)
default_tts_model = config.get('tts-model', 'edge-tts')
subtitles_color1 = config['character-1-subtitles-color']
subtitles_color2 = config.get('character-2-subtitles-color', 'cyan')
default_voice_name_1 = config.get('tts-voice-name-1')
default_voice_name_2 = config.get('tts-voice-name-2')
default_voice_id_1 = config.get('tts-voice-id-1')
default_voice_id_2 = config.get('tts-voice-id-2')


async def generate_monologue_video(text, has_character, has_images, music_path, background_path,
                                    character_name='Yui', tts_model=None, elevenlabs_api_key=None,
                                    voice_id_1=None, voice_id_2=None, job_id=None):
    tts_model = tts_model or default_tts_model
    voice_name = default_voice_name_1
    voice_id = voice_id_1 or default_voice_id_1

    if tts_model == 'edge-tts' and not voice_name:
        raise ValueError("Missing edge-tts voice name in config.yaml")
    if tts_model == 'eleven-labs' and not voice_id:
        raise ValueError("Missing ElevenLabs voice ID")

    _emit(job_id, "Generating speech from script...")
    await text_to_speech(
        text,
        'static/temp/out.wav',
        voice_name=voice_name,
        voice_id=voice_id,
        model=tts_model,
        elevenlabs_api_key=elevenlabs_api_key,
    )

    _emit(job_id, "Transcribing audio...")
    subtitles, chunked_text = transcribe(has_images)

    _emit(job_id, "Creating subtitles...")
    subtitles = create_subtitles()

    _emit(job_id, "Compositing & rendering video...")
    await asyncio.to_thread(
        edit,
        subtitles=subtitles,
        chunked_text=chunked_text,
        music_path=music_path,
        background_path=background_path,
        color1=subtitles_color1,
        char_name1=character_name,
        has_images=has_images,
        has_character=has_character,
    )

    _emit(job_id, "Done!", status="completed")


async def generate_dialogue_video(text, has_character, character_name1, character_name2,
                                   music_path, background_path, has_images=False,
                                   tts_model=None, elevenlabs_api_key=None,
                                   voice_id_1=None, voice_id_2=None, job_id=None):
    tts_model = tts_model or default_tts_model
    dialogues = re.findall(r"(?m)^(.+?):\r?\n(.+?)(?=\r?\n\r?\n|\Z)", text)

    v_name_1 = default_voice_name_1
    v_name_2 = default_voice_name_2
    v_id_1 = voice_id_1 or default_voice_id_1
    v_id_2 = voice_id_2 or default_voice_id_2

    if tts_model == 'edge-tts' and (not v_name_1 or not v_name_2):
        raise ValueError("Missing edge-tts voice names in config.yaml")
    if tts_model == 'eleven-labs' and (not v_id_1 or not v_id_2):
        raise ValueError("Missing ElevenLabs voice IDs")

    # Generate all dialogue TTS in parallel
    _emit(job_id, f"Generating speech for {len(dialogues)} dialogue lines...")
    tasks = []
    for idx, (speaker, line) in enumerate(dialogues):
        if speaker == character_name1:
            voice_name = v_name_1
            voice_id = v_id_1
        else:
            voice_name = v_name_2
            voice_id = v_id_2

        tasks.append(text_to_speech(
            line,
            file_path=f"static/temp/audio/out_{idx}.wav",
            voice_name=voice_name,
            voice_id=voice_id,
            model=tts_model,
            elevenlabs_api_key=elevenlabs_api_key,
        ))

    await asyncio.gather(*tasks)

    _emit(job_id, "Transcribing audio...")
    subtitles, chunked_text, character_apper_durations = transcribe(has_images, gen_type='dialogue')

    _emit(job_id, "Creating subtitles...")
    subtitles = create_subtitles()

    _emit(job_id, "Compositing & rendering video...")
    await asyncio.to_thread(
        edit,
        subtitles=subtitles,
        chunked_text=chunked_text,
        music_path=music_path,
        background_path=background_path,
        color1=subtitles_color1,
        color2=subtitles_color2,
        char_name1=character_name1,
        char_name2=character_name2,
        has_images=has_images,
        has_character=has_character,
        character_apper_durations=character_apper_durations,
        gen_type='dialogue',
    )

    _emit(job_id, "Done!", status="completed")


def _emit(job_id, step, status="in_progress"):
    if job_id:
        progress.emit(job_id, step, status)
