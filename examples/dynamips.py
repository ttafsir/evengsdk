from evengsdk.client import EvengClient

client = EvengClient(
    "eve-ng10.ttafsir.me", log_file="test.log", ssl_verify=False, protocol="https"
)
client.disable_insecure_warnings()  # disable warnings for self-signed certificates
client.login(username="admin", password="eve")
client.set_log_level("DEBUG")

# create a lab
lab = {"name": "test_lab", "description": "Test Lab", "path": "/"}
resp = client.api.create_lab(**lab)
if resp["status"] == "success":
    print("lab created successfully.")

# we need the lab path to create objects in the lab
lab_path = f"{lab['path']}{lab['name']}.unl"

# create Nodes
nodes = [
    {
        "name": "r1",
        "template": "c3725",
        "image": "c3725-adventerprisek9-mz124-15",
        "left": 50,
    },
    {
        "name": "r2",
        "template": "c3725",
        "image": "c3725-adventerprisek9-mz124-15",
        "left": 200,
    },
]
for node in nodes:
    client.api.add_node(lab_path, **node)

# create p2p links
p2p_links = [{"src": "r1", "src_label": "e0", "dst": "r2", "dst_label": "e0"}]
for link in p2p_links:
    client.api.connect_node_to_node(lab_path, **link)

client.logout()
