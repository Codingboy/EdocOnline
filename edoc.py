#!/usr/bin/env python3.4

import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

HOST = "coding42.diphda.uberspace.de"
PORT = 62155

PROJECTNAME = "edoc"

app = Flask(__name__)
app.config["SECRET_KEY"] = "BlaBlub42"
socketio = SocketIO(app)
app.config.update(PROPAGATE_EXCEPTIONS=True)

logger = logging.getLogger(PROJECTNAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(PROJECTNAME+".log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
    
@app.route("/", methods=["GET", "POST"])
def root():
    return render_template("base.html")
    
@app.route("/impressum", methods=["GET", "POST"])
def impressum():
    return render_template("impressum.html")

@socketio.on("requestBrands")
def sendMessage(json):
    logger.info(json)
    emit("receiveMessage", json, room=None)
    
if __name__ == "__main__":
    socketio.run(app, host=HOST, port=PORT, debug=False)