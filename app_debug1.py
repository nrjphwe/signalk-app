# with websocket-client's create_connection
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask import request
from websocket import create_connection
import logging
import json
import time

app = Flask(__name__)
#socketio = SocketIO(app, cors_allowed_origins="*", debug=True)
#socketio = SocketIO(app, async_mode="eventlet")
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25,logger=True, engineio_logger=True)

# Set up logging
logging.basicConfig(
    filename='/home/pi/signalk-app/myapp.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
# Flag to ensure the listener starts only once
listener_started = False

@app.route("/")
def index():
    app.logger.info('aa25 Serving index page.')
    return render_template('index.html')

@socketio.on("disconnect")
def handle_disconnect():
    app.logger.info(f"aa41 Client disconnected. SID: {request.sid}")

@socketio.on("connect")
def test_connect():
    app.logger.info("aa44 Client connected")
    socketio.emit("test_event", {"message": "Test event successful!"})

    # Start the SignalK listener in the background
    global listener_started
    if not listener_started:
        listener_started = True
        socketio.start_background_task(signalk_listener)

def signalk_listener():
    app.logger.info("aa41 signalk_listener started.")
    url = "ws://fidelibe.local:3000/signalk/v1/stream?subscribe=all"
    try:
        ws = create_connection(url)
        while True:
            time.sleep(1)
            message = ws.recv()  # Blocking call to receive messages
            try:
                data = json.loads(message)  # Attempt to parse the message
                app.logger.debug(f"aa49 Parsed data: {data}")  # Log parsed JSON
            except json.JSONDecodeError as e:
                app.logger.error(f"JSON decode error: {e}, message: {message}")  # Log error
                continue  # Skip processing this message

            updates = []
            for update in data.get("updates", []):
                for value in update.get("values", []):
                    path = value.get("path")
                    app.logger.debug(f"aa58 path=: {path}")
                    if path in {  # performance
                        'performance.maxSpeedAngle',
                        'performance.maxSpeed',
                        'performance.targetSpeed',
                        'performance.targetAngle',
                        'performance.polarSpeed',
                        'performance.gybeAngle',
                        'performance.beatAngle',
                    }:
                        updates.append(value)
                    elif path in {  # steering
                        'steering.autopilot.state',
                        'steering.autopilot.target.headingMagnetic',
                        'steering.autopilot.target.windAngleApparent',
                        'steering.rudderAngle',
                        'steering.autopilot.target.headingTrue',
                        'steering.autopilot.actions.tack',
                        'steering.autopilot.actions.adjustHeading',
                    }:
                        updates.append(value)
                    elif path in {  # navigation
                        'navigation.headingTrue',
                        'navigation.headingMagnetic',
                        'navigation.magneticVariation',
                        'navigation.courseOverGroundTrue',
                        'navigation.speedOverGround',
                        'navigation.speedThroughWater',
                    }:
                        updates.append(value)
                    elif path in {  # environment
                        'environment.wind.angleApparent',
                        'environment.wind.speedApparent',
                        'environment.wind.directionTrue',
                        'environment.depth.belowKeel',
                        'environment.wind.angleTrueWaterDamped',
                        'environment.wind.speedTrue',
                    }:
                        updates.append(value)

            if updates:
                socketio.emit("update_data", {"updates": updates})
                app.logger.info(f"aa104 Emitted data: {updates}")
    except Exception as e:
        app.logger.error(f"aa98 Error in signalk_listener: {e}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8001)