# signalk-app

The existing signalk-autopilot plugin is running and the web-page below is using functionality (signalk-autopilot.min.js) in that plugin as well as some other functionality in signalk. 

Connect to your Raspberry Pi via SSH Clone this repo: git clone https://github.com/nrjphwe/signalk-app

All files are added copied to:
cp xxx  ~/.signalk/node_modules/@signalk/signalk-autopilot

**Three things:**
1. A new web-page (**index.html**) to make a new GUI to control the autopilot, as well as showing data on the page. 

This WEB-page is running on a web server on the Raspberry Pi to serve this new interface. 

2. To execute the web-page on a web-server
- you could Run:  python3 -m http.server 8000
- Another way is to run it through a lightweight server like Flask (Python).
- To use Flask, Install Flask: pip install flask
- then make an **app.py** that will be runnung

3. To make this a permanent and robust solution for the "app.py", make systemd service to manage the application. 

A new service is created **myapp.service**: 
copy the myappservice code to:
sudo cp myapp.service /etc/systemd/system/myapp.service

sudo systemctl daemon-reload
sudo systemctl enable myapp.service
sudo systemctl start myapp.service

**To access the New GUI:**
Open the web browser on your iPad/Iphone and navigate to the Raspberry Pi's IP address followed by the port number, e.g., http://hostname:8000.
