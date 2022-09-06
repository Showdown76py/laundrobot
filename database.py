import os
import json


class Errors:
	class FileAlreadyExists(Exception):
		pass

	class FileDoesNotExistsOrIsUnavailable(Exception):
		pass

	class ParentFolderDoesNotExists(Exception):
		pass




def create_file(name: str, extension: str="json", overwrite_if_exists: bool=False):
	file = f"{name}.{extension}"
	folder = '/'.join(name.split('/')[:-1]) or None # if folder: folder == "some/path/to/folder" else folder == "", so replace to None


	if file in os.listdir(folder) and not overwrite_if_exists:
		raise Errors.FileAlreadyExists(f"The file {file} already exists.")

	with open(file, 'w', encoding='utf-8') as f:
		f.write('{}' if extension == "json" else '')


	return name

def read_file(name: str, extension: str="json", create_if_unavailable: bool=True):
	file = f"{name}.{extension}"
	folder = '/'.join(name.split('/')[:-1]) or None # if folder: folder == "some/path/to/folder" else folder == "", so replace to None


	if not file in os.listdir(folder):
		if create_if_unavailable is False:
			raise Errors.FileDoesNotExistsOrIsUnavailable(f"The file {file} does not exists.")
		
		else:
			create_file(name, extension)


	with open(file, 'r', encoding='utf-8') as f:
		if extension == "json":
			return json.load(f)

		return f.read()

def write_to_file(name: str, extension: str="json", data=None, create_if_unavailable: bool=True):
	file = f"{name}.{extension}"
	folder = '/'.join(name.split('/')[:-1]) or None # if folder: folder == "some/path/to/folder" else folder == "", so replace to None


	if not file in os.listdir(folder):
		if create_if_unavailable:
			create_file(name, extension)

		else:
			raise Errors.FileDoesNotExistsOrIsUnavailable(f"The file {file} does not exists")


	with open(file, 'w', encoding='utf-8') as f:
		f.write(data)




class Laundromat:
	def __init__(self):
		pass

	def get(self, name: str, raise_error_if_not_found: bool=True):
		data = read_file('database')['connected']

		if data.get(name) is None:
			if raise_error_if_not_found:
				raise UnknownLaundromat(f"The laundromat '{name}' is no where to be found.")

			else:
				return None

		return data[name]



	def get_connected(self, only_links: bool=False):
		data = read_file("database")['connected']
		connected = []

		for laundro in data:
			if only_links:
				connected.append(data[laundro]['link'])
			else:
				connected.append(data[laundro])

		return connected

	def fetch_all(self, format_for_select: bool=False):
		data = read_file("database")['connected']

		if format_for_select:
			fetched = []

			for laundro in data:
				obj = [
					laundro, # resName
					'🏫' if data[laundro]['type'] == "residence" else '👕', #resTypeEmote
					data[laundro]['desc']
				]
				fetched.append(obj)


			return fetched

		return data




laundromat = Laundromat()




