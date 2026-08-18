
from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid
import traceback

app = Flask(__name__)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "downloads"
)

# bgutil POT server
BGUTIL_URL = "http://127.0.0.1:4416"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# YT-DLP OPTIONS
# ============================================================

def get_ytdlp_options():

    options = {

        "quiet": True,

        "no_warnings": False,

        "noplaylist": True,

        "extractor_args": {

            "youtube": {

                # Use mweb client
                "player_client": [
                    "mweb"
                ]

            },

            "youtubepot-bgutilhttp": {

                # bgutil server
                "base_url": [
                    BGUTIL_URL
                ]

            }

        }

    }

    return options


# ============================================================
# VIDEO INFO
# ============================================================

def get_video_info(url):

    options = get_ytdlp_options()

    print("========================================")
    print("YOUTUBE REQUEST")
    print("URL:", url)
    print("COOKIES: DISABLED")
    print("BGUTIL:", BGUTIL_URL)
    print("========================================")

    with yt_dlp.YoutubeDL(options) as ydl:

        return ydl.extract_info(
            url,
            download=False
        )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# PROCESS
# ============================================================

@app.route(
    "/process",
    methods=["POST"]
)
def process():

    url = request.form.get(
        "url",
        ""
    ).strip()

    if not url:

        return render_template(
            "index.html",
            error="Please enter a YouTube URL."
        )

    try:

        info = get_video_info(
            url
        )

        video_id = info.get(
            "id"
        )

        title = info.get(
            "title",
            "Unknown video"
        )

        return render_template(
            "result.html",
            video_id=video_id,
            title=title,
            url=url
        )

    except Exception as e:

        print(
            "PROCESS ERROR:",
            repr(e)
        )

        traceback.print_exc()

        return render_template(
            "index.html",
            error=(
                "Video could not be accessed: "
                + str(e)
            )
        )


# ============================================================
# WAIT PAGE
# ============================================================

@app.route("/wait")
def wait():

    url = request.args.get(
        "url",
        ""
    ).strip()

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


# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download():

    url = request.form.get(
        "url",
        ""
    ).strip()

    quality = request.form.get(
        "quality",
        "720"
    )

    if not url:

        return (
            "Invalid request.",
            400
        )

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    try:

        height = int(
            quality
        )

    except ValueError:

        height = 720

    if height not in [
        360,
        480,
        720,
        1080
    ]:

        height = 720

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    filename = str(
        uuid.uuid4()
    )

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        filename + ".%(ext)s"
    )

    # --------------------------------------------------------
    # YT-DLP OPTIONS
    # --------------------------------------------------------

    options = {

        "format":
            f"bestvideo[height<={height}][ext=mp4]+"
            f"bestaudio[ext=m4a]/"
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
            True,

        "no_warnings":
            False,

        "extractor_args": {

            "youtube": {

                "player_client": [
                    "mweb"
                ]

            },

            "youtubepot-bgutilhttp": {

                "base_url": [
                    BGUTIL_URL
                ]

            }

        }

    }

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    print("========================================")
    print("DOWNLOAD REQUEST")
    print("URL:", url)
    print("QUALITY:", height)
    print("COOKIES: DISABLED")
    print("BGUTIL:", BGUTIL_URL)
    print("========================================")

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download(
                [url]
            )

        # ----------------------------------------------------
        # FIND OUTPUT
        # ----------------------------------------------------

        matching_files = [

            f

            for f in os.listdir(
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

        # ----------------------------------------------------
        # PREFER MP4
        # ----------------------------------------------------

        mp4_files = [

            f

            for f in matching_files

            if f.lower().endswith(
                ".mp4"
            )

        ]

        if mp4_files:

            filepath = os.path.join(
                DOWNLOAD_FOLDER,
                mp4_files[0]
            )

        else:

            filepath = os.path.join(
                DOWNLOAD_FOLDER,
                matching_files[0]
            )

        # ----------------------------------------------------
        # SEND FILE
        # ----------------------------------------------------

        return send_file(

            filepath,

            as_attachment=True,

            download_name="video.mp4"

        )

    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            repr(e)
        )

        traceback.print_exc()

        return (
            "Download failed: "
            + str(e),
            500
        )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
