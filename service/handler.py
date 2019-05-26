import boto3
import json
import os
import requests
import uuid

from botocore import UNSIGNED
from botocore.client import Config
from bs4 import BeautifulSoup
from tld import get_tld


# #S3 configurations
s3 = boto3.resource('s3')
client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
bucket = os.environ['bucket_name']

# #DynamoDB configurations
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['table_name']

# #Lambda client
lambda_client = boto3.client('lambda')

STATUS_PENDING = 'PENDING'
STATUS_PROCESSED = 'PROCESSED'


##########################################################################################################
##Logging for debugging
##########################################################################################################
import logging
import sys


def setup_logging():
    '''Within your lambda handler.
    logger = setup_logging()
    logger.info('Log')
    '''
    logger = logging.getLogger()
    for h in logger.handlers:
      logger.removeHandler(h)
    h = logging.StreamHandler(sys.stdout)
    FORMAT = '%(asctime)s %(message)s'
    h.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
    return logger

##########################################################################################################
##Helper functions
##########################################################################################################

def upload_to_s3(html_string, url):
    # #Function to create a file from string and save to s3.
    # #Save it to local storage of Lambda, having a limit of 512MB
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


def save_to_dynamo(data):
    table = dynamodb.Table(table_name)
    data.update({'id': str(uuid.uuid1())})
    table.put_item(Item=data)


def update_to_dynamo(key, data):
    table = dynamodb.Table(table_name)
    update_exp  = "SET "
    exp_attr_values = {}
    for k, v in data.items():
        update_exp += "{} = :{},".format(k, k)
        exp_attr_values[":{}".format(k)] = v
    table.update_item(Key=key,
            UpdateExpression=update_exp[:-1],
            ExpressionAttributeValues=exp_attr_values)


def get_from_dynamo(key):
    table = dynamodb.Table(table_name)
    record = table.get_item(Key=key)
    if record.get('Item'):
        return record["Item"]


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
    return str(title.string)


##########################################################################################################
##Registered AWS Lambda funcitons below.
##########################################################################################################
def parse_title(event, context):
    '''
    logger = setup_logging()
    logger.info(event)
    '''
    data = event['Records'][0]
    event_name = data['eventName']
    record = data['dynamodb']
    new_record = record.get('NewImage')
    if event_name == 'INSERT' and new_record:
        url = new_record['url']['S']
        response, error = request_get(url)
        s3_url = None
        if response:
            s3_url = upload_to_s3(response, url)
            title = get_title_from_html_string(response)
        if error:
            title = error
        key = {'id': new_record['id']['S']}
        data = {'s3_url': s3_url, 'title': title}
        data['record_state'] = STATUS_PROCESSED
        update_to_dynamo(key, data)


def async_parse_title(event, context):
    url = event
    return_value = {'url': url, 'record_state': STATUS_PENDING}
    save_to_dynamo(return_value)
    return return_value


def get_processed_title(event, context):
    key = {'id': event}
    return get_from_dynamo(key)

