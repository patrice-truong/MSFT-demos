import time
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv
import os
import mimetypes
from qdrant import getVectorsCount, put_data, search_collection

from azureblobstorage import upload_file


load_dotenv()

if 'vision_base_endpoint' not in st.session_state:
    st.session_state['vision_base_endpoint']=os.getenv("COMPUTER_VISION_ENDPOINT")
if 'vision_key' not in st.session_state:
    st.session_state["vision_key"] = os.getenv("COMPUTER_VISION_KEY")

COLLECTION_NAME = "accidents"
CONTAINER_NAME = "accidents"
DISTANCE_METRIC = "Cosine"
VECTORS_COUNT = 1536
BATCH_SIZE = 100

title = "Fraud detection using Azure Computer Vision"
st.set_page_config(page_title=title, layout="wide")
st.header(title)
styles = """
            <style>
            .green { color: green }
            .red { color: red }
            .bold { font-weight: bold }
            </style>
            """
st.markdown(styles, unsafe_allow_html=True)

st.write("#### Scenario")
st.write("In this scenario, we will use the Qdrant API to index images and then search for identical images. \n\nThis use case has potential applications in the insurance industry, specifically for identifying fraudulent claims. An example of such fraudulent activity is when an individual submits images of accidents that already exist in the database, which constitutes an attempted fraud. In order to detect such attempts, the submitted images are compared to the images already in the database. If the images match exactly, the claim is deemed fraudulent and rejected. On the other hand, if the images do not match exactly, the claim is accepted.")


# ---------------- Images embeddings ----------------
st.write("#### Load accident images into Qdrant")
st.write(f"There are already embeddings for <span class='red bold'>{getVectorsCount('accidents')}</span> accidents in the Qdrant collection", unsafe_allow_html=True)
    
vision_embed_endpoint = f"{st.session_state['vision_base_endpoint']}/computervision/retrieval:vectorizeImage?api-version=2023-02-01-preview&modelVersion=latest"
vision_analyze_endpoint = f"{st.session_state['vision_base_endpoint']}/vision/v3.2/analyze?visualFeatures=Description,Objects,ImageType,Color,Categories,Tags,Faces,Adult&language=en"
# vision_detect_endpoint = f"{st.session_state['vision_base_endpoint']}/vision/v3.2/detect"
uploaded_files = st.file_uploader("Upload a document to add it to the Azure Storage Account", type=['jpeg','jpg','png'], accept_multiple_files=True)


if st.button("Convert images into embeddings"):
    if uploaded_files is not None:
        points = []
        for i, up in enumerate(uploaded_files):
            # To read file as bytes:
            bytes_data = up.getvalue()
            if st.session_state.get('filename', '') != up.name:
                # Upload a new file
                st.session_state['filename'] = up.name
                content_type = mimetypes.MimeTypes().guess_type(up.name)[0]
                fullpath = upload_file(CONTAINER_NAME, bytes_data, st.session_state['filename'], content_type=content_type)
                            
                headers = { 'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': st.session_state["vision_key"] }

                try:
                    # Analyze the image
                    analyze_response = requests.post(
                        vision_analyze_endpoint,
                        headers=headers,
                        # params=params,
                        json={'url': fullpath}
                    )
                
                    # create the embedding vector
                    response = requests.post(
                        vision_embed_endpoint,
                        headers=headers,
                        # params=params,
                        json={ 'url': fullpath }
                    )
                    
                    r = response.json()

                    # create and store Qdrant point
                    point = {   
                        "id": str(uuid.uuid4()),
                        "vector": r['vector'],
                        "payload": {
                            "filename": st.session_state['filename'],
                            "fullpath": fullpath,
                            'details': analyze_response.json()
                        }
                    }
                    points.append(point)
                    print(st.session_state['filename'])


                    # flush every 6 images and pause for 30 sec
                    if i> 0 and i%6 == 0:
                        print(f"Uploading {i} images to Qdrant")
                        payload = {
                            "points": points
                        }
                        response = put_data(f"/collections/{COLLECTION_NAME}/points", payload)
                        points = []
                        print("Pausing for 30 seconds..")
                        time.sleep(30)

                except Exception as e:
                    print(f"Error: {e}")
        
        uploaded_files = None

# ---------------- Search images ----------------
st.write(f"#### Searching for identical accident images")

st.session_state['filename'] = ''
st.session_state['file_url'] = ''
uploaded_file = st.file_uploader("Upload the image to find", type=['jpeg','jpg','png'], accept_multiple_files=False)

if st.button("Search for image"):
    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()

        if st.session_state.get('filename', '') != uploaded_file.name:
            # Upload a new file
            st.session_state['filename'] = uploaded_file.name
            content_type = mimetypes.MimeTypes().guess_type(uploaded_file.name)[0]
            st.session_state['file_url'] = upload_file(COLLECTION_NAME, bytes_data, "tmp/"+st.session_state['filename'], content_type=content_type)

            # Analyze the image
            headers = {
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': st.session_state["vision_key"]
            }

            params = {
                'visualFeatures': ['Description','Objects', 'ImageType', 'Color', 'Categories'],
                'language': 'en'
            }
            
            # create the embedding vector
            embedding_response = requests.post(
                vision_embed_endpoint,
                headers=headers,
                params=params,
                json={'url': st.session_state['file_url']}
            )
            # st.write(response.json())
            r = embedding_response.json()
            query_vector = r['vector']
            st.write("Vector created using Azure Computer Vision API")

            # Search for identical images
            start = time.time()
            st.write(f"Searching for images identical to '{uploaded_file.name}'")
            
            # display source image
            st.image(st.session_state['file_url'], width=200)
            min_score = 1
            result = search_collection(COLLECTION_NAME, query_vector, topn=1)
            end = time.time()
            st.write(f"Search completed in {end - start} sec")

            # Display identical images in the qdrant database
            found = False
            if result.json()["result"][0]["score"] >= min_score:
                for image in (result.json()["result"]):
                    found = True
                    st.image(image["payload"]["fullpath"], width=200)
                st.markdown("<span class='green bold'>Found image</span>", unsafe_allow_html=True)
                st.json(result.json())

            if not found:
                st.markdown("<span class='red bold'>No Match</span>", unsafe_allow_html=True)
            
            # Delete the uploaded image
            # delete_image(st.session_state['filename'])
            st.session_state['filename'] = ''
            st.session_state['file_url'] = ''        