# -*- coding: utf-8 -*-
import os
import logging

import pytest

from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengLoginError, EvengHTTPError


@pytest.fixture()
def local_client_host():
    return "1.1.1.1"


class TestEvengClient:
    """Test cases"""

    def test_create_client_with_logfile(self, local_client_host):
        """
        Verify EvengClient is successfully created with log_file argument
        """
        client = EvengClient(local_client_host, log_file="client.log")
        assert client.log is not None

    def test_create_client_init_log_level(self):
        """Initialize client with log level set"""
        client = EvengClient(local_client_host, log_level="DEBUG")
        assert client is not None
        assert client.log.getEffectiveLevel() == logging.DEBUG

    def test_set_client_log_level(self, client):
        """
        Verify changing/setting of log level using client setter method
        """
        client.set_log_level("DEBUG")
        assert client.log.getEffectiveLevel() == logging.DEBUG
        client.set_log_level("INFO")
        assert client.log.getEffectiveLevel() == logging.INFO

    def test_set_client_log_level_invalid_value(self, client):
        """
        Verify an invalid log level value will default the log level to INFO
        """
        client.set_log_level("FAKE")
        assert client.log.getEffectiveLevel() == logging.INFO

    def test_client_login_bad_username(self, client):
        """
        Verify connection attempt with a bad username
        raises an EvengLoginError
        """
        with pytest.raises(EvengLoginError):
            bad_username = "kadflks"
            passwd = os.environ["EVE_NG_PASSWORD"]
            client.login(username=bad_username, password=passwd)

    def test_client_login_bad_password(self, client):
        """
        Verify connect fails with bad password
        """
        with pytest.raises(EvengLoginError):
            username = os.environ["EVE_NG_USERNAME"]
            bad_passwd = "asldflakdjf"
            client.login(username=username, password=bad_passwd)

    def test_client_login_bad_host(self, local_client_host):
        """
        Verify connection fails to a wrong server
        """
        client = EvengClient(local_client_host)
        with pytest.raises(EvengLoginError):
            username = os.environ["EVE_NG_USERNAME"]
            passwd = os.environ["EVE_NG_PASSWORD"]
            client.login(username=username, password=passwd)

    # *********************************
    #   HTTP METHODS
    # *********************************
    def test_client_get_status_full_url(self, authenticated_client):
        """
        Verify GET call from client
        """
        url = (
            f"{authenticated_client.protocol}://{authenticated_client.host}/api/status"
        )
        r = authenticated_client.get(url)
        assert r["data"]

    def test_client_get_status_endpoint(self, authenticated_client):
        """
        Verify GET call from client
        """
        r = authenticated_client.get("/status")
        assert r["data"]

    def test_client_get_bad_endpoint(self, authenticated_client):
        """
        Verify GET with bad endpoint returns an error
        """
        endpoint = "/bad_endpoint"
        with pytest.raises(EvengHTTPError):
            authenticated_client.get(endpoint)

    def test_client_post_bad_endpoint(self, authenticated_client):
        """
        Verify post with bad URL returns an error
        """
        endpoint = "/bad_endpoint"
        with pytest.raises(EvengHTTPError):
            authenticated_client.post(endpoint, data=None)
