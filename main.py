from flask import Flask, request, jsonify
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from youtube_transcript_api.proxies import WebshareProxyConfig
from dotenv import load_dotenv
import re
import os

load_dotenv()
app = Flask(__name__)

# Configure Webshare proxy globally for the API instance
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=os.getenv("WEBSHARE_USERNAME"),  # <-- Replace this
        proxy_password=os.getenv("WEBSHARE_PASSWORD")   # <-- Replace this
    )
)

@app.route('/')
def home():
    return '✅ Transcript microservice is running.'

@app.route("/transcript")
def transcript():
    vid = request.args.get("video_id")
    if not vid:
        return jsonify({"error": "Missing video_id"}), 400

    try:
        segments  = ytt_api.fetch(vid)
        full_text = " ".join(seg.text for seg in segments)

        if len(full_text) > 1_000:
            # try to remove the first sentence
            match = re.search(r"[.?!]\s+", full_text)
            if match:
                trimmed = full_text[match.end():]  # text after the first sentence
            else:
                # no punctuation early on → drop the first 15 words as a fallback
                trimmed = " ".join(full_text.split()[15:])

            # if it's still longer than 1 000, hard‑cut
            if len(trimmed) > 1_000:
                trimmed = trimmed[:1_000].rstrip()

            final_text = trimmed
        else:
            final_text = full_text

        return jsonify({"transcript": final_text})

    except TranscriptsDisabled:
        return jsonify({"error": "Captions are turned off"}), 403

    except VideoUnavailable:
        print(f"❌ Video unavailable: {vid}")
        return jsonify({ "error": "Video unavailable" }), 404

    except Exception as e:
        print(f"🚨 Unexpected error for {vid}:", str(e))
        return jsonify({ "error": str(e) }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)
