from flask import Flask, send_from_directory, request, jsonify
import requests

app = Flask(__name__, static_url_path='')

@app.route('/')
def root():
    return send_from_directory('', 'index.html')

@app.route('/api/autopilot/turn-left', methods=['POST'])
def turn_left():
    # Relay the request to the autopilot plugin
    response = requests.post('http://localhost:YOUR_PLUGIN_PORT/turn-left')
    return jsonify(response.json())

@app.route('/api/autopilot/turn-right', methods=['POST'])
def turn_right():
    # Relay the request to the autopilot plugin
    response = requests.post('http://localhost:YOUR_PLUGIN_PORT/turn-right')
    return jsonify(response.json())

@app.route('/api/autopilot/set-course', methods=['POST'])
def set_course():
    data = request.json
    response = requests.post('http://localhost:YOUR_PLUGIN_PORT/set-course', json=data)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
