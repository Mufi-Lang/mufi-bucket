import requests
import hashlib
import json

TAG = "next-experimental"
VERSION = "0.10.0"


links = [
    f"https://github.com/Mustafif/MufiZ/releases/download/{TAG}/mufiz_{VERSION}_x86_64-windows.zip",
    f"https://github.com/Mustafif/MufiZ/releases/download/{TAG}/mufiz_{VERSION}_x86-windows-gnu.zip",
    f"https://github.com/Mustafif/MufiZ/releases/download/{TAG}/mufiz_{VERSION}_aarch64-windows.zip"
]

output = {}
for i, link in enumerate(links):
    response = requests.get(link)
    hash = hashlib.sha256(response.content).hexdigest()
    if i == 0:
        output["64bit"] = {"url": link, "hash": hash}
    elif i == 1:
        output["32bit"] = {"url": link, "hash": hash}
    elif i == 2:
        output["arm64"] = {"url": link, "hash": hash}

json_output = json.dumps(output)

print(json_output)
