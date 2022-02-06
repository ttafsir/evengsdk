import json
import logging

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from evengsdk.api import EvengApi

from evengsdk.exceptions import EvengHTTPError, EvengLoginError


class EvengClient:
    def __init__(
        self,
        host: str = None,
        protocol: str = "http",
        log_file: str = None,
        log_level: str = "INFO",
        port: int = None,
        disable_insecure_warnings: bool = False,
        ssl_verify: bool = True,
    ):
        self.host = host
        self.protocol = protocol
        self.session = None
        self.log_level = log_level
        self.log_file = log_file
        self.html5 = -1
        self.api = None
        self.port = port
        self.ssl_verify = ssl_verify
        self.user = None

        # Create Logger and set Set log level
        self.log = logging.getLogger("eveng-client")
        self.set_log_level(log_level)
        if log_file:
            self.log.addHandler(logging.FileHandler(log_file))
        else:
            self.log.addHandler(logging.NullHandler())

        # Disable insecure warnings
        if disable_insecure_warnings:
            self.disable_insecure_warnings()

    def disable_insecure_warnings(self):
        # disable insecure warnings
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    @property
    def url_prefix(self):
        """Return full url prefix for EVE-NG API."""
        if self.port:
            return f"{self.protocol}://{self.host}:{self.port}/api"
        return f"{self.protocol}://{self.host}/api"

    def set_log_level(self, log_level: str) -> None:
        """Set log level for logger. Defaults to INFO if no level passed in or
        if an invalid level is passed in.

        :param log_level: Log level to use for logger, defaults to 'INFO'
        :type log_level: str, optional
        """
        LOG_LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if log_level.upper() not in LOG_LEVELS:
            log_level = "INFO"
        self.log.setLevel(getattr(logging, log_level))

    def login(self, username: str, password: str, *args, **kwargs) -> None:
        """Initiate login to EVE-NG host. Accepts args and kwargs for
        request.Session object, except "data" key.

        :param username: EVE-NG login username, defaults to ''
        :type username: str, optional
        :param password: EVE-NG login password, defaults to ''
        :type password: str, optional
        :raises EvengLoginError: raises for unsuccessful logins
        """
        login_endpoint = self.url_prefix + "/auth/login"
        authdata = {"username": username, "password": password, "html5": self.html5}

        self.log.debug("creating session")
        if not self.session:
            self.session = requests.Session()
            self.session.verify = self.ssl_verify

        # set default session header
        self.session.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        _ = kwargs.pop("data", None)  # avoids duplicate `data` key for Session
        r = self.session.post(
            login_endpoint, data=json.dumps(authdata), *args, **kwargs
        )
        if r.ok:
            try:
                "logged in" in r.json()
                self.username = username
                self.api = EvengApi(self)  # create API wrapper object
            except json.decoder.JSONDecodeError:
                self.log.error("Error logging in: {}".format(r.text))
                raise EvengLoginError("Error logging in: {}".format(r.text))
        else:
            self.session = {}
            raise EvengLoginError("Error logging in: {}".format(r.text))

    def logout(self):
        try:
            self.session.get(self.url_prefix + "/auth/logout")
        finally:
            self.session = None

    def _make_request(
        self, method: str, url: str, use_prefix: bool = True, *args, **kwargs
    ) -> dict:
        """Craft request to EVE-NG API

        :param method: request method
        :type method: str
        :param url: full url or endpoint for request
        :type url: str
        :raises ValueError: if no session exists
        :raises ValueError: if response object does not contain valid JSON data
        :return: Response dictionary from EVE-NG API
        :rtype: dict
        """
        if not self.session:
            raise ValueError("No valid session exist")

        if use_prefix and self.url_prefix not in url:
            url = self.url_prefix + url

        req = requests.Request(method, url, *args, **kwargs)
        prepped_req = self.session.prepare_request(req)

        r = self.session.send(prepped_req)
        if r.ok:
            try:
                return r.json()
            except json.JSONDecodeError:
                return r
        self.log.error("Error: {}".format(r.text))

        # EVE-NG API returns HTTP error code and message in JSON response
        if hasattr(r, "json"):
            try:
                err_code = r.json().get("code")
            except json.JSONDecodeError:
                err_code = r.text
            try:
                err_msg = r.json().get("message")
            except json.JSONDecodeError:
                err_msg = r.text
            raise EvengHTTPError("Error: {} {}".format(err_code, err_msg))

        # Other HTTP errors for which we don't have a JSON response
        r.raise_for_status()

    def post(self, url: str, *args, **kwargs):
        return self._make_request("POST", url, *args, **kwargs)

    def get(self, url: str, *args, **kwargs):
        return self._make_request("GET", url, *args, **kwargs)

    def put(self, url: str, *args, **kwargs):
        return self._make_request("PUT", url, *args, **kwargs)

    def patch(self, url: str, *args, **kwargs):
        return self._make_request("PATCH", url, *args, **kwargs)

    def delete(self, url: str, *args, **kwargs):
        return self._make_request("DELETE", url, *args, **kwargs)
