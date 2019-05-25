import requests

from bs4 import BeautifulSoup


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
        return_value = {"title": get_title_from_html_string(response)}
    if error:
        return_value = {"error": error}

    return return_value

