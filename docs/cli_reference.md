# CLI Reference

This page provides documentation for our command line tools.

## :gear: Configuration

It is simple enough to pass the proper flags to `eve-ng` specify details for your EVE-NG host. However, you may also pass the connection details as environment variables. You can set the following `evengsdk` environment variables:

* `EVE_NG_HOST ` - EVE-NG host name or IP address
* `EVE_NG_USERNAME` - EVE-NG username
* `EVE_NG_PASSWORD` - EVE-NG API/GUI password
* `EVE_NG_PORT` - EVE-NG API port. Default `80`
* `EVE_NG_PROTOCOL` - EVE-NG API protocol. Default `http`
* `EVE_NG_SSL_VERIFY` - Verify SSL. Default `False`
* `EVE_NG_INSECURE` - Suppress insecure warnings. Default `False`
* `EVE_NG_LAB_PATH` - EVE-NG default lab path. Ex. `/myLab.unl`

You may set the variables and export them to your shell environment. You can also define your environment variables in a `.env` folder that will automatically be sourced. The example. below shows the contents of a `.env`  file that will permit you to both source the file and automatically load the variables as needed.

```txt
export EVE_NG_HOST=192.168.2.100
export EVE_NG_USERNAME=admin
export EVE_NG_PASSWORD=eve
export EVE_NG_PORT=80
export EVE_NG_PROTOCOL=http
export EVE_NG_SSL_VERIFY=False
export EVE_NG_INSECURE=True
export EVE_NG_LAB_PATH='/mylab.unl'
```

## :keyboard: Commands

::: mkdocs-click
    :module: evengsdk.cli.cli
    :command: main
    :prog_name: eve-ng
    :depth: 1
