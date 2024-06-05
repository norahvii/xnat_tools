import argparse
from collections import Counter
import pycurl
from io import BytesIO
import getpass, requests, urllib3
import re, os, shutil, gzip, json
import datetime, subprocess
import pandas as pd



# Function to get the password from the user
def get_password(site):
    return getpass.getpass(f"Enter password for ({site}): ")


# Function to start the session and store cookies
def start_session(site, username, password):
    cookie_jar = f".cookies-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with BytesIO() as buffer:
        curl = pycurl.Curl()
        curl.setopt(curl.URL, f"{site}/data/JSESSION")
        curl.setopt(curl.USERPWD, f"{username}:{password}")
        curl.setopt(curl.COOKIEJAR, cookie_jar)
        curl.setopt(curl.SSL_VERIFYPEER, 0)
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        curl.setopt(curl.WRITEDATA, buffer)
        curl.perform()
        curl.close()
    return cookie_jar


# Function to get the JSESSION ID token
def get_jsession_token(site, username, password):
    with BytesIO() as buffer:
        curl = pycurl.Curl()
        curl.setopt(curl.URL, f"{site}/data/JSESSION")
        curl.setopt(curl.USERPWD, f"{username}:{password}")
        curl.setopt(curl.SSL_VERIFYPEER, 0)
        curl.setopt(curl.SSL_VERIFYHOST, 0)    
        curl.setopt(curl.WRITEDATA, buffer)
        curl.perform()
        curl.close()
        response = buffer.getvalue().decode('utf-8')
    return re.search(r'[A-Za-z0-9]{32}', response).group(0)


# Function for adding to the site
def curl_request(url, cookie_jar, method='GET', file_path=None):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.COOKIEFILE, cookie_jar)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    if method == 'PUT':
        c.setopt(c.CUSTOMREQUEST, 'PUT')
        if file_path:
            c.setopt(c.SSL_VERIFYPEER, 0)
            c.setopt(c.SSL_VERIFYHOST, 0)
            c.setopt(c.UPLOAD, 1)
            c.setopt(c.READDATA, open(file_path, 'rb'))
    c.perform()
    c.close()
    return buffer.getvalue()


# Function to upload a file based on the file path and url
def put_file(url, filepath, cookie_jar):
    try:
        result = subprocess.run(
            ['curl', '-H', 'Expect:', '--keepalive-time', '2', '-X', 'PUT', '-k',
             '--cookie', cookie_jar, '--data-binary', f'@{filepath}', url],
            capture_output=True,
            text=True,
            check=True
        )
        print("Response:", result.stdout)
        print("Error:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.returncode}")
        print(e.output)
        print(e.stderr)


def put_nii(url, filepath, cookie_jar):
    try:
        result = subprocess.run(
            ['curl', '-H', 'Expect:', '-H', 'Content-Type: application/octet-stream',
             '--keepalive-time', '2', '-T', filepath, '-k',
             '--cookie', cookie_jar, url],
            capture_output=True,
            text=True,
            check=True
        )
        print("Response:", result.stdout)
        print("Error:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.returncode}")
        print("Output:", e.output)
        print("Error Details:", e.stderr)


# Function to create the timing file for pet 
def generate_timing_file(time_frame, time_duration, time_elapsed, nii_dir_name, nii_file_path):
    """Generates a timing file CSV based on JSON content."""
    timing_data = list(zip(time_frame, time_duration, time_elapsed))
    timing_df = pd.DataFrame(timing_data, columns=["Time frame", "Duration of time frame (min)", "Elapsed time (min)"])
    timing_file_name = os.path.basename(nii_file_path).split('.')[0] + '.csv'
    timing_file_path = os.path.join(nii_dir_name, timing_file_name)
    timing_df.to_csv(timing_file_path, index=False)
    print(f"Timing file generated: {timing_file_path}")
    return timing_file_path

