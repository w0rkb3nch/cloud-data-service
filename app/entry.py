import os
from sanic import Sanic
from sanic.response import json
from collection import Collection

app = Sanic("api")


@app.route("/softwares/<software_name>")
async def get_software(_, software_name):
    collection = Collection()
    return json(collection.get_sofware_by_name(software_name))


if __name__ == "__main__":
    app.run(host="0.0.0.0", workers=4, debug=os.environ.get("ENV") == "DEV")
