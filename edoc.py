#!/usr/bin/env python3.4

import logging
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import time

HOST = "coding42.diphda.uberspace.de"
PORT = 62155

PROJECTNAME = "edoc"
DBNAME = PROJECTNAME+".sqlite"
LOGNAME = PROJECTNAME+".log"

app = Flask(__name__)
app.config["SECRET_KEY"] = "BlaBlub42"
socketio = SocketIO(app)
app.config.update(PROPAGATE_EXCEPTIONS=True)

logger = logging.getLogger(PROJECTNAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOGNAME)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

def initDB():
	connection = sqlite3.connect(DBNAME, check_same_thread = False)
	cursor = connection.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS rooms(id INTEGER, name TEXT, users INTEGER, PRIMARY KEY(id))")
	try:
		cursor.execute("INSERT INTO rooms (id, name, users) VALUES (0, '', 0)")
	except sqlite3.IntegrityError:
		pass
	connection.commit()
	connection.close()

def joinRoom(room):
	connection = sqlite3.connect(DBNAME, check_same_thread = False)
	cursor = connection.cursor()
	cursor.execute("UPDATE rooms SET users=users+1 WHERE id=?", (room,))
	connection.commit()
	connection.close()
	join_room(room)
	session["room"] = room

def leaveRoom(room):
	connection = sqlite3.connect(DBNAME, check_same_thread = False)
	cursor = connection.cursor()
	cursor.execute("UPDATE rooms SET users=users-1 WHERE id=?", (room,))#TODO delete room if emty
	connection.commit()
	connection.close()
	leave_room(room)
	session["room"] = -1

@app.route("/", methods=["GET", "POST"])
def root():
	return render_template("base.html")

@app.route("/impressum", methods=["GET", "POST"])
def impressum():
	return render_template("impressum.html")

@socketio.on("sendMessage")
def sendMessage(json):
	logger.info(json)
	room = session["room"]
	millis = int(round(time.time() * 1000))
	json["time"] = millis
	emit("receiveMessage", json, room=room)

@socketio.on("sendMetaMessage")
def handleSendMetaMessage(json):
	logger.info(json)
	emit("receiveMetaMessage", json, room=0)

@socketio.on("connect")
def handleConnect():
	joinRoom(0)
	emit("receiveMetaMessage", {"connected":True}, room=0)
	emit("createRooms", {"rooms":[0]}, room=0)

@socketio.on("disconnect")
def handleDisconnect():
	room = session["room"]
	leaveRoom(room)
	emit("receiveMetaMessage", {"disconnected":True}, room=0)

@socketio.on_error_default
def error_handler(e):
	logger.info(e)

if __name__ == "__main__":
	initDB()
	socketio.run(app, host=HOST, port=PORT, debug=False)
