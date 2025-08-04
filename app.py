from flask import Flask, render_template, request
import os
import remove_times
import timesheet_helper
import re

app = Flask(__name__)


def clean_ansi_codes(text):
    """Remove ANSI escape codes from text for web display"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        timesheet_text = request.form.get("timesheet_text", "")

        if timesheet_text.strip():
            # Process the timesheet using the existing functions
            email_format_raw = remove_times.remove_timespans(timesheet_text)
            duration_format_raw = timesheet_helper.replace_with_duration(timesheet_text)
            # Clean ANSI codes for web display
            email_format = clean_ansi_codes(email_format_raw)
            duration_format = clean_ansi_codes(duration_format_raw)
            return render_template(
                "index.html",
                email_format=email_format,
                duration_format=duration_format,
                input_text=timesheet_text,
            )
        return render_template("index.html")
    else:
        return render_template("index.html")
if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(debug=debug, host=host, port=port)
