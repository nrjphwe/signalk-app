from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import asyncio
import websockets
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
@app.route('/index2')
def index():
    return render_template('index2.html')

@socketio.on('connect')
def on_connect():
    print("a38 Client connected")
    socketio.start_background_task(run_async_task)  # Start the async wrapper

SIGNALK_SERVER_URL = "ws://fidelibe.local:3000/signalk/v1/stream?subscribe=all"

#######################################################################
# The signalk-polar-performance-plugin are reading the following paths:
# navigation.speedThroughWater
# environment.wind.speedTrue
# environment.wind.angleTrueWater
# navigation.speedOverGround (optional)
# see more: https://github.com/htool/signalk-polar-performance-plugin/
# sends maximum speed angle and max boat speed for a given TWS
#######################################################################


async def signalk_listener():
    async with websockets.connect(SIGNALK_SERVER_URL) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            updates = []
            for update in data.get("updates", []):
                for value in update.get("values", []):
                    path = value.get("path")
                    if path in {
                        'performance.maxSpeedAngle',
                        'performance.maxSpeed',
                        'performance.targetSpeed',
                        'performance.polarSpeed',
                        'performance.gybeAngle',
                        'performance.beatAngle',
                        'performance.targetAngle',
                        "environment.wind.angleApparent",
                        "navigation.headingMagnetic",
                        "steering.autopilot.state",
                        'steering.autopilot.target.windAngleApparent',
                        'navigation.headingMagnetic',
                        'steering.autopilot.target.headingMagnetic',
                    }:
                        updates.append(value)

            if updates:
                socketio.emit("update_data", {"updates": updates})
                #print(f"a34 Emitted data: {updates}")

# Wrapper function to start the asyncio event loop
def run_async_task():
    asyncio.run(signalk_listener())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001)
