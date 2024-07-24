# signalk-app

I created another web-page (index.html) to make a new GUI to control the autopilot, as well as showing data on the page. 

This WEB-page is running on a web server on the Raspberry Pi to serve this new interface. This is done through a lightweight server like Flask (Python).

To use Flask:

Install Flask: pip install flask

To run the flask app you could run python3 app.py but to make a permanent and robust solution for the "app.py", make systemd service to manage the application. 

sudo nano /etc/systemd/system/myapp.service


sudo systemctl daemon-reload
sudo systemctl enable myapp.service
sudo systemctl start myapp.service
