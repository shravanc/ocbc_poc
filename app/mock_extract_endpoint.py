from flask import Flask, send_from_directory
from flask_cors import CORS
import constant

app = Flask(__name__)
CORS(app)


@app.route('/extract', methods=["POST"])
def extract_data_route():
    with open("mock_response.json") as f:
        return f.read()


@app.route('/', methods=["GET"])
def home_page_route():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True, host=constant.HOST, port=constant.PORT_NUMBER)
