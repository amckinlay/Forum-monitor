from urllib.parse import urljoin, urlencode
import re
import os
import inspect

from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPBasicAuth

from conf.conf import *

data_folder = "../dat/"

# Vbulletin forums (maybe simply list urlparse objects instead,
# unparse and extact info from parse object, could check/match
# domain to parser, too)

forum_rel = "forumdisplay.php"
thread_rel = "showthread.php"

def main():
	for forum in FORUMS:
		# Scrape forums
		soup = scrape_page(forum)

		# Get threads
		threads = find_threads(soup)

		# Declare save filename (could easily use urlparse object for better name)
		file_path = os.path.split(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))[0] + "/res/" + forum["name"] + ".txt"

		# Filter new threads
		new_threads = filter_new(threads, file_path)

		for new_thread in new_threads:
			# Send notification
			send_notification(new_thread, forum["base_url"])

			# Save id
			save_id(file_path, parse_id(new_thread))

# Scraping and filtering

def scrape_page(forum):
	url = urljoin(forum["base_url"], forum_rel) + "?" + urlencode(forum["forum"])

	return BeautifulSoup(requests.get(url).content)

def find_threads(soup):
	threads = soup.find_all("a", id=re.compile("thread_title"), text=re.compile("670"))
	threads += soup.find_all("a", id=re.compile("thread_title"), text=re.compile("ssd", re.IGNORECASE))
	threads += soup.find_all("a", id=re.compile("thread_title"), text=re.compile("i7", re.IGNORECASE))
	threads += soup.find_all("a", id=re.compile("thread_title"), text=re.compile("i5", re.IGNORECASE))

	return threads

def filter_new(threads, file_path):
	previous_ids = saved_ids(file_path)

	new_threads = [thread for thread in threads if parse_id(thread) not in previous_ids]
	return new_threads

def parse_id(thread):
	return re.findall("\d+", thread['id'])[-1]

# File io

def saved_ids(file_path):
	try:
		file = open(file_path, "r")
		ids = [re.findall("\d+", id_)[0] for id_ in file.readlines()]
		file.close()

		return ids

	except IOError as e:
		return []

def save_id(file_path, id_):
	file = open(file_path, "a")
	file.write(id_ + "\n")
	file.close()

# Notification

def send_notification(thread, base_url):
	# Thread info
	thread_url = urljoin(base_url, thread_rel) + urlencode({"t": parse_id(thread)})
	title = thread.text

	# Messege body
	message = shorten_url(thread_url) + " " + title

	# Request info
	url = "https://api.twilio.com/2010-04-01/Accounts/" + TWILIO_SID + "/SMS/Messages"
	data = {"From": TWILIO_ORIG, "To": TWILIO_DEST, "Body": message}
	auth = HTTPBasicAuth(TWILIO_SID, TWILIO_TOKEN)

	# Request
	requests.post(url=url, auth=auth, data=data)

def shorten_url(long_url):
	vgd_url = "http://v.gd/create.php"
	query = {"url": long_url, "format": "simple"}

	# Extract shortened url from response
	return requests.get(url=vgd_url, params=query).text

if __name__ == "__main__":
	main()
