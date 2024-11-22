from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import asyncio
import websockets
import json
import time
from threading import Thread
import logging

app = Flask(__name__)
# Add CORS support to your Flask app
CORS(app, resources={r"/*": {"origins": "*"}})

# Set up logging
logging.basicConfig(
    filename='/home/pi/signalk-app/myapp.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Add a global variable to track the last time autopilot data was received
last_autopilot_time = time.time()

socketio = SocketIO(app, cors_allowed_origins = "*", logger=True, engineio_logger=True)

@app.route('/')
#@app.route('/index')
def index():
    app.logger.info(f'a30 Home page accessed')
    return render_template('index.html')

@socketio.on("connect")
def handle_connect():
    app.logger.info("a35 Client connected.")
    #socketio.start_background_task(run_async_task)  # Start the async wrapper
    #socketio.start_background_task(asyncio.ensure_future, signalk_listener())
    socketio.start_background_task(signalk_listener)  # Direct coroutine

@socketio.on("disconnect")
def handle_disconnect():
    app.logger.info("a41 Client disconnected")

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

# Function to periodically check for autopilot inactivity
def check_autopilot_status():
    global last_autopilot_time
    while True:
        # If more than 10 seconds have passed since the last autopilot message, assume autopilot is off
        if time.time() - last_autopilot_time > 10:
            # Emit a message to the frontend that the autopilot is off
            socketio.emit('autopilot_status', {'status': 'off'})
        time.sleep(5)  # Check every second

# Start the check in a separate thread
Thread(target=check_autopilot_status, daemon=True).start()

async def signalk_listener():
    try:
        async with websockets.connect(SIGNALK_SERVER_URL) as websocket:
            app.logger.info("a68 Connected to SignalK server")
            global last_autopilot_time
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)  # Attempt to parse the message
                    app.logger.debug(f"a74 Parsed data: {data}")  # Log parsed JSON
                except json.JSONDecodeError as e:
                    app.logger.error(f"JSON decode error: {e}, message: {message}")  # Log error
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
                        # data from autopilot
                        elif path in { #steering
                            'steering.autopilot.state', # pgn:65379
                            'steering.autopilot.target.headingMagnetic', # pgn: 65360
                            'steering.autopilot.target.windAngleApparent', # pgn: 65345
                            'steering.rudderAngle',  # pgn: 127245
                            'steering.autopilot.target.headingTrue', # APB
                            'steering.autopilot.actions.tack',
                            'steering.autopilot.actions.adjustHeading',
                        }:
                            #print(f"a93 path in steering value = {value}")
                            if 'autopilot' in path:
                                last_autopilot_time = time.time()
                            updates.append(value)
                        # other data
                        elif path in { # navigation 
                            'navigation.headingTrue', # pgn:127250 
                            'navigation.headingMagnetic', # pgn: 65359
                            'navigation.magneticVariation', # HDG pgn: 127258
                            'navigation.courseOverGroundTrue', # VTG & pgn: 129038 129026
                            'navigation.speedOverGround', # SOG ,VTG & pgn:129039 129026
                            'navigation.speedThroughWater', # VHW
                        }:
                            updates.append(value)
                        elif path in { # environment
                            'environment.wind.angleApparent', # pgn: 130306
                            'environment.wind.speedApparent', # pgn: 130306
                            'environment.wind.directionTrue',
                            'environment.depth.belowKeel', # pgn: 128267
                            'environment.wind.angleTrueWaterDamped',
                            'environment.wind.speedTrue', # VWT

                        }:
                            updates.append(value)
                if updates:
                    socketio.emit("update_data", {"updates": updates})
                    app.logger.info(f"a135 Emitted data: {updates}")
    except Exception as e:
        app.logger.error(f"a127 WebSocket connection failed: {str(e)}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001)
    #socketio.run(app, host='0.0.0.0', port=8001, allow_unsafe_werkzeug=True)