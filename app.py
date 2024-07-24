[Unit]
Description=My Python App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/.signalk/node_modules/@signalk/signalk-autopilot/app.py
WorkingDirectory=/home/pi/.signalk/node_modules/@signalk/signalk-autopilot
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
