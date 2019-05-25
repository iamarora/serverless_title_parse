import boto3
import requests
import os

from botocore import UNSIGNED
from botocore.client import Config
from bs4 import BeautifulSoup
from tld import get_tld


s3 = boto3.resource('s3')
client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

bucket = os.environ['bucket_name']

def upload_to_s3(html_string, url):
    # Save it to local storage of Lambda, having a limit of 512MB
    url_parts = get_tld(url, as_object=True)
    fname = "{}{}.html".format(url_parts.subdomain, url_parts.fld)
    tmp_file_path = "/tmp/{}".format(fname)
    with open(tmp_file_path, "w") as f:
        f.write(html_string)
    # #Upload file to s3
    s3.Bucket(bucket).upload_file(tmp_file_path, fname,
                                  ExtraArgs={'ACL': 'public-read'})
    # #Generate public url
    s3_url = client.generate_presigned_url('get_object', ExpiresIn=0,
                                           Params={'Bucket': bucket, 'Key': fname})
    return s3_url


def request_get(url):
    response, error = None, None
    try:
        response = requests.get(url).text
    except requests.exceptions.RequestException as e:
        error = str(e)
    return response, error


def get_title_from_html_string(html_string):
    soup = BeautifulSoup(html_string, features="html.parser")
    title = soup.title # # finds the first title element anywhere in the html document
    return title.string


def parse_title(event, context):
    url = event
    response, error = request_get(url)
    if response:
        s3_url = upload_to_s3(response, url)
        title = get_title_from_html_string(response)
        return_value = {"title": title,
                        "s3_url": s3_url}
    if error:
        return_value = {"error": error}

    return return_value

