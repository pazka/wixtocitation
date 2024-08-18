from flask import Flask, request, make_response, send_file, send_from_directory
from werkzeug.utils import secure_filename
from docgen import doc_gen
import traceback

import os

app = Flask(__name__)

# static in static folder
app.static_folder = 'static'


@app.route('/upload', methods=['POST'])
def upload_file():
    f = request.files['export']

    if f.content_type != 'text/csv':
        return "only csv accepted", 400

    f.save('./export.csv')
    filename = ""
    try:
        filename = doc_gen('./export.csv')
    except Exception as e:
        print(e)
        return make_response(f"Error: {str(e)}", 500)

    try:
        filename = secure_filename(filename)  # Sanitize the filename
        file_path = os.path.join("./", filename)
        if os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            print(e)
            return make_response(f"File '{filename}' not found.", 404)
    except Exception as e:
        print(e)
        return make_response(f"Error: {str(e)}", 500)


@app.route("/<path:path>")
def send_report(path):
    return send_from_directory('static', path)


@app.route("/")
def send_index():
    return send_from_directory('static', 'index.html')


PORT = os.environ.get("PORT") or 6451

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=PORT, debug=True)
