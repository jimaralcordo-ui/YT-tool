from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid
import traceback

app = Flask(__name__)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "downloads"
)

# Render Secret File location.
# If running locally, fall back to cookies.txt
# beside app.py.
RENDER_COOKIE_FILE = "/etc/secrets/cookies.txt"
LOCAL_COOKIE_FILE = os.path.join(
    BASE_DIR,
    "cookies.txt"
)

if os.path.exists(RENDER_COOKIE_FILE):
    COOKIE_FILE = RENDER_COOKIE_FILE
else:
    COOKIE_FILE = LOCAL_COOKIE_FILE

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)


# --------------------------------------------------
# YOUTUBE / YT-DLP CONFIG
# --------------------------------------------------

def get_ytdlp_options():

    options = {
        "quiet": True,
        "no_warnings": False,
        "noplaylist": True,

        # Use Render Secret File in production,
        # or local cookies.txt during development.
        "cookiefile": COOKIE_FILE,

        # mweb successfully returned real formats
        # during local testing.
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb"]
            }
        }
    }

    return options


# --------------------------------------------------
# VIDEO INFO
# --------------------------------------------------

def get_video_info(url):

    options = get_ytdlp_options()

    print("========================================")
    print("YouTube request")
    print("Cookie file:", COOKIE_FILE)
    print(
        "Cookie exists:",
        os.path.exists(COOKIE_FILE)
    )

    if os.path.exists(COOKIE_FILE):

        try:

            print(
                "Cookie file size:",
                os.path.getsize(
                    COOKIE_FILE
                ),
                "bytes"
            )

        except Exception:
            pass

    print("========================================")

    with yt_dlp.YoutubeDL(options) as ydl:

        return ydl.extract_info(
            url,
            download=False
        )


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# --------------------------------------------------
# PROCESS / GET VIDEO INFORMATION
# --------------------------------------------------

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


# --------------------------------------------------
# WAIT PAGE
# --------------------------------------------------

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


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

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

    # --------------------------------------------------
    # AUTHORIZATION
    # --------------------------------------------------
    #
    # Keep your own authorization/licensing checks here.
    #

    authorized = True

    if not authorized:

        return (
            "Download not permitted for this video.",
            403
        )

    # --------------------------------------------------
    # QUALITY
    # --------------------------------------------------

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

    # --------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------

    filename = str(
        uuid.uuid4()
    )

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        filename + ".%(ext)s"
    )

    # --------------------------------------------------
    # YT-DLP OPTIONS
    # --------------------------------------------------

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
            True,

        "no_warnings":
            False,

        # Use Render Secret File or local cookies.
        "cookiefile":
            COOKIE_FILE,

        # mweb was the client that returned
        # real video formats locally.
        "extractor_args": {

            "youtube": {

                "player_client":
                    ["mweb"]

            }

        }
    }

    # --------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------

    print("========================================")
    print("DOWNLOAD REQUEST")
    print("URL:", url)
    print("Quality:", height)
    print("Cookie file:", COOKIE_FILE)

    print(
        "Cookie exists:",
        os.path.exists(COOKIE_FILE)
    )

    if os.path.exists(COOKIE_FILE):

        try:

            print(
                "Cookie file size:",
                os.path.getsize(
                    COOKIE_FILE
                ),
                "bytes"
            )

        except Exception:
            pass

    print("========================================")

    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download(
                [url]
            )

        # --------------------------------------------------
        # FIND DOWNLOADED FILE
        # --------------------------------------------------

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

        filepath = os.path.join(
            DOWNLOAD_FOLDER,
            matching_files[0]
        )

        # --------------------------------------------------
        # SEND FILE
        # --------------------------------------------------

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


# --------------------------------------------------
# LOCAL DEVELOPMENT
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )