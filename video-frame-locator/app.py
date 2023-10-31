import os, openai, json, random, uuid, requests, time, cv2,glob,sys,shutil

from dotenv import load_dotenv
from utils import get_results_using_prompt, process_all_images, video_details, extract_frames
import streamlit as st

from IPython.display import Image
from matplotlib import pyplot as plt
from PIL import Image as PILImage
from tqdm import tqdm
from IPython.display import Video

import http.client
import urllib.parse
import base64

from datetime import datetime
from moviepy.editor import *
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import CosmosDBChatMessageHistory, ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import AzureChatOpenAI
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

INDEX_NAME = "videoindex"
FRAMES_DIR = "frames"
EMBEDDINGS_DIR = "embeddings"
VIDEO_URL=f"https://{os.getenv('BLOB_STORAGE_ACCOUNT')}.blob.core.windows.net/videos/Quelle application pour envoyer un colis.mp4?{os.getenv('BLOB_SAS_TOKEN')}"
video_file = "videos/retail_video.mp4"


# ----------------------------- 
def display_env():
    """
    Get a list of all variables from the .env file and display them
    """    
    env_variables = os.environ
    for key, value in env_variables.items():
        st.write(f"{key}: {value}")

if __name__ == "__main__":
    title = "Video frame locator with Florence"
    st.set_page_config(page_title=title, layout="wide")
    st.write(f"## {title}")    

    st.write("This demo shows how to use Florence to locate a frame in a video. The video is first split into frames, then each frame is processed to extract its embedding. Finally, the embeddings are used to find the most similar frames to a given question.")
    
    video_file = open(video_file, 'rb')
    video_bytes = video_file.read()
    embeddings = []

    # Afficher le player video
    st.video(video_bytes)
    
    st.write("### Video details")
    duration, fps, nbframes = video_details(video_file.name)
    st.write(f"Duration: {duration} seconds")
    st.write(f"FPS: {fps} fps")

    # --------------------------
    st.divider()
    st.write("### Online demo")
    st.write("If you are running the online demo, 700 frames have already been extracted and embeddings have been computed for each frame. ")
    st.write("You can directly ask a question and get the results.")
        
    filename = "embeddings/20231021_160317.json"
    with open(filename, "r") as f:
        embeddings = json.load(f)
    st.write("Embeddings loaded from:", filename)
    st.write("Number of images =", len(embeddings))
    # --------------------------

    st.divider()
    st.write("### Building your own demo")

    st.write(f"<b>Extract frames:</b>", unsafe_allow_html=True)
    image_files = glob.glob(FRAMES_DIR + "/*")
    # sort images by name
    image_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))    

    st.write(f"Number of frames: <b>{len(image_files)}</b>", unsafe_allow_html=True)

    st.write("If the number of frames indicated above equals 0, you need to extract the frames from the video first. This will create 1 frame per second of the video.")
    if st.button("Extract frames"):
        with st.spinner("Extracting frames (1 per sec)..."):
            nb_frames = extract_frames(video_file.name, fps, FRAMES_DIR)
            st.write(f"Successfully extracted {nb_frames} frames !")


    st.write(f"<b>Compute embeddings:</b>", unsafe_allow_html=True)
    embeddings_files = glob.glob(EMBEDDINGS_DIR + "/*")
    st.write(f"Number of embedding files: <b>{len(embeddings_files)}</b>", unsafe_allow_html=True)
    st.write("If the number of embedding files indicated above is greater than 0, you can load embeddings from one of the files. Otherwise, click on 'Compute embeddings' to generate embeddings for all the images.")
    if st.button("Compute embeddings"):

        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with st.spinner(f"Computing embeddings for {len(image_files)} images..."):
            start = time.time()

            # Running the images vector embeddings for all the images files
            embeddings = process_all_images(image_files, max_workers=4, max_retries=20)

            # End of job
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elapsed = time.time() - start
            st.write(f"\nElapsed time: {int(elapsed / 60)} minutes, {int(elapsed % 60)} seconds")
            st.write("Number of processed images =", len(embeddings))
            st.write(f"Processing time per image = {(elapsed / len(embeddings)):.5f} sec")
            
            # Saving embeddings into a Json file
            current_dt = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
            json_file = os.path.join(EMBEDDINGS_DIR, f"{current_dt}.json")
            with open(json_file, "w") as f:
                json.dump(embeddings, f)

            st.write("Embeddings saved to:", json_file)

    if st.selectbox('Select an embedding file', embeddings_files):
        with open(embeddings_files[0], "r") as f:
            embeddings = json.load(f)
        st.write("Embeddings loaded from:", embeddings_files[0])
        st.write("Number of images =", len(embeddings))


    # --------------------------

    st.divider()
    st.write("### Q&A")
    st.write("Here are some examples of questions you can ask:")

    questions = [
        "liquid spilled on the floor",
        "I want to see the woman with a pink jacket",
        "woman falling on the floor",
        "person with a grey t-shirt pushing a cart",
        "agent cleaning the floor"
    ]
    questions
    query = st.text_input("Ask a question about the video")
    if st.button("Search"):        
        with st.spinner("Please wait.."):
            df = get_results_using_prompt(query, image_files, embeddings, topn=4, disp=False)
        
            columns = st.columns(2)
            for i, row in df.iterrows():
                # st.write(row)
                columns[i % 2].image(row["image_file"], caption=row["image_file"], use_column_width=True)
        
        
    