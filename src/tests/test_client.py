#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import pytest
import sys

from evengsdk.client import EvengClient
from evengsdk.exceptions import EvengLoginError, EvengApiError


DEVICE_UNDER_TEST = {
    'host': '10.246.49.23',
    'username': 'admin',
    'password': 'eve'
}


@pytest.fixture()
def client():
    host = '1.1.1.1'
    client = EvengClient(host)
    return client


@pytest.fixture()
def dut():
    dut = EvengClient(DEVICE_UNDER_TEST['host'])
    return dut


class TestEvengClient:
    ''' Test cases '''

    def test_clnt_with_logfile(self):
        """
        Verify EvengClient is successfully created with log_file argument
        """
        host = '1.1.1.1'
        client = EvengClient(host, log_file='client.log')
        assert client.log is not None

    def test_clnt_init_log_level(self):
        ''' Initialize client with log level set
        '''
        host = '1.1.1.1'
        clnt = EvengClient(host, log_level='DEBUG')
        assert clnt is not None
        assert clnt.log.getEffectiveLevel() == logging.DEBUG

    def test_set_log_level(self, client):
        """
        Verify changing/setting of log level using client setter method
        """
        client.set_log_level('DEBUG')
        assert client.log.getEffectiveLevel() == logging.DEBUG
        client.set_log_level('INFO')
        assert client.log.getEffectiveLevel() == logging.INFO

    def test_set_log_level_invalid_value(self, client):
        """
        Verify an invalid log level value will default the log level to INFO
        """
        client.set_log_level('FAKE')
        assert client.log.getEffectiveLevel() == logging.INFO

    def test_login(self, dut):
        """
        Verify HTTP login succeeds to Server
        """
        username = DEVICE_UNDER_TEST['username']
        passwd = DEVICE_UNDER_TEST['password']
        dut.login(username=username, password=passwd)
        assert dut.session is not None

    def test_logout(self, dut):
        """
        Verify that HTTP logout succeeds to Server
        """
        username = DEVICE_UNDER_TEST['username']
        passwd = DEVICE_UNDER_TEST['password']
        dut.login(username=username, password=passwd)
        assert dut.session is not None
        dut.logout()
        assert not dut.session

    def test_login_bad_username(self, dut):
        """
        Verify connection attempt with a bad username
        raises an EvengLoginError
        """
        bad_username = 'kadflks'
        passwd = DEVICE_UNDER_TEST['password']
        with pytest.raises(EvengLoginError):
            dut.login(username=bad_username, password=passwd)

    def test_login_bad_password(self, dut):
        """
        Verify connect fails with bad password
        """
        username = DEVICE_UNDER_TEST['username']
        bad_passwd = 'asldflakdjf'
        with pytest.raises(EvengLoginError):
            dut.login(username=username, password=bad_passwd)

    def test_login_bad_host(self):
        """
        Verify connection fails to a wrong server
        """
        bad_host = '1.1.1.1'
        username = DEVICE_UNDER_TEST['username']
        passwd = DEVICE_UNDER_TEST['username']
        client = EvengClient(bad_host)
        with pytest.raises(EvengLoginError):
            client.login(username=username, password=passwd)

    # *********************************
    #   HTTP METHODS
    # *********************************
    def test_get_call(self,  dut):
        """
        Verify GET call from client
        """
        username = DEVICE_UNDER_TEST['username']
        passwd = DEVICE_UNDER_TEST['password']
        dut.login(username=username, password=passwd)
        url = dut.url_prefix + '/status'
        r = dut.session.get(url)
        assert r.code >= 200 <= 299

    @pytest.mark.xfail
    def test_get_call_bad_url(self, dut):
        """
        Verify GET with bad URL returns an error
        """
        pass

    @pytest.mark.xfail
    def test_post_call(self, dut):
        """
        Verify POST call with client
        """
        pass

    def test_post_call_bad_url(self, dut):
        """
        Verify post with bad URL returns an error
        """
        username = DEVICE_UNDER_TEST['username']
        passwd = DEVICE_UNDER_TEST['password']
        dut.login(username=username, password=passwd)
        with pytest.raises(EvengApiError):
            dut.post('/bogus', data=None)

    @pytest.mark.xfail
    def test_put_call(self, dut):
        """
        Verify PUT call with client
        """
        pass

    @pytest.mark.xfail
    def test_put_call_bad_url(self, dut):
        """
        Verify PUT with bad URL returns an error
        """
        pass