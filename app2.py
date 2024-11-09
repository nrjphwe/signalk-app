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
            data = json.loads(message) #https://www.geeksforgeeks.org/json-loads-in-python/

            updates = []
            for update in data.get("updates", []):
                for value in update.get("values", []):
                    path = value.get("path")
                    # data from polar performance plugin
                    if path in { # performance
                        'performance.maxSpeedAngle',
                        'performance.maxSpeed',
                        'performance.targetSpeed',
                        'performance.targetAngle',
                        'performance.polarSpeed',
                        'performance.gybeAngle',
                        'performance.beatAngle',
                    }:
                        updates.append(value)
                    # data fromn autopilot
                    elif path in { #steering
                        'steering.autopilot.target.headingMagnetic',
                        'steering.autopilot.target.headingTrue', # APB
                        'steering.autopilot.state',
                        'steering.autopilot.target.windAngleApparent',
                    }:
                        updates.append(value)
                    # other data
                    elif path in { # navigation 
                        'navigation.headingTrue', # pgn:127250
                        'navigation.headingMagnetic',
                        'navigation.magneticVariation', # RMC, HDG & pgn:127250
                        'navigation.courseOverGroundTrue', # VTG & pgn: 129038
                        'navigation.speedOverGround', # SOG ,VTG & pgn:129039
                        'navigation.speedThroughWater', # VHW
                        'navigation.courseOverGroundTrue', # pgn:129039
                    }:
                        updates.append(value)

                    elif path in { # environment
                        "environment.wind.angleApparent",
                        'environment.wind.directionTrue',
                        'environment.depth.belowKeel',
                        'environment.wind.angleTrueWaterDamped',
                        'environment.wind.speedTrue', # VWT

                    }:
                        updates.append(value)
            if updates:
                socketio.emit("update_data", {"updates": updates})
                print(f"a84 Emitted data: {updates}")

# Wrapper function to start the asyncio event loop
def run_async_task():
    asyncio.run(signalk_listener())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001)
