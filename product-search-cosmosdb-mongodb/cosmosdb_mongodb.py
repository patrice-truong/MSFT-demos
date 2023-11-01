def create_index(collection, index_name, dimension_size=1536, num_lists=100):
    # check if index exists
    existing_indexes = collection.index_information()
    if index_name not in existing_indexes:
        # Define the index key, specifying the field "embedding" with a cosine similarity search type
        index_key = [("embedding", "cosmosSearch")]
        # Define the options for the index
        index_options = {
            "kind": "vector-ivf",   # Index type: vector-ivf
            "numLists": num_lists,        # Number of lists (partitions) in the index
            "similarity": "COS",    # Similarity metric: Cosine similarity
            "dimensions": dimension_size      # Number of dimensions in the vectors
        }
        # Create the index with the specified name and options
        index = collection.create_index(index_key, name=index_name, cosmosSearchOptions=index_options)
        return index

def get_products(collection):
    limit = 10
    products = []
    for product in collection.find().limit(limit):
        serialized_product = {**product, "_id": str(product["_id"])}
        products.append(serialized_product)
    return products

def count_products(collection):
    c = collection.count_documents({})
    return c

def insert_one(collection, product):
    return collection.insert_one(product)

def insert_one_if_not_exists(collection, product):
    product_id = str(product.get("_id"))
    
    if collection.count_documents({"_id": product_id}) == 0:
        result = collection.insert_one(product)
        return f"Successfully inserted product with _id: {product_id}."
    else:
        return f"Product with _id {product_id} already exists, no insertion performed."

def insert_many(collection, products):
    return collection.insert_many(products)

def insert_many_if_not_exist(collection, products):
    existing_product_ids = [str(product["_id"]) for product in collection.find({}, {"_id": 1})]

    new_products = []
    for product in products:
        product_id = str(product["_id"])
        if product_id not in existing_product_ids:
            new_products.append(product)

    if new_products:
        result = collection.insert_many(new_products)
        return f"Successfully inserted {len(new_products)} new products."
    else:
        return "No new products to insert."


def similar(collection, query_vector, limit=5, min_score=0.8):

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
    