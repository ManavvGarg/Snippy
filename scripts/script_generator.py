import json
import httpx


def generate_video_metadata(script_text, provider='openai', api_key=None):
    """Generate title, description, and tags from a video script."""
    system = (
        "You generate YouTube Shorts metadata from a video script. "
        "Return ONLY valid JSON with exactly these keys:\n"
        '{"title": "...", "description": "...", "tags": "tag1 tag2 tag3"}\n'
        "Title: catchy, under 70 chars. Description: 1-2 sentences. "
        "Tags: 5-8 space-separated keywords. No markdown, no extra text."
    )
    user_msg = f"Generate metadata for this script:\n\n{script_text}"

    if provider == 'openai':
        raw = _call_openai(api_key, system, user_msg)
    else:
        raw = _call_gemini(api_key, f"{system}\n\n{user_msg}")

    return json.loads(raw)


def _call_openai(api_key, system, user_msg):
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": 512,
            "temperature": 0.7,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(api_key, full_prompt):
    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 512, "temperature": 0.7},
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def generate_script(prompt, provider='openai', api_key=None, gen_type='monologue', char_name1=None, char_name2=None):
    if provider == 'openai':
        return _generate_openai(prompt, api_key, gen_type, char_name1, char_name2)
    elif provider == 'gemini':
        return _generate_gemini(prompt, api_key, gen_type, char_name1, char_name2)
    else:
        raise ValueError(f"Unknown script provider: {provider}")


def _build_system_prompt(gen_type, char_name1=None, char_name2=None):
    if gen_type == 'dialogue':
        return (
            f"You are a creative scriptwriter for short-form vertical videos. "
            f"Write a dialogue between two characters: {char_name1} and {char_name2}. "
            f"Use EXACTLY this format — character name, colon, newline, then the line. "
            f"Separate each block with a blank line. Example:\n\n"
            f"{char_name1}:\nFirst line of dialogue\n\n{char_name2}:\nSecond line of dialogue\n\n"
            f"Keep it short (30-60 seconds when spoken). Be entertaining, punchy, and engaging. "
            f"Only output the script, nothing else."
        )
    return (
        "You are a creative scriptwriter for short-form vertical videos. "
        "Write a monologue script that is entertaining, punchy, and engaging. "
        "Keep it short (30-60 seconds when spoken). "
        "Only output the raw script text, no formatting, no stage directions, no quotes."
    )


def _generate_openai(prompt, api_key, gen_type, char_name1, char_name2):
    system = _build_system_prompt(gen_type, char_name1, char_name2)
    return _call_openai(api_key, system, f"Write a script about: {prompt}")


def _generate_gemini(prompt, api_key, gen_type, char_name1, char_name2):
    system = _build_system_prompt(gen_type, char_name1, char_name2)
    return _call_gemini(api_key, f"{system}\n\nWrite a script about: {prompt}")
