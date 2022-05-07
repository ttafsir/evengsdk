# Topology Builder

The CLI application allows you to build lab topologies using a declarative model in order to quickly spin a lab and configure nodes using configuration files or jinja templates. Below is a sample topology for a 5 node leaf/spine network.


```yaml
---
  name: test
  description: Arista VEOS leaf-spine lab
  path: "/"
  nodes:
    - name: leaf01
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 50
      top: 135
      configuration:
        file: examples/configs/test_leaf01.cfg
    - name: leaf02
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 200
      top: 135
      configuration:
        template: base.j2
        vars:
          hostname: leaf02
          management_address: 10.10.10.1
    - name: leaf03
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 350
      top: 135
      configuration:
        template: base.j2
        vars: examples/data/leaf03.yml
    - name: leaf04
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 500
      top: 135
    - name: spine01
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 150
      top: 474
    - name: spine02
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 350
      top: 474
  networks:
    - name: vCloud
      network_type: pnet1
      visibility: 1
      top: 300
      left: 475
  links:
    network:
      - {"src": "leaf01", "src_label": "Mgmt1", "dst": "vCloud"}
      - {"src": "leaf02", "src_label": "Mgmt1", "dst": "vCloud"}
      - {"src": "leaf03", "src_label": "Mgmt1", "dst": "vCloud"}
      - {"src": "leaf04", "src_label": "Mgmt1", "dst": "vCloud"}
      - {"src": "spine01", "src_label": "Mgmt1", "dst": "vCloud"}
      - {"src": "spine02", "src_label": "Mgmt1", "dst": "vCloud"}
    node:
      - {"src": "leaf01", "src_label": "Eth3", "dst": "spine01", "dst_label": "Eth1"}
      - {"src": "leaf02", "src_label": "Eth3", "dst": "spine01", "dst_label": "Eth2"}
      - {"src": "leaf03", "src_label": "Eth3", "dst": "spine01", "dst_label": "Eth3"}
      - {"src": "leaf04", "src_label": "Eth3", "dst": "spine01", "dst_label": "Eth4"}
      - {"src": "leaf01", "src_label": "Eth2", "dst": "spine02", "dst_label": "Eth1"}
      - {"src": "leaf02", "src_label": "Eth2", "dst": "spine02", "dst_label": "Eth2"}
      - {"src": "leaf03", "src_label": "Eth2", "dst": "spine02", "dst_label": "Eth3"}
      - {"src": "leaf04", "src_label": "Eth2", "dst": "spine02", "dst_label": "Eth4"}

```

## Device Configurations

The topology builder allows you to create device configurations using either static files or jinja templates. The following example shows how to create a static configuration file for a leaf node.

Below is an example of a static configuration file for a leaf node.

```yaml
  nodes:
    - name: leaf01
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 50
      top: 135
      configuration:
        file: examples/configs/test_leaf01.cfg
```

Jinja templates are also used to create device configurations. The following example shows how to create a jinja template for a leaf node. In this example, the variables in the template are defined in a yaml file. However, you can also define the variables in the template directly under the `vars` key.

```yaml
    - name: leaf03
      template: veos
      image: veos-4.22.0F
      node_type: qemu
      left: 350
      top: 135
      configuration:
        template: base.j2
        vars: examples/data/leaf03.yml
```

To create a topology from the example above simply run the following command

```sh
eve-ng lab create-from-topology -t examples/test_topology.yml --template-dir examples/templates
```

By default, the configuration tool searches for templates in `templates` directory, but you can use `--template-dir` as shown above to specify another location.
