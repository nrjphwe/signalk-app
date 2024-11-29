# with websocket-client's create_connection, 2024-11-23.
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask import request
import eventlet
from websocket import create_connection
import logging
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', ping_timeout=60, ping_interval=25)

# Set up logging
logging.basicConfig(
    filename='/home/pi/signalk-app/myapp.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Flag to ensure the listener starts only once
listener_started = False


@app.route("/")
def index():
    app.logger.info('aa30 Serving index page.')
    return render_template('index.html')


@socketio.on("disconnect")
def handle_disconnect():
    app.logger.info(f"aa35 Client disconnected. SID: {request.sid}")


@socketio.on("connect")
def test_connect():
    app.logger.info("aa37 Client connected")
    socketio.emit("test_event", {"message": "Test event successful!"})
    # Start the SignalK listener in the background
    global listener_started
    if not listener_started:
        listener_started = True
        socketio.start_background_task(signalk_listener)


def signalk_listener():
    app.logger.debug("aa46 signalk_listener started.")
    url = "ws://fidelibe.local:3000/signalk/v1/stream?subscribe=all"
    global last_autopilot_time
    try:
        ws = create_connection(url)
        app.logger.info("aa67 Connected to SignalK WebSocket.")
        while True:
            # Non-blocking sleep to prevent blocking other tasks
            eventlet.sleep(1)
            try:
                # Blocking call to receive messages
                message = ws.recv()
                app.logger.debug(f"aa56 Received message: {message[:400]}")
                try:
                    data = json.loads(message)
                    app.logger.debug(f"aa59 Parsed data: {data}")
                except json.JSONDecodeError as e:
                    app.logger.error(f"aa61 JSON parsing error: {e}")
                    continue
                updates = []
                for update in data.get("updates", []):
                    for value in update.get("values", []):
                        path = value.get("path")
                        app.logger.debug(f"aa67 path=: {path}")
                        if path in {  # navigation
                            'navigation.speedThroughWater',
                            'navigation.speedOverGround',
                            'navigation.headingTrue',
                            'navigation.headingMagnetic',
                            'navigation.magneticVariation',
                            'navigation.courseOverGroundTrue',
                        }:
                            updates.append(value)
                        elif path in {  # performance
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
                app.logger.error(f"aa110 Error in signalk_listener: {e}")
                pass
    except Exception as e:
        app.logger.error(f"aa108 Failed to connect to SignalK WebSocket: {e}")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8001)