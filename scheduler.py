from apscheduler.schedulers.background import BackgroundScheduler
from updater import run_update
import json

scheduler = BackgroundScheduler()

def daily_updates():
    hosts = json.load(open("hosts.json"))
    for name, h in hosts.items():
        run_update(h["host"], h["user"], name, [])

scheduler.add_job(daily_updates, "interval", days=1)
scheduler.start()

