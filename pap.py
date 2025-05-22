from flask import Flask, redirect
import requests
from flask import Response
import requests
app = Flask(__name__)

@app.route('/')
def home():
    # Redirect to the target URL
    url = "http://localhost:8191/v1"
    headers = {"Content-Type": "application/json"}
    data = {
        "cmd": "request.get",
        "url": "https://ubg77.github.io/game131022/drive-mad/",
        "maxTimeout": 60000
    }

    response = requests.post(url, json=data, headers=headers)
    return str(Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type')))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)