==========
Quickstart
==========

To use evengsdk client in a project::

    from evengsdk.client import EvengClient
    client = EvengClient('10.246.32.119')

    client.login(username='admin', password='eve')

    # get EVE-NG server status
    client.api.get_server_status()

    # create lab
    lab = {
        'name': 'TestLab',
        'path': '/',
        'description': 'short description',
        'version': '1',
        'body': 'longer description'
    }
    client.api.create_lab(**lab)
