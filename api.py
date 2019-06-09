#!/usr/bin/env python
# coding: utf-8

import re
import json
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

class SMUD_API:

    def __init__(self):
        self.session = None
        self.login_retries = 3
        self.current_url = None

    def login(self, username, password):
        """ login to the smud system """

        #self.session, _, _ = login(config['Auth']['username'], config['Auth']['password'])
        self.session, _, _ = login(username, password)

    def is_alive(self):
        """ determine if auth is still valid """
        return self.session.cookies.get('sid', domain="smud.okta.com") is not None

    def _get(self, url):
        """ helper to make url request """

        if not self.is_alive():
            self.login()

        ret = self.session.get(url)
        # check if session is alive after request
        #  expires when out of use for a while
        if self.is_alive():
            return ret
        else:
            if self.login_retries > 0:
                self.login_retries -= 1
                ret = self._get(url)
                return ret
            else:
                Exception("Too many retries with failure")

    @staticmethod
    def _make_url(resource_type, resource_by, date):
        """ convert request into a url.
            resource_type must be in valid_types,
            resource_by must be in valid_bys
            date is a tuple (year, month, day) """

        url_base = "https://smud.opower.com/ei/app/myEnergyUse/"
        resource_type_dict = {"cost": "rates/", "usage": "usage/"}
        valid_types = ["cost", "usage"]
        valid_bys = ["day", "bill", "year"]

        # validate
        if resource_type not in valid_types:
            raise Exception("Type must be: ", valid_types)

        if resource_by not in valid_bys:
            raise Exception("Resource must be requested by: ", valid_bys)

        try:
            #TODO: validate type, range; >2000, (0,12), (0,31)
            year, month, day = date
        except ValueError as e:
            raise Exception("Date must be a tuple of (y, m, d)")

        # make url
        url = url_base
        url += resource_type_dict.get(resource_type)
        url += f'{resource_by}/'
        if resource_by == "day":
            url += f'{year}/{month}/{day}'
        elif resource_by == "bill":
            url += f'{year}/{month}'
        else:
            url += f'{year}'
        return url

    def get(self, resource_type, resource_by, date):
        """ make a url request """

        # make request, parse and clean
        self.current_url = SMUD_API._make_url(resource_type, resource_by, date)
        resp = self._get(self.current_url)
        if resp.status_code != 200:
            raise Exception("Url (%s) returned status %s" % \
                    (self.current_url, resp.status_code))

        parsed = self.parse_html(resp.text)
        data = self.clean_data(parsed)
        return data

    @staticmethod
    def parse_html(html):
        """ parse html from script tag into python dictionary """

        # find all script elements
        scripts_elems = BeautifulSoup(html).find_all('script')
        script_elem = list(filter(lambda x: x.text.find('window.seriesDTO')!=-1, scripts_elems))

        if len(script_elem) < 1:
            raise Exception("could not find data in page")

        # grab the dictionary portion
        js_data = re.findall(r'window.seriesDTO = (.*});', script_elem[0].text, re.M|re.I|re.DOTALL)[0]
        data = json.loads(js_data)
        return data

    @staticmethod
    def clean_data(data, series_col=0):
        """ given a list, it keeps keys from KEYS_TO_KEEP, and returns a list with the rest removed """

        # for energy rates
        data = data.get('series', [{}])[series_col].get('data')
        KEYS_TO_KEEP = ['startDate', 'endDate', 'value']
        ret_data = []

        # for each datapoint
        for item in data:
            new_item = {}
            # find keys you want to keep
            for key in KEYS_TO_KEEP:
                new_item.update({key: item.get(key, None)})
            ret_data.append(new_item)
        return ret_data

