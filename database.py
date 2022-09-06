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








