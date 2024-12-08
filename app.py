# with websocket-client's create_connection, 2024-11-23.
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask import request
import eventlet
from websocket import create_connection, WebSocketConnectionClosedException
import logging
import json

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*", 
    async_mode='eventlet', 
    ping_timeout=60, 
    ping_interval=25
    )

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
    app.logger.warning(f"aa35 Client disconnected. SID: {request.sid}")


@socketio.on("connect")
def test_connect():
    app.logger.warning("aa37 Client connected")
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

    while True:   # Loop to handle reconnections
        ws = None
        try:
            app.logger.info("aa60 Attempting to connect to SK WebSocket..")
            ws = create_connection(url)
            app.logger.info("aa62 Connected to SignalK WebSocket.")

            while True:  # Inner loop for receiving messages
                eventlet.sleep(1)  # Non-blocking sleep
                try:
                    # Blocking call to receive messages
                    message = ws.recv()
                    app.logger.debug(f"aa69 Received message: {message[:400]}")

                    # Parse JSON data
                    try:
                        data = json.loads(message)
                        app.logger.debug(f"aa74 Parsed data: {data}")
                    except json.JSONDecodeError as e:
                        app.logger.error(f"aa76 JSON parsing error: {e}")
                        continue

                    # Process and filter SignalK updates
                    updates = []
                    for update in data.get("updates", []):
                        for value in update.get("values", []):
                            path = value.get("path")
                            app.logger.debug(f"aa84 path=: {path}")
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
                                'environment.wind.angleTrueGround',
                                'environment.wind.angleTrueWater',
                                'environment.wind.speedTrue',
                            }:
                                updates.append(value)
                    if updates:
                        socketio.emit("update_data", {"updates": updates})
                        app.logger.info(f"aa125 Emitted data: {updates}")

                except WebSocketConnectionClosedException:
                    app.logger.error("aa128 WebSocket connection closed.")
                    break  # Exit inner loop to reconnect
                except Exception as e:
                    app.logger.error(f"aa131 Error in signalk_listener: {e}")
                    break  # Exit inner loop to reconnect
        except Exception as e:
            app.logger.error(f"aa135 Failed connect to SK WebSocket: {e}")

        finally:
            # Ensure the WebSocket is properly closed
            if ws:
                ws.close()
                app.logger.info("aa141 WebSocket connection closed.")

        # Reconnection logic
        app.logger.info("aa144 Reconnecting to SignalK WebSocket in 5 seconds")
        eventlet.sleep(5)  # Delay before attempting reconnection


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8001)