import yaml
import os
from pymongo import MongoClient

# Reading the config file
with open("resources/config.yml", 'r') as configyml:
    config = yaml.load(configyml, Loader=yaml.SafeLoader)
    PATH = config.get("Datapath")
    URI = config.get("URI")
    DB_NAME = config.get("Database")
    COLLECTION_NAME = config.get("Collection")
    PORT = config.get("port")
    HOST = config.get("host")

client = MongoClient(URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
