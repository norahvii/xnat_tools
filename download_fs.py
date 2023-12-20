import getpass, requests
import os, re, shutil, zipfile
from bs4 import BeautifulSoup
from tqdm import tqdm

# Login and download FreeSurfers based on a list of fs_ids

def login():
    # Set the URL of the webpage
    token_url = 'https://dca.wustl.edu/data/services/tokens/issue'
    # Get password, response, and soup object
    password = getpass.getpass("Enter XNAT password: ")
    response = requests.get(token_url, auth=('nvii', password))
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    # Get the "alias" and "secret" values
    regex_alias = r'"alias":"([^"]+)"'; regex_secret = r'"secret":"([^"]+)"'
    match_alias = re.search(regex_alias, str(soup)); match_secret = re.search(regex_secret, str(soup))
    alias = match_alias.group(1); secret = match_secret.group(1)
    # Wipe the password from memory
    password = None; del password
    return alias, secret

alias, secret = login() # Logina nd extract alias and secret
fs_id_list = [row.strip() for row in open('fs_ids.csv')]

def parse_fs(alias, secret, row):
    fs_id = row
    sess_id = re.match(r'(.+)_freesurfer', fs_id).group(1) or "Regex pattern did not match."
    outdir = os.getcwd()

    # Use requests to download the file with user and alias tokens
    file_url = f"https://dca.wustl.edu/data/experiments/{sess_id}/assessors/{fs_id}/resources/DATA/files?format=zip"
    file_response = requests.get(file_url, auth=(alias, secret))

    if file_response.status_code == 200:
        # Save the ZIP file
        with open(fs_id + '.zip', 'wb') as file:
            file.write(file_response.content)
        print(f"{fs_id} Downloaded")
        # Extract only the necessary files from the ZIP file
        with zipfile.ZipFile(fs_id + '.zip', 'r') as zip_ref:
            zip_ref.extractall(path=outdir)
            print("Extracted Folder")
        # Relocate files to present directory
        os.system(f"mv -r {fs_id}/out/resources/DATA/files/*/ .")
        all_subdirs = [d for d in os.listdir('.') if os.path.isdir(d)]
        latest_subdir = max(all_subdirs, key=os.path.getmtime)
        print(f"Extracted FreeSurfer {latest_subdir}")
        # Remove extra folders
        os.system(f"rm -rf {fs_id}"); os.system(f"rm -rf {fs_id}.zip")
        print("Cleaned Leftovers")
    else:
        print(f"Failed to download the ZIP file. Status code: {file_response.status_code}")

# Call the parse_fs function with alias, secret, and the list of fs_ids
for line in tqdm(fs_id_list):
    parse_fs(alias, secret, line)
