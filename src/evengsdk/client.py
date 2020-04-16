#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import requests

from requests.exceptions import HTTPError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from evengsdk.exceptions import EvengLoginError, EvengApiError, EvengClientError
from evengsdk.api import EvengApi


DISABLE_INSECURE_WARNINGS = True

class EvengClient:

    def __init__(self, host, log_level='INFO', log_file=None):
        self.host = host
        self.port = None
        self.authdata = None
        self.verify = False
        self.cookies = None
        self.url_prefix = ''
        self.api = None
        self.session = {}
        self.timeout = 10
        self.html5 = -1
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': '',
        }

        if DISABLE_INSECURE_WARNINGS:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # Create Logger
        self.log = logging.getLogger('eve-client')
        # Set log level
        self.set_log_level(log_level)
        # Log to file is filename is provided
        if log_file:
            self.log.addHandler(logging.FileHandler(log_file))
        else:
            self.log.addHandler(logging.NullHandler())

    def set_log_level(self, log_level='INFO'):
        """
        Set log level for logger. Defaults to INFO if no level passed in or
        if an invalid level is passed in.

        Args:
            log_level (str): Log level to use for logger. Default is INFO.

        """
        log_level = log_level.upper()
        LOG_LEVELS =  ('NOTSET','DEBUG','INFO','WARNING','ERROR','CRITICAL')
        if log_level not in LOG_LEVELS:
            log_level = 'INFO'
        self.log.setLevel(getattr(logging, log_level))

    def login(self, username='', password='', verify=False):
        """
        Initiate login to EVE-NG host. Api object is created
        after successful login.

        Args:
            username (str): username to login with
            password (str): password to login with
        """
        self.verify = verify
        self.authdata = {'username': username, 'password': password, 'html5': self.html5}

        self.log.debug('creating session')
        self._create_session()

        if not self.session:
            msg = 'Please check your login credentials and try again'
            raise EvengLoginError('Could not login to {}: {}'.format(
                self.host, msg))

        self.api = EvengApi(self)

    def _create_session(self):
        """
        Login to EVE-NG host and set session information
        """
        host = self.host
        port = self.port or 80
        protocol = {
            80: 'http',
            443: 'https'
        }
        self.url_prefix = f"{protocol[port]}://{host}:{port}/api"

        self.session = requests.Session()
        url = self.url_prefix + "/auth/login"

        error = ''
        try:
            r = self.session.post(url, data=json.dumps(self.authdata), verify=self.verify)
            r_json = r.json()
            # The response is None for unsuccessful login attempt
            if not r_json.get('status') == 'success':
                error += 'invalid login'
                self.session = {}
            else:
                self.log.debug('logged in as: {}'.format(self.authdata.get('username')))
        except Exception as e:
            self.session = {}
            return

    def logout(self):
        """
        Logout of of EVE-NG host
        """
        logout_endpoint = '/auth/logout'
        if self.session:
            r_obj = self.get(logout_endpoint)
            self.session = {}

    def post(self, url, data=None, **kwargs):
        return self._make_request('POST', url, data=data, **kwargs)

    def get(self, url):
        return self._make_request('GET', url)

    def put(self, url, data=None, **kwargs):
        return self._make_request('PUT', url, data=data, **kwargs)

    def delete(self, url):
        return self._make_request('DELETE', url)

    def _make_request(self, method, url, data=None, **kwargs):
        if not self.session:
            raise ValueError('No valid session exist')

        r_obj = None
        self.log.debug('making {} request'.format(method))
        if self.url_prefix not in url:
            url = self.url_prefix + url

        # craft and send the request
        r = self._send_request(method, url, data=data, verify=self.verify, **kwargs)
        if  r.status_code in range(200, 300):
            self.log.debug('retrieving response data'.format(method))
            r_json = r.json()
            data = r_json.get('data')
            resp = data if data is not None else r_json
            return None, resp
        else:
            # return the errors
            self.log.error(r.text)
            return r.text, None


    def _send_request(self, method, url, data=None, **kwargs):
        # resp = None
        self.log.debug(f'Request: {method} {url}')
        try:
            if method == 'DELETE':
                resp = self.session.delete(url, **kwargs)
            elif method == 'GET':
                resp = self.session.get(url)
            elif method == 'PUT':
                resp = self.session.put(url, data=data, **kwargs)
            elif method == 'POST':
                resp = self.session.post(url, data=data, **kwargs)
            return resp

        except HTTPError as e:
            raise EvengHTTPError('HTTP Error: {0}\n\t{1}'.format(url, str(e)))

        except Exception as e:
            raise e
