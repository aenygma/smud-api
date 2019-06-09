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

session, _, _ = login(config['Auth']['username'], config['Auth']['password'])

# XXX HACK. prevent exporting of Auth class consumer
#del config['Auth']

class SMUD_API:

    def __init__(self):
        self.session = None
        self.alive = False
        self.login_retries = 3

    def login(self, username, password):
        """ login to the smud system """

        #self.session, _, _ = login(config['Auth']['username'], config['Auth']['password'])
        self.session, _, _ = login(username, password)

    def is_alive(session):
        """ determine if auth is still valid """
        return session.cookies.get('sid', domain="smud.okta.com") is not None

    def get(self, url):
        """ make a url request """

        if not self.alive:
            self.login()

        ret = self.session.get(url)
        # check if session is alive after request
        #  expires when out of use for a while
        if self.is_alive():
            return ret
        else:
            if self.login_retries > 0:
                self.login_retries -= 1
                ret = self.get(url)
                return ret
            else:
                Exception("Too many retries with failure")

    def parse_html(html):
        """ parse html from script tag into python dictionary """

        # find all script elements
        scripts_elems = BeautifulSoup(html).find_all('script')
        script_elem = list(filter(lambda x: x.text.find('window.seriesDTO')!=-1, scripts_elems))

        assert len(script_elem) > 0, "could not find data in page"

        # grab the dictionary portion
        js_data = re.findall(r'window.seriesDTO = (.*});', script_elem[0].text, re.M|re.I|re.DOTALL)[0]
        data = json.loads(js_data)
        return data



# -----
#g=list(filter(lambda x: x.text.find('window.seriesDTO')!=-1, BeautifulSoup(d[1].content).find_all('script')))

#i=re.findall(r'window.seriesDTO = (.*});', g[0].text, re.M|re.I|re.DOTALL)[0]
#j = json.loads(i)
#j.get('series')[0].get('data')


