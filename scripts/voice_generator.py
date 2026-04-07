import edge_tts
import asyncio
import os

_elevenlabs_client = None

def _get_elevenlabs_client(api_key=None):
    global _elevenlabs_client
    if _elevenlabs_client is None:
        from elevenlabs.client import ElevenLabs
        key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        _elevenlabs_client = ElevenLabs(api_key=key)
    return _elevenlabs_client


async def text_to_speech(text, file_path, voice_id='Xb7hH8MSUJpSbSDYk0k2', voice_name='en-US-AvaMultilingualNeural', model='edge-tts', elevenlabs_api_key=None):

    if model == 'eleven-labs':
        from elevenlabs import save
        client = _get_elevenlabs_client(elevenlabs_api_key)

        def _generate():
            audio = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
            )
            save(audio, file_path)

        await asyncio.to_thread(_generate)

    elif model == 'edge-tts':
        audio = edge_tts.Communicate(text=text, voice=voice_name)
        await audio.save(file_path)

    with open("static/temp/text.txt", "w", encoding="utf-8") as f:
        f.write(text)
