from flask import Flask, render_template
import asyncio
from flask_socketio import SocketIO
import websockets
import logging
import json
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", debug=True)

# Set up logging
logging.basicConfig(
    filename='/home/pi/signalk-app/myapp.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

@app.route("/")
def index():
    app.logger.info('aa21 Serving index page.')
    return render_template('index.html')

listener_started = False  # Prevent duplicate listeners # response 2

@socketio.on("connect")
def handle_connect():
    global listener_started  # response 2
    app.logger.info("aa28 Client connected.")
    if not listener_started:  # response 2
        listener_started = True # response 2
        socketio.start_background_task(signalk_listener) # response 2

@socketio.on("disconnect")
def handle_disconnect():
    app.logger.info("aa28 Client disconnected.")

async def signalk_listener():
    app.logger.info("aa31 signalk_listener started.")
    url = "ws://fidelibe.local:3000/signalk/v1/stream?subscribe=all"
    try:
        async with websockets.connect(url) as websocket:
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)  # Attempt to parse the message
                    app.logger.debug(f"aa40 Parsed data: {data}")  # Log parsed JSON
                except json.JSONDecodeError as e:
                    app.logger.error(f"JSON decode error: {e}, message: {message}")  # Log error
                updates = []
                for update in data.get("updates", []):
                    for value in update.get("values", []):
                        path = value.get("path")
                        app.logger.debug(f"aa47 path=: {path}") 
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
                    app.logger.info(f"aa135 Emitted data: {updates}")
    except Exception as e:
        app.logger.error(f"aa98 Error in signalk_listener: {e}")

# Run the listener as a background task
#@socketio.on("connect")
#def start_listener_on_connect():
#    socketio.start_background_task(signalk_listener)

try:
    socketio.run(app, host="0.0.0.0", port=8001)
except KeyboardInterrupt:
    app.logger.info("Server has been manually stopped.")