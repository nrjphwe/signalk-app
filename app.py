from flask import Flask, render_template
from flask_socketio import SocketIO
app = Flask(__name__)
from flask_cors import CORS
import asyncio
import websockets
import json
import time
from threading import Thread
import logging

# Set up logging
logging.basicConfig(
    filename='/home/pi/signalk-app/myapp.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
# Add CORS support to your Flask app
CORS(app, resources={r"/*": {"origins": "*"}})

# Add a global variable to track the last time autopilot data was received
last_autopilot_time = time.time()

socketio = SocketIO(app, cors_allowed_origins=["http://192.168.0.4","http://fidelibe.local:8001"], logger=True, engineio_logger=True)
#socketio = SocketIO(app, cors_allowed_origins = "*", logger=True, engineio_logger=True)
#socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
#@app.route('/index')
def index():
    app.logger.info('a28 Home page accessed')
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    app.logger.info("a33 Client connected")
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
            app.logger.info("A63 Connected to SignalK server")
            global last_autopilot_time
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
                    app.logger.info(f"a120 Emitted data: {updates}")
    except Exception as e:
        app.logger.error(f"a122 WebSocket connection failed: {str(e)}")
# Wrapper function to start the asyncio event loop
def run_async_task():
    asyncio.run(signalk_listener())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001, allow_unsafe_werkzeug=True)