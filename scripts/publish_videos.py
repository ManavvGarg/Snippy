import httpx

UPLOAD_POST_URL = "https://api.upload-post.com/api/upload"


def upload_video(api_key, video_path, title, description, user, tags=None):
    """Upload a video to YouTube via upload-post.com API."""
    with open(video_path, "rb") as video_file:
        files = {"video": (video_path.split("/")[-1], video_file, "video/mp4")}
        data = {
            "title": title,
            "description": description,
            "user": user,
            "platform[]": "youtube",
        }
        if tags:
            data["tags"] = tags

        response = httpx.post(
            UPLOAD_POST_URL,
            headers={"Authorization": f"Apikey {api_key}"},
            files=files,
            data=data,
            timeout=300,
        )
        response.raise_for_status()
        return response.json()
