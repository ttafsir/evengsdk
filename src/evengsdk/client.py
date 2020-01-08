#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from evengsdk.exceptions import EvengLoginError, EvengApiError
from evengsdk.api import EvengApi


DISABLE_INSECURE_WARNINGS = True


class EvengClient:

    def __init__(self, host, logger='eve-client', log_level='INFO', log_file=None):
        self.host = host
        self.port = None
        self.authdata = None
        self.cert = False
        self.cookies = None
        self.url_prefix = ''
        self.api = None
        self.session = {}
        self.timeout = 10
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': '',
        }

        if DISABLE_INSECURE_WARNINGS:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # Log to file is filename is provided
        self.log = logging.getLogger(logger)
        self.set_log_level(log_level)
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
        if log_level not in ['NOTSET', 'DEBUG', 'INFO',
                             'WARNING', 'ERROR', 'CRITICAL']:
            log_level = 'INFO'
        self.log.setLevel(getattr(logging, log_level))

    def login(self, username='', password='', cert=False):
        """
        Initiate login to EVE-NG host

        Args:
            username (str): username to login with
            password (str): password to login with
        """
        self.cert = cert
        self.authdata = {'username': username, 'password': password}

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
        port = self.port or 443
        self.url_prefix = "https://{0}:{1}/api".format(host, port)

        # try HTTPS, and fallback to HTTP
        self.log.debug('Trying connection to: {}'.format(self.url_prefix))
        err = self._check_session()
        if err and port != 80:
            port = 80
            self.log.debug('falling back to port {}'.format(port))
            self.url_prefix = "http://{0}:{1}/api".format(host, port)
            err = self._check_session()

    def _check_session(self):
        """
        Try logging into EVE-NG host. If the login succeeded None will be returned and
        self.session will be valid. If the login failed then an
        exception error will be returned and self.session will
        be set to None.

        Returns:
            error (str): error message or None.

        """
        self.log.debug('Creating session...')
        self.session = requests.Session()

        self.log.debug('logging in...')
        error = None
        try:
            self._login()
            self.log.debug('logged in as: {}'.format(self.authdata.get('username')))
        except Exception as e:
            self.log.warning(str(e))
            self.session = {}
            error = str(e)
        return error

    def _login(self):
        session = self.session
        login_endpoint = "/auth/login"
        url = self.url_prefix + login_endpoint

        r = session.post(url, data=json.dumps(self.authdata))
        cookie = r.json().get('Set-Cookie')
        if cookie:
            session.headers = self.headers
            session.headers['Cookie'] = cookie

    def logout(self):
        logout_endpoint = '/auth/logout'
        if self.session:
            r_obj = self.get(logout_endpoint)
            self.session = {}

    def _is_good_response(self):
        pass

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
        r_obj = self._send_request(method, url, data=data, **kwargs)

        r_data = None
        if r_obj:
            try:
                self.log.debug('retrieving response data'.format(method))
                r_data = r_obj.read()
                return r_data
            except Exception as e:
                self.log.error(str(e))
        return

    def _send_request(self, method, url, data=None, **kwargs):
        resp = None
        self.log.debug('sending {} request'.format(method))
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
            self.log.error('EvengApiError')
            raise EvengApiError('API Resource does not exist or is invalid: {0}\n\t{1}'.format(url, e.read()))

        except Exception as error:
            self.log.error(error)
            raise(error)
