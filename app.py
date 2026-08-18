from flask import Flask, render_template, request, send_file
import requests
import io
import os
import traceback

app = Flask(__name__)

# ============================================================
# PC DOWNLOADER
# ============================================================

DOWNLOADER_URL = os.environ.get(
    "DOWNLOADER_URL",
    ""
).rstrip("/")

DOWNLOADER_API_KEY = os.environ.get(
    "DOWNLOADER_API_KEY",
    ""
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

    return render_template(
        "result.html",
        video_id="",
        title="YouTube Video",
        url=url
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
    # CHECK DOWNLOADER CONFIG
    # --------------------------------------------------------

    if not DOWNLOADER_URL:

        print(
            "ERROR: DOWNLOADER_URL is not configured."
        )

        return (
            "Downloader service is not configured.",
            500
        )

    if not DOWNLOADER_API_KEY:

        print(
            "ERROR: DOWNLOADER_API_KEY is not configured."
        )

        return (
            "Downloader API key is not configured.",
            500
        )

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
    # DOWNLOADER URL
    # --------------------------------------------------------

    endpoint = (
        DOWNLOADER_URL
        + "/download"
    )

    print(
        "========================================"
    )

    print(
        "REMOTE DOWNLOAD"
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
        "DOWNLOADER:",
        DOWNLOADER_URL
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # REQUEST TO PC WORKER
    # --------------------------------------------------------

    try:

        response = requests.post(

            endpoint,

            headers={
                "Authorization":
                    "Bearer "
                    + DOWNLOADER_API_KEY
            },

            json={
                "url": url,
                "quality": height
            },

            timeout=900

        )

        print(
            "DOWNLOADER STATUS:",
            response.status_code
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if response.status_code == 200:

            print(
                "DOWNLOAD SUCCESS"
            )

            return send_file(

                io.BytesIO(
                    response.content
                ),

                mimetype=(
                    response.headers.get(
                        "Content-Type",
                        "video/mp4"
                    )
                ),

                as_attachment=True,

                download_name="video.mp4"

            )

        # ----------------------------------------------------
        # ERROR FROM PC WORKER
        # ----------------------------------------------------

        try:

            error_data = response.json()

            error_message = error_data.get(
                "error",
                "Downloader failed."
            )

        except Exception:

            error_message = (
                response.text
                or "Downloader failed."
            )

        print(
            "DOWNLOADER ERROR:"
        )

        print(
            error_message
        )

        return (
            "Download failed: "
            + error_message,
            response.status_code
            if response.status_code >= 400
            else 500
        )

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except requests.exceptions.Timeout:

        print(
            "DOWNLOADER TIMEOUT"
        )

        return (
            "The downloader took too long to respond.",
            504
        )

    # --------------------------------------------------------
    # CONNECTION ERROR
    # --------------------------------------------------------

    except requests.exceptions.ConnectionError as e:

        print(
            "DOWNLOADER CONNECTION ERROR"
        )

        print(
            repr(e)
        )

        return (
            "Could not connect to the PC downloader.",
            502
        )

    # --------------------------------------------------------
    # OTHER ERROR
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

        return (
            "Download failed: "
            + str(e),
            500
        )


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "downloader": DOWNLOADER_URL != ""
    }


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