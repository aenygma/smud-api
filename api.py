#!/usr/bin/env python
# coding: utf-8

import time
import requests
import configparser
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read("config.ini")

HEADERS = {
    "user-agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"}

def login(username, password):
    """ log into smud site """

    LOGIN_URL = "https://myaccount.smud.org/?Length=0&ack=True"
    DATA_URL = "https://myaccount.smud.org/manage/energyusage"
    session = requests.session()

    # Login to get token
    resp = session.get(LOGIN_URL, headers=HEADERS)
    page = BeautifulSoup(resp.content, 'html5lib')
    token = page.find('input', attrs={'name': "__RequestVerificationToken"}).get('value')

    form_data = {
        "__RequestVerificationToken": token,
        "Lang": "en",
        "UserId": username,
        "Password": password}

    # Login with creds
    resp = session.post(LOGIN_URL, data=form_data, headers=HEADERS)
    if resp.status_code != 200:
        print("Error :", resp.status_code, resp.content)
        raise

    # Go to usage
    resp = session.get(DATA_URL, headers=HEADERS)
    if resp.status_code != 200:
        print("Error :", resp.status_code, resp.content)
        raise

    # parse SSO request
    sso_page = BeautifulSoup(resp.content, 'html5lib')
    sso_form = sso_page.find('form')
    sso_url = sso_form.get('action')
    sso_data = dict([(i.get('name'), i.get('value')) for i in sso_form.find_all('input')])
    time.sleep(2)

    # send SSO request
    resp = session.post(sso_url, data=sso_data, headers=HEADERS)
    if resp.status_code != 200:
        print("Error :", resp.status_code, resp.content)
        raise
    return session, resp, sso_page

def dump(page, filename="dump.html"):
    """ helper to dump a page """

    with open(filename, 'wb') as fh:
        fh.write(page.content)

# XXX HACK. prevent exporting of Auth class consumer
#del config['Auth']

def is_alive(session):
    """ determine if auth is still valid """
    return session.cookies.get('sid', domain="smud.okta.com") is not None

# -----
#g=list(filter(lambda x: x.text.find('window.seriesDTO')!=-1, BeautifulSoup(d[1].content).find_all('script')))

#i=re.findall(r'window.seriesDTO = (.*});', g[0].text, re.M|re.I|re.DOTALL)[0]
#j = json.loads(i)
#j.get('series')[0].get('data')


