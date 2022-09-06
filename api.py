import json
import aiohttp
from bs4 import BeautifulSoup

available_parser = ["gad"]

async def GAD_Parser(html: str):
	soup = BeautifulSoup(html, "html.parser")

	machines = soup.find_all("div", class_="v-card")

	_washers = []
	_dryers = []

	for machine in machines:
		title = machine.find('div', class_="h6").text

		if title.startswith("LAVEUSE"):
			_washers.append(machine)
		
		elif title.startswith("SECHOIR"):
			_dryers.append(machine)

	del machines


	washing_machines = []

	for washer in _washers:
		infos = [el.text.strip() for el in washer.find_all("span")]
		if infos[0] == "Occupé":
			w = {
				"state": "Unavailable",
				"available_in": infos[2].split(' ')[-1]
			}

		elif infos[0] == "Disponible":
			w = {
				"state": "Available",
				"available_in": 0
			}

		w['price'] = float(infos[-3].encode('ascii', 'ignore').decode('ascii'))
		w['weight'] = infos[-1]

		washing_machines.append(w)
	

	clothes_dryers = []

	for dryer in _dryers:
		infos = [el.text.strip() for el in dryer.find_all("span")]

		if infos[0] == "Occupé":
			w = {
				"state": "Unavailable",
				"available_in": infos[2].split(' ')[-1]
			}

		elif infos[0] == "Disponible":
			w = {
				"state": "Available",
				"available_in": 0
			}

		w['price'] = float(infos[-3].encode('ascii', 'ignore').decode('ascii'))
		w['duration'] = infos[-1]

		clothes_dryers.append(w)


	machines = {
		"washers": washing_machines,
		"dryers": clothes_dryers
	}
	return machines





async def fetch_and_parse(parser: str, url: str):
	assert parser in available_parser, "Unknown parser used"

	# Fetch
	async with aiohttp.ClientSession() as s:
		async with s.get(url) as r:
			content = await r.text()

	# Parse
	parsed = await GAD_Parser(content)
	return parsed



if __name__ == "__main__":
	import asyncio

	loop = asyncio.get_event_loop()
	loop.run_until_complete(fetch_and_parse('gad', 'https://gad.touchnpay.fr:8080/fr/public/material/u3v4a9bgkrap70tz'))