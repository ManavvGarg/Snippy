from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from scripts import main
from scripts.publish_videos import upload_video
from scripts.script_generator import generate_script, generate_video_metadata
from scripts import progress
import asyncio
import threading
import uuid
import json
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = "Jknvfk805034bnf58034jngfj034gnjr"

# Ensure all required directories exist
for _dir in [
    'static/musics',
    'static/background_videos',
    'static/temp',
    'static/temp/audio',
    'static/temp/videos',
    'static/temp/fetched_images',
    'static/characters/flipped_characters',
]:
    os.makedirs(_dir, exist_ok=True)


def _get_characters():
    chars_dir = 'static/characters'
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(chars_dir)
        if f.lower().endswith('.png') and not os.path.isdir(os.path.join(chars_dir, f))
    )


def _get_tts_params(form):
    tts_model = form.get('tts_model', 'edge-tts')
    elevenlabs_api_key = form.get('elevenlabs_api_key', '').strip() or None
    voice_id_1 = form.get('voice_id_1', '').strip() or None
    voice_id_2 = form.get('voice_id_2', '').strip() or None
    return tts_model, elevenlabs_api_key, voice_id_1, voice_id_2


def _run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Pages ──

@app.route("/", methods=['GET'])
def monologue_generator():
    music_files = os.listdir('static/musics')
    background_files = os.listdir('static/background_videos')
    video_files = os.listdir('static/temp/videos')
    characters = _get_characters()
    return render_template('monologue_generate.html', music_files=music_files, background_files=background_files, videos_path=video_files, characters=characters)


@app.route("/dialogue_content", methods=['GET'])
def dialogue_generator():
    music_files = os.listdir('static/musics')
    background_files = os.listdir('static/background_videos')
    video_files = os.listdir('static/temp/videos')
    characters = _get_characters()
    return render_template('duo_generate.html', music_files=music_files, background_files=background_files, videos_path=video_files, dialogue=True, characters=characters)


@app.route("/video/<video_path>", methods=['GET', 'POST'])
def video_detail(video_path):
    if request.method == 'POST':
        if 'remove' in request.form:
            os.remove(f'static/temp/videos/{video_path}')
            return redirect(url_for('monologue_generator'))
    return render_template('publish.html', video_path=video_path)


# ── Generation APIs ──

@app.route("/api/generate/monologue", methods=['POST'])
def api_generate_monologue():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    tts_model = data.get('tts_model', 'edge-tts')
    elevenlabs_api_key = data.get('elevenlabs_api_key', '').strip() or None
    voice_id_1 = data.get('voice_id_1', '').strip() or None

    coro = main.generate_monologue_video(
        data['script'],
        bool(data.get('display_character')),
        bool(data.get('images')),
        data['music'],
        data['background'],
        character_name=data.get('character', 'Yui'),
        tts_model=tts_model,
        elevenlabs_api_key=elevenlabs_api_key,
        voice_id_1=voice_id_1,
        job_id=job_id,
    )

    def _run():
        try:
            _run_async_in_thread(coro)
        except Exception as e:
            progress.emit(job_id, str(e), status="error")

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/generate/dialogue", methods=['POST'])
def api_generate_dialogue():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    tts_model = data.get('tts_model', 'edge-tts')
    elevenlabs_api_key = data.get('elevenlabs_api_key', '').strip() or None
    voice_id_1 = data.get('voice_id_1', '').strip() or None
    voice_id_2 = data.get('voice_id_2', '').strip() or None

    coro = main.generate_dialogue_video(
        data['script'],
        bool(data.get('display_character')),
        data.get('character_1', 'Rem'),
        data.get('character_2', 'Subaru'),
        data['music'],
        data['background'],
        tts_model=tts_model,
        elevenlabs_api_key=elevenlabs_api_key,
        voice_id_1=voice_id_1,
        voice_id_2=voice_id_2,
        job_id=job_id,
    )

    def _run():
        try:
            _run_async_in_thread(coro)
        except Exception as e:
            progress.emit(job_id, str(e), status="error")

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/progress/<job_id>")
def api_progress(job_id):
    def stream():
        for event in progress.listen(job_id):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ── Other APIs ──

@app.route("/api/generate_script", methods=['POST'])
def api_generate_script():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    provider = data.get('provider', 'openai')
    api_key = data.get('api_key', '').strip()
    gen_type = data.get('gen_type', 'monologue')
    char_name1 = data.get('char_name1')
    char_name2 = data.get('char_name2')

    if not prompt or not api_key:
        return jsonify({"error": "Prompt and API key are required"}), 400

    try:
        script = generate_script(
            prompt, provider=provider, api_key=api_key,
            gen_type=gen_type, char_name1=char_name1, char_name2=char_name2,
        )
        return jsonify({"script": script})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate_metadata", methods=['POST'])
def api_generate_metadata():
    data = request.get_json()
    script_text = data.get('script', '').strip()
    provider = data.get('provider', 'openai')
    api_key = data.get('api_key', '').strip()

    if not script_text or not api_key:
        return jsonify({"error": "Script text and API key are required"}), 400

    try:
        metadata = generate_video_metadata(script_text, provider=provider, api_key=api_key)
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/publish", methods=['POST'])
def api_publish():
    upload_api_key = request.form.get('upload_api_key', '').strip()
    user = request.form.get('user', '').strip()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    tags = request.form.get('tags', '').strip()
    video_path = request.form.get('video_path', '').strip()

    if not all([upload_api_key, user, title, video_path]):
        return jsonify({"error": "API key, user, title, and video are required"}), 400

    full_path = f'static/temp/videos/{video_path}'
    if not os.path.exists(full_path):
        return jsonify({"error": "Video file not found"}), 404

    try:
        result = upload_video(upload_api_key, full_path, title, description, user, tags)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
