from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid
import traceback
import shutil

app = Flask(__name__)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "downloads"
)

# Render Secret File
RENDER_COOKIE_FILE = "/etc/secrets/cookies.txt"

# Local development cookie file
LOCAL_COOKIE_FILE = os.path.join(
    BASE_DIR,
    "cookies.txt"
)

# Writable runtime location
RUNTIME_COOKIE_FILE = "/tmp/yt-dlp-cookies.txt"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)


# --------------------------------------------------
# COOKIE SETUP
# --------------------------------------------------

def prepare_cookie_file():

    # ----------------------------------------------
    # Render
    # ----------------------------------------------

    if os.path.exists(RENDER_COOKIE_FILE):

        try:

            shutil.copyfile(
                RENDER_COOKIE_FILE,
                RUNTIME_COOKIE_FILE
            )

            print(
                "Using Render Secret File:"
            )

            print(
                RENDER_COOKIE_FILE
            )

            print(
                "Copied cookies to:"
            )

            print(
                RUNTIME_COOKIE_FILE
            )

            return RUNTIME_COOKIE_FILE

        except Exception as e:

            print(
                "ERROR copying Render cookies:",
                repr(e)
            )

            raise

    # ----------------------------------------------
    # Local development
    # ----------------------------------------------

    if os.path.exists(LOCAL_COOKIE_FILE):

        print(
            "Using local cookie file:"
        )

        print(
            LOCAL_COOKIE_FILE
        )

        return LOCAL_COOKIE_FILE

    # ----------------------------------------------
    # No cookies found
    # ----------------------------------------------

    print(
        "WARNING: No cookies.txt found."
    )

    return None


# --------------------------------------------------
# YOUTUBE / YT-DLP CONFIG
# --------------------------------------------------

def get_ytdlp_options():

    cookie_file = prepare_cookie_file()

    options = {

        "quiet":
            True,

        "no_warnings":
            False,

        "noplaylist":
            True,

        # mweb successfully returned real
        # video formats during local testing.
        "extractor_args": {

            "youtube": {

                "player_client":
                    ["mweb"]

            }

        }

    }

    # Only add cookiefile when a cookie
    # file actually exists.

    if cookie_file:

        options["cookiefile"] = (
            cookie_file
        )

    return options


# --------------------------------------------------
# VIDEO INFO
# --------------------------------------------------

def get_video_info(url):

    options = get_ytdlp_options()

    cookie_file = options.get(
        "cookiefile"
    )

    print("========================================")
    print("YouTube request")
    print("Cookie file:", cookie_file)

    if cookie_file:

        print(
            "Cookie exists:",
            os.path.exists(cookie_file)
        )

        if os.path.exists(cookie_file):

            try:

                print(
                    "Cookie file size:",
                    os.path.getsize(
                        cookie_file
                    ),
                    "bytes"
                )

            except Exception:
                pass

    else:

        print(
            "No cookie file is being used."
        )

    print("========================================")

    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

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
    # PREPARE COOKIES
    # --------------------------------------------------

    cookie_file = prepare_cookie_file()

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

        # mweb worked during local testing.
        "extractor_args": {

            "youtube": {

                "player_client":
                    ["mweb"]

            }

        }

    }

    # Add writable cookie file.

    if cookie_file:

        options["cookiefile"] = (
            cookie_file
        )

    # --------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------

    print("========================================")
    print("DOWNLOAD REQUEST")
    print("URL:", url)
    print("Quality:", height)
    print("Cookie file:", cookie_file)

    if cookie_file:

        print(
            "Cookie exists:",
            os.path.exists(cookie_file)
        )

        if os.path.exists(cookie_file):

            try:

                print(
                    "Cookie file size:",
                    os.path.getsize(
                        cookie_file
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