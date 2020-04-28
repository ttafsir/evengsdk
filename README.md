# evengsdk

Python SDK and utilities to work with [EVE-NG](https://www.eve-ng.net/) API.

* [evengcli](#evengcli)
* [API Client](#API)

## Requirements

* Python 3.6+

## Installation

1. Clone this repository

```sh
git clone --single-branch --branch develop https://github.com/ttafsir/evengsdk
```

2. Create and activate a Python virtual environment

```sh
cd evengsdk
python3 -m venv venv
source venv/bin/activate
```

3. Install

```sh
python setup.py install
```

## evengcli

```
Usage: evengcli [OPTIONS] COMMAND [ARGS]...

Options:
  --host TEXT      [required]
  --username TEXT  [default: (current user); required]
  --password TEXT  [required]
  --port INTEGER   HTTP port to connect to. Default is 80
  --help           Show this message and exit.

Commands:
  lab     EVE-NG lab commands
  node    EVE-NG lab commands
  system  EVE-NG system commands
```

#

## Authors