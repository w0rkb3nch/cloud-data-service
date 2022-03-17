import os
import pymongo
from pymongo.errors import BulkWriteError

class Collection:
    def __init__(self):
        mongo_client = pymongo.MongoClient(os.environ.get("MONGODB_URL"))
        mongo_db = mongo_client.cloud_db
        self._mongo_collection = mongo_db.softwares
        self._mongo_collection.create_index([("name", pymongo.ASCENDING)], unique=True)

    def insert_softwares(self, softwares):
        try:
            self._mongo_collection.insert_many(softwares)
        except BulkWriteError:
            for software in softwares:
                self._mongo_collection.replace_one(
                    {'name' : software['name']}, {**software}, upsert=True
                )

    def get_sofware_by_name(self, software_name):
        software = self._mongo_collection.find_one({"name": software_name})
        del software["_id"]
        return software
