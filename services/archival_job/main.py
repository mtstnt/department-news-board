from datetime import datetime
import schedule
import requests
import time

GATEWAY_BASE_URL = "http://gateway:8000"
API_KEY = 'r3QCkcsjmspt1KLvWxPq5kkekPcXQ3GK'

def job():
	try:
		print("Executing archival job", flush=True)
		response = requests.post(GATEWAY_BASE_URL + "/news/archive", json={"key": "r3QCkcsjmspt1KLvWxPq5kkekPcXQ3GK"}, verify=False)
		if response.status_code != 200:
			print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] Error:", response.status_code, "=>", response.json(), flush=True)
		else:
			print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] Successfully executed archival job", flush=True)
	except requests.exceptions.ConnectionError as e:
		time.sleep(5)
		job()

schedule.every().day.at("00:00").do(job)
# schedule.every(30).seconds.do(job)

while True:
	schedule.run_pending()
	time.sleep(3600)
	# time.sleep(1)