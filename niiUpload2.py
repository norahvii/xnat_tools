import argparse
from collections import Counter
import pycurl
from io import BytesIO
import getpass, requests, urllib3
import re, os, shutil, gzip, json
import datetime, subprocess
import pandas as pd

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class XNATClient:
    def __init__(self, site, username, password):
        self.site = site
        self.username = username
        self.password = password
        self.session = self.start_session()
        self.jsession_token = self.get_jsession_token()

    def start_session(self):
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.verify = False
        return session

    def get_jsession_token(self):
        try:
            response = self.session.get(f"{self.site}/data/JSESSION")
            response.raise_for_status()
            return re.search(r'[A-Za-z0-9]{32}', response.text).group(0)
        except HTTPError as e:
            logging.error(f"Failed to get JSESSION token: {e}")
            raise

    def upload_file(self, url, filepath):
        try:
            with open(filepath, 'rb') as file:
                response = self.session.put(url, data=file)
            response.raise_for_status()
            logging.info(f"Uploaded file to {url}")
        except HTTPError as e:
            logging.error(f"Failed to upload file {filepath}: {e}")
            raise

    def create_or_update_resource(self, url, data=None):
        try:
            response = self.session.put(url, data=data)
            response.raise_for_status()
            logging.info(f"Resource at {url} created/updated")
        except HTTPError as e:
            logging.error(f"Failed to create/update resource {url}: {e}")
            raise

class TimingFileGenerator:
    def __init__(self, time_frame, time_duration, time_elapsed, output_dir, base_filename):
        self.time_frame = time_frame
        self.time_duration = time_duration
        self.time_elapsed = time_elapsed
        self.output_dir = output_dir
        self.base_filename = base_filename

    def generate(self):
        timing_data = list(zip(self.time_frame, self.time_duration, self.time_elapsed))
        timing_df = pd.DataFrame(timing_data, columns=["Time frame", "Duration of time frame (min)", "Elapsed time (min)"])
        timing_file_name = self.base_filename + '.csv'
        timing_file_path = os.path.join(self.output_dir, timing_file_name)
        timing_df.to_csv(timing_file_path, index=False)
        logging.info(f"Timing file generated: {timing_file_path}")
        return timing_file_path