#############################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CSV and JSON files to generate necessary outputs.")
    parser.add_argument('username', type=str, help='Username for the site')
    parser.add_argument('csv_path', type=str, help='Path to the input CSV file')
    args = parser.parse_args()

    # Load some data for curl authentication
    username = args.username
    site = 'https://fornix.wustl.edu'
    project = 'NORAH_TEST'
    project_id = project
    password = get_password(site)
    cookie_jar = start_session(site, username, password)
    jsession_token = get_jsession_token(site, username, password)
    subject_group = 'Wisconsin'

    # Create a requests session and authenticate
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False  # Disable SSL verification (not recommended for production)

    # Get the input CSV
    df = pd.read_csv(args.csv_path)
    adrc_demographics = pd.read_csv('./demographic_data/all_adrc_demographics.csv')
    wrap_demographics = pd.read_csv('./demographic_data/all_wrap_demographics.csv')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Main loop
    for _, row in df.iterrows():
        id_string = row['id_string']
        full_path = row['full_path']

        if full_path.lower().endswith('.json'):
            try:
                with open(full_path, 'r') as f:
                    json_content = json.load(f)

                # Parse full path content
                parts = id_string.split('_')
                prefix = parts[0] + '_s'
                subject_number = parts[1][1:] if parts[1].startswith('s') else parts[1]
                session_number = parts[2][1:] if parts[2].startswith('v') else parts[2]
                subject_tag = f's{subject_number}'
                session_tag = f'v{session_number}'
                subject_label = f'{prefix}{subject_number}'

                # Retrieve json content
                scanner_manufacturer = json_content.get('Manufacturer', '').replace(' ', '%20') if json_content.get('Manufacturer') is not '' or None else 'NA'
                scanner_model = json_content.get('ManufacturersModelName', '').replace(' ', '%20') if json_content.get('ManufacturersModelName') is not '' or None else 'NA'
                series_description = json_content.get('SeriesDescription', '').replace(' ', '%20') if json_content.get('SeriesDescription') is not '' or None else 'NA'
                acquisition_site = json_content.get('InstitutionName', '').replace(' ', '%20') if json_content.get('InstitutionName') is not '' or None else 'NA'
                session_date = json_content.get('StudyDate', '')
                modality = json_content.get('Modality', '')
                scan_id = json_content.get('SeriesNumber') if json_content.get('SeriesNumber') not in ('', None) else 1
                field_strength = json_content.get('MagneticFieldStrength') if json_content.get('MagneticFieldStrength') not in ('', None) else 3

                if modality != 'pet':
                    xsi_type = 'xnat:mrSessionData'
                    xnat_sess_xsi_type = xsi_type
                    scan_type = 'xnat:mrScanData'
                    xnat_scan_xsi_type = scan_type
                    xnat_MRIsession_label = f'{prefix}{subject_number}_{session_tag}_mr'

                    # add the subject if it doesn't exist
                    if session.get(f'https://fornix.wustl.edu/data/projects/{project_id}/subjects/{subject_label}?format=json').status_code != 200:
                        subject_create_url = f"{site}/data/projects/{project_id}/subjects/{subject_label}?src={subject_group}&group={subject_group}"
                        curl_request(subject_create_url, cookie_jar, method='PUT')

                    # Get demogrpahic data
                    if prefix == 'wiscwrap_s':
                        subject_row = wrap_demographics[wrap_demographics['subject'] == f'{subject_number}']
                    else:
                        subject_row = adrc_demographics[adrc_demographics['subject'] == f'{subject_number}']

                    if not subject_row.empty:
                        gender = subject_row['gender'].values[0]
                        race = subject_row['race'].values[0]
                        ethnicity = subject_row['ethnicity'].values[0]
                        # Add demographics data
                        session.put(f'https://fornix.wustl.edu/data/archive/projects/{project_id}/subjects/{subject_label}?gender={gender}&race={race}&group={subject_group}&src={subject_group}&ethnicity={ethnicity}')

                    else:
                        print(f"Subject {subject_label} already exists")

                    # add the session if it doesn't exist
                    if session.get(f"{site}/data/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}").status_code != 200:
                        session_create_url = f"{site}/data/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}?xsiType={xnat_sess_xsi_type}&date={session_date}&{xnat_sess_xsi_type}/fieldStrength={field_strength}&modality={modality}&{xnat_sess_xsi_type}/scanner/manufacturer={scanner_manufacturer}&{xnat_sess_xsi_type}/scanner/model={scanner_model}&{xnat_sess_xsi_type}/acquisition_site={subject_group}"
                        curl_request(session_create_url, cookie_jar, method='PUT')
                        # add the scan
                        scan_create_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}?xsiType={xnat_scan_xsi_type}&{xnat_scan_xsi_type}/type={series_description}&{xnat_scan_xsi_type}/series_description={series_description}"
                        curl_request(scan_create_url, cookie_jar, method='PUT')
                        # add the resource
                        nii_resource_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/NIFTI?format=NIFTI&content=NIFTI"
                        curl_request(nii_resource_url, cookie_jar, method='PUT')
                        bids_resource_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/BIDS?format=BIDS&content=BIDS"
                        curl_request(bids_resource_url, cookie_jar, method='PUT')
                        # prepare to upload a little
                        json_file_path = full_path
                        json_file_name = os.path.basename(json_file_path)
                        if os.path.exists(json_file_path):
                            json_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/BIDS/files/{json_file_name}?inbody=true"
                            put_file(json_upload_url, json_file_path, cookie_jar)

                        nii_file_name = os.path.basename(full_path).replace('.json', '.nii.gz')
                        nii_file_path = full_path.replace('.json', '.nii.gz')
                        # check if nii file exists
                        if os.path.exists(nii_file_path):
                            # rename file path
                            unzipped_file_name = nii_file_name.replace('.gz', '')
                            unzipped_file_path = nii_file_path.replace('.gz', '')
                            # unzip the file
                            with gzip.open(nii_file_path, 'rb') as f_in:
                                with open(unzipped_file_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                                    if os.path.exists(unzipped_file_path):
                                        scan_nii_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/NIFTI/files/{unzipped_file_name}?inbody=true"
                                        # try uploading with curl
                                        put_nii(scan_nii_upload_url, unzipped_file_path, cookie_jar)
                                        os.remove(unzipped_file_path) # remove the unzipped file after uploading

                        if os.path.exists(nii_file_path.replace('.nii.gz','.bval')):
                            bval_file_name = os.path.basename(nii_file_path.replace('.nii.gz','.bval'))
                            bval_file_path = nii_file_path.replace('.nii.gz','.bval')
                            bval_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/BIDS/files/{bval_file_name}?inbody=true"
                            put_file(bval_upload_url, bval_file_path, cookie_jar)

                        if os.path.exists(nii_file_path.replace('.nii.gz','.bvec')):
                            bvec_file_name = os.path.basename(nii_file_path.replace('.nii.gz','.bvec'))
                            bvec_file_path = nii_file_path.replace('.nii.gz','.bval')
                            bvec_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_MRIsession_label}/scans/{scan_id}/resources/BIDS/files/{bvec_file_name}?inbody=true"
                            put_file(bvec_upload_url, bvec_file_path, cookie_jar)
                               
                    else:
                        print(f"Session {xnat_MRIsession_label} already exists")

                else:
                    xsi_type = 'xnat:petSessionData'
                    xnat_sess_xsi_type = xsi_type
                    scan_type = 'xnat:petScanData'
                    xnat_scan_xsi_type = scan_type
                    tracer = json_content.get('TracerName', '').replace(' ', '%20').lower() if json_content.get('TracerName') is not '' or None else 'NA'
                    attenuation_correction = json_content.get('AttenuationCorrection').replace(',', '').replace(' ', '%20') if json_content.get('AttenuationCorrection') not in ('', None) else 'NA'
                    xnat_PETsession_label = f'{prefix}{subject_number}_{session_tag}_{tracer}'

                    # add the subject if it doesn't exist        
                    if session.get(f'https://fornix.wustl.edu/data/projects/{project_id}/subjects/{subject_label}?format=json').status_code != 200:
                        subject_create_url = f"{site}/data/projects/{project_id}/subjects/{subject_label}?src={subject_group}&group={subject_group}"
                        curl_request(subject_create_url, cookie_jar, method='PUT')

                    # Get demogrpahic data
                    if prefix == 'wiscwrap_s':
                        subject_row = wrap_demographics[wrap_demographics['subject'] == f'{subject_number}']
                    else:
                        subject_row = adrc_demographics[adrc_demographics['subject'] == f'{subject_number}']

                    if not subject_row.empty:
                        gender = subject_row['gender'].values[0]
                        race = subject_row['race'].values[0]
                        ethnicity = subject_row['ethnicity'].values[0]
                        # Add demographics data
                        session.put(f'https://fornix.wustl.edu/data/archive/projects/{project_id}/subjects/{subject_label}?gender={gender}&race={race}&group={subject_group}&src={subject_group}&ethnicity={ethnicity}')

                    else:
                        print(f"Subject {subject_label} already exists")

                    # add the session if it doesn't exist
                    if session.get(f"{site}/data/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}").status_code != 200:
                        session_create_url = f"{site}/data/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}?xsiType={xnat_sess_xsi_type}&date={session_date}&{xnat_sess_xsi_type}/fieldStrength={field_strength}&modality={modality}&{xnat_sess_xsi_type}/scanner/manufacturer={scanner_manufacturer}&{xnat_sess_xsi_type}/scanner/model={scanner_model}&{xnat_sess_xsi_type}/acquisition_site={subject_group}"
                        curl_request(session_create_url, cookie_jar, method='PUT')
                        # add the scan
                        scan_create_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}?xsiType={xnat_scan_xsi_type}&{xnat_scan_xsi_type}/type={modality}&{xnat_scan_xsi_type}/series_description={modality}_{tracer}_{attenuation_correction}"
                        curl_request(scan_create_url, cookie_jar, method='PUT')
                        # add the resource
                        nii_resource_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}/resources/NIFTI?format=NIFTI&content=NIFTI"
                        curl_request(nii_resource_url, cookie_jar, method='PUT')
                        bids_resource_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}/resources/BIDS?format=BIDS&content=BIDS"
                        curl_request(bids_resource_url, cookie_jar, method='PUT')
                        # prepare to upload a little
                        json_file_path = full_path
                        json_file_name = os.path.basename(json_file_path)
                        if os.path.exists(json_file_path):
                            json_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}/resources/BIDS/files/{json_file_name}?inbody=true"
                            put_file(json_upload_url, json_file_path, cookie_jar)

                        nii_file_name = os.path.basename(full_path).replace('.json', '.nii.gz')
                        nii_file_path = full_path.replace('.json', '.nii.gz')
                        # check if nii file exists
                        if os.path.exists(nii_file_path):
                            # rename file path
                            unzipped_file_name = nii_file_name.replace('.gz', '')
                            unzipped_file_path = nii_file_path.replace('.gz', '')
                            # unzip the file
                            with gzip.open(nii_file_path, 'rb') as f_in:
                                with open(unzipped_file_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                                    if os.path.exists(unzipped_file_path):
                                        scan_nii_upload_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}/resources/NIFTI/files/{unzipped_file_name}?inbody=true"
                                        # try uploading with curl
                                        put_nii(scan_nii_upload_url, unzipped_file_path, cookie_jar)
                                        os.remove(unzipped_file_path) # remove the unzipped file after uploading

                            # prepare to upload the timing file
                            nii_dir_name = os.path.dirname(nii_file_path)
                            # make our columns
                            time_frame = [str(i+1) for i in list(range(len(json_content.get('FrameDuration',''))))]
                            time_duration = json_content.get('FrameDuration','')
                            time_elapsed = json_content.get('FrameTimesEnd','')
                            # create our file 
                            timing_file_path = generate_timing_file(time_frame, time_duration, time_elapsed, nii_dir_name, nii_file_path)
                            timing_file_name = os.path.basename(timing_file_path)             
                            timing_file_url = f"{site}/data/archive/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}/scans/{scan_id}/resources/NIFTI/files/{timing_file_name}?inbody=true"
                            # try uploading with curl 
                            put_file(timing_file_url, timing_file_path, cookie_jar)
                            os.remove(timing_file_path) # remove the timing file after uploading

                        # get our injection times
                        scan_start = json_content.get('ScanStart','')
                        injection_start = json_content.get('InjectionStart','')
                        acq = json_content.get('AcquisitionMode', '')
                        trc = json_content.get('TracerName', '')
                        # prepare our string
                        session_update_url = f"{site}/data/projects/{project_id}/subjects/{subject_label}/experiments/{xnat_PETsession_label}?xsiType={xnat_sess_xsi_type}&{xnat_sess_xsi_type}/acquisition_site={acquisition_site}&{xnat_sess_xsi_type}/start_time_scan=1990-01-01%20{scan_start}&{xnat_sess_xsi_type}/start_time_injection=1990-01-01%20{injection_start}&{xnat_sess_xsi_type}/tracer_name={tracer}"
                        session.put(session_update_url)
                    else:
                        print(f"Session {xnat_PETsession_label} already exists")

            except json.JSONDecodeError:
                print(f"Error reading JSON file: {full_path}")

        else:
            print(f"Skipped non-JSON file: {full_path}")
