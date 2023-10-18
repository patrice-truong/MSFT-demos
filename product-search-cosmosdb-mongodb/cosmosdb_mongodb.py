import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

username = os.getenv('COSMOSDB_MONGODB_USERNAME')
password = os.getenv('COSMOSDB_MONGODB_PASSWORD')
host = os.getenv('COSMOSDB_MONGODB_HOST')
database_name = os.getenv('COSMOSDB_MONGODB_DATABASE')
collection_name = os.getenv('COSMOSDB_MONGODB_COLLECTION')
port = os.getenv('COSMOSDB_MONGODB_PORT')

connection_string = f'mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{host}/?"tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"'
client = MongoClient(connection_string)
database = client[database_name]
collection = database[collection_name]

def drop_and_create_mongo_objects(database_name, collection_name, index_name):
    # List all existing database names
    existing_databases = client.list_database_names()

    if database_name in existing_databases:
        # The database exists, drop it and create it again
        client.drop_database(database_name)

    database = client[database_name]
    collection = database[collection_name]

    # Define the index key, specifying the field "embedding" with a cosine similarity search type
    index_key = [("embedding", "cosmosSearch")]

    # Define the options for the index
    index_options = {
        "kind": "vector-ivf",   # Index type: vector-ivf
        "numLists": 100,        # Number of lists (partitions) in the index
        "similarity": "COS",    # Similarity metric: Cosine similarity
        "dimensions": 1536      # Number of dimensions in the vectors
    }

    # Create the index with the specified name and options
    collection.create_index(index_key, name=index_name, cosmosSearchOptions=index_options)

    return f"Success."

def get_products():
    limit = 10
    products = []
    for product in collection.find().limit(limit):
        serialized_product = {**product, "_id": str(product["_id"])}
        products.append(serialized_product)
    return products

def count_products():
    c = collection.count_documents({})
    return c

def insert_one(product):
    return collection.insert_one(product)

def insert_many(products):
    return collection.insert_many(products)

def similar(query_vector, limit=5, min_score=0.8):

    pipeline = [
            {
                '$search': {
                    'cosmosSearch': {
                        'vector': query_vector,
                        'path': 'embedding',
                        'k': limit
                    },
                    'returnStoredSource': True
                }
            }
        ]

    products = []
    for product in collection.aggregate(pipeline):
        serialized_product = {**product, "_id": str(product["_id"])}
        products.append(serialized_product)

    return products
    