class FileProcessor:
    def __init__(self, xnat_client, project_id, subject_group):
        self.xnat_client = xnat_client
        self.project_id = project_id
        self.subject_group = subject_group
        self.adrc_demographics = pd.read_csv('./demographic_data/all_adrc_demographics.csv', dtype={'subject': str})
        self.wrap_demographics = pd.read_csv('./demographic_data/all_wrap_demographics.csv', dtype={'subject': str})

    def process_file(self, csv_row):
        id_string = csv_row['id_string']
        full_path = csv_row['full_path']

        if full_path.lower().endswith('.json'):
            try:
                with open(full_path, 'r') as f:
                    json_content = json.load(f)

                content = self.extract_content_from_json(json_content, id_string)
                subject_label = self.get_subject_label(id_string)
                session_label = self.get_session_label(content, id_string)
                scan_id = content['scan_id']

                self.create_or_update_subject(subject_label, id_string)
                self.create_or_update_session(subject_label, session_label, content)
                self.create_or_update_scan(subject_label, session_label, scan_id, content)

                json_file_path = full_path
                nii_file_path = full_path.replace('.json', '.nii.gz')
                timing_file_path = None

                if os.path.exists(nii_file_path):
                    time_frame = [str(i + 1) for i in range(len(json_content.get('FrameDuration', '')))]
                    timing_generator = TimingFileGenerator(time_frame, json_content.get('FrameDuration', ''), json_content.get('FrameTimesEnd', ''), os.path.dirname(nii_file_path), os.path.basename(nii_file_path).split('.')[0])
                    timing_file_path = timing_generator.generate()

                self.upload_files(subject_label, session_label, scan_id, json_file_path, nii_file_path, timing_file_path)
            except Exception as e:
                logging.error(f"Error processing file {full_path}: {e}")

    def extract_content_from_json(self, json_content, id_string):
        parts = id_string.split('_')
        prefix = parts[0] + '_s'
        subject_number = parts[1][1:] if parts[1].startswith('s') else parts[1]
        session_number = parts[2][1:] if parts[2].startswith('v') else parts[2]
        return {
            'scanner_manufacturer': json_content.get('Manufacturer', 'NA').replace(' ', '%20'),
            'scanner_model': json_content.get('ManufacturersModelName') or json_content.get('ManufacturerModelName', 'NA').replace(' ', '%20'),
            'series_description': json_content.get('SeriesDescription', 'NA').replace(' ', '%20'),
            'acquisition_site': json_content.get('InstitutionName', 'NA').replace(' ', '%20'),
            'session_date': json_content.get('StudyDate', ''),
            'modality': json_content.get('Modality', ''),
            'scan_id': json_content.get('SeriesNumber', 1),
            'field_strength': json_content.get('MagneticFieldStrength', 3),
            'tracer': json_content.get('TracerName', 'NA').replace(' ', '%20').lower(),
            'attenuation_correction': json_content.get('AttenuationCorrection', 'NA').replace(',', '').replace(' ', '%20'),
            'xsi_type': 'xnat:petSessionData' if json_content.get('Modality', '') == 'pet' else 'xnat:mrSessionData',
            'scan_type': 'xnat:petScanData' if json_content.get('Modality', '') == 'pet' else 'xnat:mrScanData'
        }

    def get_subject_label(self, id_string):
        return f'{id_string.split("_")[0]}{id_string.split("_")[1][1:]}'

    def get_session_label(self, content, id_string):
        return f"{content['prefix']}{id_string.split('_')[1][1:]}_{id_string.split('_')[2][1:]}"

    def create_or_update_subject(self, subject_label, id_string):
        url = f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}?format=json"
        response = self.xnat_client.session.get(url)
        if response.status_code != 200:
            subject_create_url = f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}?src={self.subject_group}&group={self.subject_group}"
            self.xnat_client.create_or_update_resource(subject_create_url)
            demographics = self.wrap_demographics if content['prefix'] == 'wiscwrap_s' else self.adrc_demographics
            demo = demographics[demographics['subject'] == id_string.split('_')[1][1:]].iloc[0]
            demo_data = {
                'gender': demo['gender'],
                'race': demo['race'],
                'ethnicity': demo['ethnicity']
            }
            self.xnat_client.create_or_update_resource(f"{self.xnat_client.site}/data/archive/projects/{self.project_id}/subjects/{subject_label}", data=demo_data)

    def create_or_update_session(self, subject_label, session_label, content):
        url = f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}"
        response = self.xnat_client.session.get(url)
        if response.status_code != 200:
            session_data = {
                'xsiType': content['xsi_type'],
                'date': content['session_date'],
                'fieldStrength': content['field_strength'],
                'modality': content['modality'],
                'scanner/manufacturer': content['scanner_manufacturer'],
                'scanner/model': content['scanner_model'],
                'acquisition_site': self.subject_group,
                'age': f"{int(id_string.split('_')[2][1:][:3])}.{id_string.split('_')[2][1:][-2:]}"
            }
            self.xnat_client.create_or_update_resource(f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}", data=session_data)

    def create_or_update_scan(self, subject_label, session_label, scan_id, content):
        url = f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}"
        response = self.xnat_client.session.get(url)
        if response.status_code != 200:
            scan_data = {
                'xsiType': content['scan_type'],
                'scanner/model': content['scanner_model'],
                'scanner/manufacturer': content['scanner_manufacturer'],
                'modality': content['modality'],
                'tracer': content['tracer'],
                'attenuationCorrection': content['attenuation_correction']
            }
            self.xnat_client.create_or_update_resource(f"{self.xnat_client.site}/data/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}", data=scan_data)

    def upload_files(self, subject_label, session_label, scan_id, json_file_path, nii_file_path, timing_file_path):
        if timing_file_path:
            self.xnat_client.upload_file(f"{self.xnat_client.site}/data/archive/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}/resources/timing/file", timing_file_path)
        self.xnat_client.upload_file(f"{self.xnat_client.site}/data/archive/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}/resources/nii/file", nii_file_path)
        self.xnat_client.upload_file(f"{self.xnat_client.site}/data/archive/projects/{self.project_id}/subjects/{subject_label}/experiments/{session_label}/scans/{scan_id}/resources/json/file", json_file_path)

def main(username, csv_path):
    site = "https://fornix.wustl.edu"
    password = getpass.getpass("XNAT password: ")
    xnat_client = XNATClient(site, username, password)
    file_processor = FileProcessor(xnat_client, project_id="PROJECT_ID", subject_group="SUBJECT_GROUP")

    try:
        df = pd.read_csv(csv_path)
        for _, csv_row in df.iterrows():
            file_processor.process_file(csv_row)
    except Exception as e:
        logging.error(f"Error in processing CSV file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload BIDS files to XNAT")
    parser.add_argument("username", help="XNAT username")
    parser.add_argument("csv_path", help="Path to the CSV file containing file paths and IDs")
    args = parser.parse_args()
    main(args.username, args.csv_path)
