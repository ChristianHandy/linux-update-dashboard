from flask import Flask, render_template, redirect, session, request
import json, threading, paramiko
from updater import run_update
import scheduler

app = Flask(__name__, template_folder="templates")
app.secret_key = "change_me"

USERNAME = "admin"
PASSWORD = "password"

logs = {}

def is_online(host, user):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, timeout=3)
        ssh.close()
        return True
    except:
        return False

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pass"] == PASSWORD:
            session["login"] = True
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("login"):
        return redirect("/")
    hosts = json.load(open("hosts.json"))
    history = json.load(open("history.json"))
    status = {n: is_online(h["host"], h["user"]) for n, h in hosts.items()}
    return render_template("dashboard.html", hosts=hosts, status=status, history=history)

@app.route("/update/<name>")
def update(name):
    hosts = json.load(open("hosts.json"))
    logs[name] = []
    threading.Thread(
        target=run_update,
        args=(hosts[name]["host"], hosts[name]["user"], name, logs[name])
    ).start()
    return redirect(f"/progress/{name}")

@app.route("/progress/<name>")
def progress(name):
    return render_template("progress.html", log=logs.get(name, []))

app.run(host="0.0.0.0", port=5000)

