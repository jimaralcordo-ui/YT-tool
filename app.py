from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def get_video_info(url):
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():

    url = request.form.get("url", "").strip()

    if not url:
        return render_template(
            "index.html",
            error="Please enter a YouTube URL."
        )

    try:

        info = get_video_info(url)

        video_id = info.get("id")
        title = info.get("title", "Unknown video")

        return render_template(
            "result.html",
            video_id=video_id,
            title=title,
            url=url
        )

    except Exception as e:

        print("ERROR:", e)

        return render_template(
            "index.html",
            error="Video could not be accessed."
        )


@app.route("/wait")
def wait():

    url = request.args.get("url", "").strip()

    quality = request.args.get(
        "quality",
        "720"
    )

    if not url:
        return render_template(
            "index.html",
            error="Missing video URL."
        )

    return render_template(
        "wait.html",
        url=url,
        quality=quality
    )


@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url", "").strip()

    quality = request.form.get(
        "quality",
        "720"
    )

    if not url:
        return "Invalid request.", 400


    # For local testing only.
    # In production, verify that you have permission
    # to download the requested video.
    authorized = True

    if not authorized:
        return (
            "Download not permitted for this video.",
            403
        )


    # Convert selected quality to integer
    try:
        height = int(quality)
    except ValueError:
        height = 720


    # Only allow the qualities from the website
    if height not in [360, 480, 720, 1080]:
        height = 720


    filename = str(uuid.uuid4())

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        filename + ".%(ext)s"
    )


    options = {

        "format":
            f"best[height<={height}][ext=mp4]/"
            f"best[height<={height}]/"
            "18",

        "outtmpl":
            output_template,

        "merge_output_format":
            "mp4",

        "noplaylist":
            True,

        "quiet":
            True
    }


    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            ydl.download([url])


        matching_files = [

            f for f in os.listdir(
                DOWNLOAD_FOLDER
            )

            if f.startswith(
                filename + "."
            )
        ]


        if not matching_files:

            return (
                "Download failed.",
                500
            )


        filepath = os.path.join(
            DOWNLOAD_FOLDER,
            matching_files[0]
        )


        return send_file(

            filepath,

            as_attachment=True,

            download_name="video.mp4"

        )


    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            e
        )

        return (
            "Download failed.",
            500
        )


if __name__ == "__main__":

    app.run(
        debug=True
    )

