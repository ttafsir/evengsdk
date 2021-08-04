# -*- coding: utf-8 -*-
import json
import logging

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from evengsdk.api import EvengApi
from evengsdk.exceptions import EvengHTTPError, EvengLoginError

DISABLE_INSECURE_WARNINGS = True


class EvengClient:
    def __init__(
        self, host, log_level="INFO", log_file=None, port=80, verify=False, **kwargs
    ):
        self.host = host
        self.port = port
        self.authdata = None
        self.verify = verify
        self.cookies = None
        self.url_prefix = ""
        self.api = None
        self.session = {}
        self.timeout = 10
        self.html5 = -1
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if DISABLE_INSECURE_WARNINGS:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # Create Logger and set Set log level
        self.log = logging.getLogger("eve-client")
        self.set_log_level(log_level)
        if log_file:
            self.log.addHandler(logging.FileHandler(log_file))
        else:
            self.log.addHandler(logging.NullHandler())

    def set_log_level(self, log_level="INFO"):
        """Set log level for logger. Defaults to INFO if no level passed in or
        if an invalid level is passed in.

        :param log_level: Log level to use for logger, defaults to 'INFO'
        :type log_level: str, optional
        """
        log_level = log_level.upper()
        LOG_LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if log_level not in LOG_LEVELS:
            log_level = "INFO"
        self.log.setLevel(getattr(logging, log_level))

    def login(self, username: str, password: str, verify: bool = False) -> None:
        """Initiate login to EVE-NG host. Api object is created
        after successful login.

        :param username: EVE-NG login username, defaults to ''
        :type username: str, optional
        :param password: EVE-NG login password, defaults to ''
        :type password: str, optional
        :param verify: verify certificates, defaults to False
        :type verify: bool, optional
        :raises EvengLoginError: raises for unsuccessful logins
        """
        self.verify = verify
        self.authdata = {
            "username": username,
            "password": password,
            "html5": self.html5,
        }

        self.log.debug("creating session")
        self._create_session()

        if not self.session:
            msg = "Please check your login credentials and try again"
            raise EvengLoginError("Could not login to {}: {}".format(self.host, msg))

        self.api = EvengApi(self)

    def _create_session(self):
        """
        Login to EVE-NG host and set session information
        """
        host = self.host
        protocol = {80: "http", 443: "https"}
        self.url_prefix = f"{protocol.get(self.port, 'http')}://{host}:{self.port}/api"

        self.session = requests.Session()
        url = self.url_prefix + "/auth/login"

        r = self.session.post(url, data=json.dumps(self.authdata), verify=self.verify)

        errors = ""
        if r.ok:
            try:
                "logged in" in r.json()
                self.log.debug(r.json())
            except json.decoder.JSONDecodeError as ex:
                errors += str(ex)
        else:
            self.session = {}
            errors += r.reason

        if errors:
            raise EvengLoginError("Could Not login @ {url}\n{errors}")

    def logout(self):
        """
        Logout of of EVE-NG host
        """
        if self.session:
            logout_endpoint = "/auth/logout"
            self.get(logout_endpoint)
            self.session = {}

    def post(self, url, **kwargs):
        return self._make_request("POST", url, **kwargs)

    def get(self, url, **kwargs):
        return self._make_request("GET", url, **kwargs)

    def put(self, url, **kwargs):
        return self._make_request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self._make_request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._make_request("DELETE", url, **kwargs)

    def _make_request(self, method, url, **kwargs):
        if not self.session:
            raise ValueError("No valid session exist")

        if self.url_prefix not in url:
            url = self.url_prefix + url

        # craft and send the request
        self.log.debug("making {} - {}".format(method, url))
        r = self._send_request(method, url, verify=self.verify, **kwargs)

        # parse response data
        if r.ok:
            try:
                return r.json()["data"]
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON data")
            except KeyError:
                return r.json()
        else:
            err = f"[{r.status_code}] - {r.reason}, {r.text}"
            raise EvengHTTPError(err)
        r.raise_for_status()

    def _send_request(self, method, url, **kwargs):
        try:
            headers = kwargs.pop("headers")
        except KeyError:
            headers = self.headers

        self.log.debug(headers)
        if method == "DELETE":
            resp = self.session.delete(url, **kwargs)
        elif method == "GET":
            resp = self.session.get(url, **kwargs)
        elif method == "PUT":
            resp = self.session.put(url, **kwargs)
        elif method == "PATCH":
            resp = self.session.patch(url, **kwargs)
        elif method == "POST":
            resp = self.session.post(url, **kwargs)
        return resp
