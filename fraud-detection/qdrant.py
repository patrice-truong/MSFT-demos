import uuid
import csv
from dotenv import load_dotenv
import streamlit as st
import os
import requests

load_dotenv()

CHUNK_SIZE = 100
QDRANT_BASE_URL = f"http://{os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}"

def get_data(url):
    headers = {
        'Content-Type': 'application/json',
    }

    url = f"{QDRANT_BASE_URL}{url}"
    return requests.get(
        url, 
        headers=headers
    )

def post_data(url, payload):
    headers = {
        'Content-Type': 'application/json',
    }

    url = f"{QDRANT_BASE_URL}{url}"

    return requests.post(
        url, 
        headers = headers,
        json = payload
    )

def put_data(url, payload):
    headers = {
        'Content-Type': 'application/json',
    }

    url = f"{QDRANT_BASE_URL}{url}"

    return requests.put(
        url, 
        headers = headers,
        json = payload
    )    

def delete_data(url):
    headers = {
        'Content-Type': 'application/json'
    }

    url = f"{QDRANT_BASE_URL}{url}"

    # utils.log(f"Delete_data: {url}")

    return requests.delete(
        url, 
        headers = headers
    )

def get_collections():
    return get_data(f"/collections")

def display_collections():
    response = refresh_collections()
    st.session_state["collections"] = response.json()

    if response:
        st.write(st.session_state["collections"])
        # Add a button at the end of each row to delete the collection
        for collection in st.session_state["collections"]["result"]["collections"]:
            if st.button(f"Delete {collection['name']}"):
                delete_collection(collection['name'])

def getVectorsCount(collection_name):    
    try:        
        response = post_data(f"/collections/{collection_name}/points/count", {})
        return response.json()["result"] ["count"]       
    except Exception as e:
        st.write(e)    

def delete_collection(collection_name):    
    try:
        delete_data(f"/collections/{collection_name}")
        refresh_collections()
    except Exception as e:        
        st.write(e)

def create_collection(collection_name, vectors_count, distance_metric):

    try:
        payload = {
            "name": collection_name,
            "vectors": {
                "size": vectors_count,
                "distance": distance_metric    
            }
        }
        put_data(f"/collections/{collection_name}", payload)
        refresh_collections()
    except Exception as e:
        st.write(e)    

def refresh_collections():
    try:
        st.session_state["collections"] = get_data(f"/collections")
    except Exception as e:
        st.write(e)

def populate_collection(collection_name, filePath):
    try:
        # Load embeddings from a CSV file
        st.write(f"Loading embeddings from '{filePath}'")
        with open(filePath, 'r') as file:
            
            embeddings = []
            header_skipped = False
            counter = 0
            total = 0
            reader = csv.reader(file, delimiter=',', quotechar='"')

            for i, line in enumerate(reader):
                # Skip the header row
                if not header_skipped:
                    header_skipped = True
                    continue
                # Extract the identifier and metadata fields
                title = line[0]
                heading = line[1]
                # Extract the embedding as a list of floats
                embedding = [float(value) for value in line[2:]]
                # Append the identifier, metadata, and embedding to the embeddings list
                payload = {
                    "title": title,
                    "heading": heading
                }
                embeddings.append({
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": payload
                })
                
                counter += 1
                total += 1

                if counter == CHUNK_SIZE:  # upsert every n embeddings
                    # client.upsert(collection_name, embeddings)
                    payload = {
                        "points": embeddings
                    }
                    put_data(f"/collections/{collection_name}/points", payload)
                    st.write(f"Upserted {total} vectors into {collection_name} collection")
                    embeddings = []  # reset embeddings list
                    counter = 0  # reset counter

            # upsert any remaining embeddings
            if len(embeddings) > 0:
                payload = {
                        "points": embeddings
                    }
                put_data(f"/collections/{collection_name}/points", payload)
                st.write(f"Upserted {total + len(embeddings)} vectors into {collection_name} collection")
    except Exception as e:
        st.write(e)

def get_collection_info(collection_name):
    try:
        return get_data(f"/collections/{collection_name}")
    except Exception as e:
        st.write(e)


def get_collection_items(collection_name):
    total = 0
    page_size = 1000
    points = []

    try:

        # Get the initial scroll ID
        response = post_data(
            f"/collections/{collection_name}/points/scroll",
            {"limit": page_size, "with_vector": True}
        )

        next_page_offset = response.json()["result"]["points"][0]["id"]

        # Iterate over all the items in the collection
        while next_page_offset is not None:
            response = post_data(
                f"/collections/{collection_name}/points/scroll",
                {"offset": next_page_offset, "limit": page_size, "with_vector": True}
            )

            scroll_data = response.json()

            # Stop iterating if there are no more items
            if not scroll_data["result"]["points"]:
                break

            # Process the items in this page
            for point in scroll_data["result"]["points"]:
                # Do something with the item
                points.append(point)

            # Get the next scroll ID
            next_page_offset = scroll_data["result"]["next_page_offset"]
            total += page_size
            print(total)
            
    except Exception as e:
        st.write(e)

    return points


def search_collection(collection_name, query_vector, topn, min_score=0.8):
    try:
        st.write(f"Searching collection '{collection_name}'")

        payload = { 
            "vector": query_vector,
            "with_vectors": True,
            "with_payload": True,
            "limit": topn,
            "params": {
                "min_score": min_score
            }
        }
        return post_data(f"/collections/{collection_name}/points/search", payload)

    except Exception as e:
        st.write(e)    


def set_document(collection_name, elem):
    # Write element to Qdrant
    try:     
        payload = {
            "points": [{   
                "id": str(uuid.uuid4()),
                "vector": elem['search_embeddings'],
                "payload": {
                    "text": elem['text'],
                    "filename": elem['filename']
                }
            }]
        }
        put_data(f"/collections/{collection_name}/points", payload)

    except Exception as e:
        st.write(e)  

