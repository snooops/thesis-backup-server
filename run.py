from json import JSONDecodeError
import requests
import os
import time


class backupserver:

    def __init__(self):
        # setting the url of the source system to backup
        self.base_url = "http://192.168.1.179:5000"
        # setting a directory where to store the backups
        self.backup_storage = "./backup"

    def call_generate_file_list(self, path: str):
        """path: What should be backuped"""
        json_payload = {
            "type": "filelist",
            "path": path
        }

        url = f"{self.base_url}/file/generate_file_list"
        response = requests.post(url=url, json=json_payload)

        try:
            filelist = response.json()
            return filelist
        except JSONDecodeError:
            print('Response could not be serialized')

    def download_filelist(self, filelist: dict):
        """Starts the download of the given filelist, retrieved from call_generate_file_list"""
        # create directory name for current directory
        time_dir = "%.0f" % time.time()
        self.current_backup_dir = f"{self.backup_storage}/{time_dir}"

        # create the directory and all it parent directories if not present
        os.makedirs(self.current_backup_dir)

        # start downloading the files from the filelist
        self.call_download(filelist=filelist)


    def call_download(self, filelist: dict):
        """Recursive function which iterates through filelist to download
        all elements and create the subdirectories."""
        # create directory for current entry
        print (f"Creating directory: {filelist["name"]}")
        os.makedirs(f"{self.current_backup_dir}{filelist["name"]}")
        
        # build url for the api call
        url = f"{self.base_url}/file/download"

        # iterate through the filelist dictonary
        for entry in filelist["items"]:
            # check if the type is a directory
            if entry["type"] == "directory":
                # then check it's items subentries
                self.call_download(entry)
                return

            # if it's not a directory, it's a file, download it
            # build the json data
            json_data = {
                "file": entry["name"],
                "directory": filelist["name"]
            }
            print (f"Iterating: {entry["name"]}")
            # download the file as stream to save ram
            with requests.post(url, stream=True, json=json_data) as r:
                # check if a non ok code is received
                r.raise_for_status()

                # building the path where to download the file to
                save_file_as = f"{self.current_backup_dir}{filelist["name"]}/{entry["name"]}"
                print (f"Downloading: {filelist["name"]}/{entry["name"]}")
                # saving the file
                with open(save_file_as, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)


# instantiate the backupserver
run = backupserver()

# generate the filelist
filelist = run.call_generate_file_list(path="/opt/thesis-test-1")

# TODO: compare against last backup job to download only modified items
# ...

# start the download with the filelist
run.download_filelist(filelist=filelist)