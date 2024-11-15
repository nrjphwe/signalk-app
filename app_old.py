from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/public/<path:path>')
def send_public(path):
    return send_from_directory('public', path)

@app.route('/signalk/v1/api/vessels/self/<path:path>', methods=['PUT'])
def handle_put(path):
    data = request.json
    print(f"Received PUT request for {path} with data: {data}")
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
