#! /usr/bin/env python


class EvengClientError(Exception):
    """Eveng Restful API client error"""

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class EvengHTTPError(EvengClientError):
    """Error encountered related to the client making an HTTP call"""

    def __init__(self, msg):
        super().__init__(msg)


class EvengApiError(EvengClientError):
    """Error encountered related to the Eveng API request"""

    def __init__(self, msg):
        super().__init__(msg)


class EvengLoginError(EvengClientError):
    """Error encountered with user credentials at login"""

    def __init__(self, msg):
        super().__init__(msg)
