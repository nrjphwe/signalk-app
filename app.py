from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/public/<path:path>')
def send_public(path):
    return app.send_static_file('public/' + path)

@app.route('/signalk/v1/api/vessels/self/<path:path>', methods=['PUT'])
def handle_put(path):
    data = request.json
    print(f"Received PUT request for {path} with data: {data}")
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
