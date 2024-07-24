# signalk-app
App or web-page to use another GUI to control autopilot, as well as showing data on the page. 

It consists of:
- one web-page: index.html 
- and "app.py" that executes a python web-server for the web-page.

To make a permanent and robust solution for the "app.py", make systemd service to manage the application. 

sudo nano /etc/systemd/system/myapp.service

sudo systemctl daemon-reload
sudo systemctl enable myapp.service
sudo systemctl start myapp.service
