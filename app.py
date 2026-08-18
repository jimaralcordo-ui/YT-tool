from flask import Flask, render_template, request
import re

app = Flask(__name__)


def get_youtube_id(url):
    patterns = [
        r"(?:youtube\.com/watch\?v=)([^&]+)",
        r"(?:youtu\.be/)([^?&]+)",
        r"(?:youtube\.com/shorts/)([^?&]+)",
        r"(?:youtube\.com/embed/)([^?&]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():

    url = request.form.get("url", "").strip()

    video_id = get_youtube_id(url)

    if not video_id:
        return render_template(
            "index.html",
            error="Invalid YouTube URL."
        )

    return render_template(
        "result.html",
        video_id=video_id
    )


if __name__ == "__main__":
    app.run(debug=True)