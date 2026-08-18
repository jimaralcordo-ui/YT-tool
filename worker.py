from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import traceback

app = Flask(__name__)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DOWNLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "downloads"
)

COOKIE_FILE = os.path.join(
    BASE_DIR,
    "cookies.txt"
)

# ============================================================
# BGUTIL POT SERVER
# ============================================================

BGUTIL_URL = os.environ.get(
    "BGUTIL_URL",
    "http://127.0.0.1:4416"
)

# ============================================================
# API KEY
# ============================================================

API_KEY = os.environ.get(
    "DOWNLOADER_API_KEY",
    "CHANGE_THIS_KEY"
).strip()

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# API KEY CHECK
# ============================================================

def check_api_key():

    # --------------------------------------------------------
    # OPTION 1:
    # X-API-Key
    # --------------------------------------------------------

    x_api_key = request.headers.get(
        "X-API-Key",
        ""
    ).strip()

    # --------------------------------------------------------
    # OPTION 2:
    # Authorization: Bearer ...
    # --------------------------------------------------------

    authorization = request.headers.get(
        "Authorization",
        ""
    ).strip()

    bearer_key = ""

    if authorization.lower().startswith(
        "bearer "
    ):

        bearer_key = authorization[
            7:
        ].strip()

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print(
        "========== AUTH DEBUG =========="
    )

    print(
        "X-API-Key received:",
        bool(x_api_key)
    )

    print(
        "Authorization received:",
        bool(authorization)
    )

    print(
        "Bearer key received:",
        bool(bearer_key)
    )

    print(
        "API key configured:",
        bool(API_KEY)
    )

    print(
        "Expected key length:",
        len(API_KEY)
    )

    print(
        "X-API-Key length:",
        len(x_api_key)
    )

    print(
        "Bearer key length:",
        len(bearer_key)
    )

    print(
        "================================"
    )

    # --------------------------------------------------------
    # ACCEPT EITHER AUTH METHOD
    # --------------------------------------------------------

    if x_api_key == API_KEY:
        return True

    if bearer_key == API_KEY:
        return True

    return False


# ============================================================
# YT-DLP OPTIONS
# ============================================================

def get_options(
    height,
    output_template
):

    return {

        # ----------------------------------------------------
        # FORMAT
        # ----------------------------------------------------

        "format":
            f"bestvideo[height<={height}][ext=mp4]+"
            f"bestaudio[ext=m4a]/"
            f"best[height<={height}][ext=mp4]/"
            f"best[height<={height}]/"
            "18",

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        "outtmpl":
            output_template,

        "merge_output_format":
            "mp4",

        # ----------------------------------------------------
        # PLAYLIST
        # ----------------------------------------------------

        "noplaylist":
            True,

        # ----------------------------------------------------
        # COOKIES
        # ----------------------------------------------------

        "cookiefile":
            COOKIE_FILE,

        # ----------------------------------------------------
        # JAVASCRIPT RUNTIME
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {}
        },

        # ----------------------------------------------------
        # YOUTUBE EXTRACTOR
        # ----------------------------------------------------

        "extractor_args": {

            "youtube": {

                "player_client": [
                    "mweb"
                ]

            },

            # ------------------------------------------------
            # BGUTIL
            # ------------------------------------------------

            "youtubepot-bgutilhttp": {

                "base_url": [
                    BGUTIL_URL
                ]

            }

        },

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        "quiet":
            False,

        "no_warnings":
            False

    }


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "ok",

        "service":
            "youtube-downloader",

        "api_key_configured":
            bool(API_KEY)

    })


# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download():

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    if not check_api_key():

        print(
            "AUTHENTICATION FAILED"
        )

        return jsonify({

            "error":
                "Unauthorized"

        }), 401

    print(
        "AUTHENTICATION SUCCESS"
    )

    # --------------------------------------------------------
    # REQUEST DATA
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    url = str(
        data.get(
            "url",
            ""
        )
    ).strip()

    quality = data.get(
        "quality",
        720
    )

    # --------------------------------------------------------
    # URL VALIDATION
    # --------------------------------------------------------

    if not url:

        return jsonify({

            "error":
                "Missing YouTube URL"

        }), 400

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    try:

        height = int(
            quality
        )

    except (
        ValueError,
        TypeError
    ):

        height = 720

    if height not in [
        360,
        480,
        720,
        1080
    ]:

        height = 720

    # --------------------------------------------------------
    # UNIQUE FILE NAME
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

    options = get_options(

        height,

        output_template

    )

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    print(
        "========================================"
    )

    print(
        "REMOTE DOWNLOAD REQUEST"
    )

    print(
        "URL:",
        url
    )

    print(
        "QUALITY:",
        height
    )

    print(
        "COOKIE FILE:",
        COOKIE_FILE
    )

    print(
        "COOKIE EXISTS:",
        os.path.exists(
            COOKIE_FILE
        )
    )

    print(
        "BGUTIL:",
        BGUTIL_URL
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([
                url
            ])

        # ----------------------------------------------------
        # FIND OUTPUT FILE
        # ----------------------------------------------------

        files = [

            f

            for f in os.listdir(
                DOWNLOAD_FOLDER
            )

            if f.startswith(
                filename + "."
            )

        ]

        if not files:

            print(
                "OUTPUT FILE NOT FOUND"
            )

            return jsonify({

                "error":
                    "Download completed but output file was not found"

            }), 500

        # ----------------------------------------------------
        # PREFER MP4
        # ----------------------------------------------------

        mp4_files = [

            f

            for f in files

            if f.lower().endswith(
                ".mp4"
            )

        ]

        if mp4_files:

            filename_final = (
                mp4_files[0]
            )

        else:

            filename_final = (
                files[0]
            )

        # ----------------------------------------------------
        # FULL FILE PATH
        # ----------------------------------------------------

        filepath = os.path.join(

            DOWNLOAD_FOLDER,

            filename_final

        )

        print(
            "FILE READY:",
            filepath
        )

        # ----------------------------------------------------
        # SEND FILE
        # ----------------------------------------------------

        return send_file(

            filepath,

            as_attachment=True,

            download_name="video.mp4"

        )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    except Exception as e:

        print(
            "========================================"
        )

        print(
            "DOWNLOAD ERROR"
        )

        print(
            repr(e)
        )

        print(
            "========================================"
        )

        traceback.print_exc()

        return jsonify({

            "error":
                str(e)

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "YOUTUBE DOWNLOADER WORKER"
    )

    print(
        "API KEY CONFIGURED:",
        bool(API_KEY)
    )

    print(
        "API KEY LENGTH:",
        len(API_KEY)
    )

    print(
        "BGUTIL:",
        BGUTIL_URL
    )

    print(
        "COOKIE FILE:",
        COOKIE_FILE
    )

    print(
        "COOKIE EXISTS:",
        os.path.exists(
            COOKIE_FILE
        )
    )

    print(
        "========================================"
    )

    app.run(

        host="0.0.0.0",

        port=5001,

        debug=False

    )