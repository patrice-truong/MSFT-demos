import cv2
import os
import requests
import shutil
import math
import json
import requests
import pandas as pd
import streamlit as st
from tqdm import tqdm

from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
key = os.getenv('COMPUTER_VISION_SUBSCRIPTION_KEY')
endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")

def display_env():
    """
    Get a list of all variables from the .env file and display them
    """    
    env_variables = os.environ
    for key, value in env_variables.items():
        st.write(f"{key}: {value}")
    
def image_embedding_batch(image_file):
    """
    Embedding image using Azure Computer Vision 4 Florence
    """
    version = "?api-version=2023-02-01-preview&modelVersion=latest"
    vec_img_url = endpoint + "/computervision/retrieval:vectorizeImage" + version

    headers_image = {
        'Content-type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': key
    }

    with open(image_file, 'rb') as f:
        data = f.read()
    r = requests.post(vec_img_url, data=data, headers=headers_image)
    image_emb = r.json()['vector']

    return image_emb, r


def text_embedding(promptxt):
    """
    Embedding text using Azure Computer Vision 4 Florence
    """
    version = "?api-version=2023-02-01-preview&modelVersion=latest"
    vec_txt_url = endpoint + "/computervision/retrieval:vectorizeText" + version

    headers_prompt = {
        'Content-type': 'application/json',
        'Ocp-Apim-Subscription-Key': key
    }

    prompt = {'text': promptxt}
    r = requests.post(vec_txt_url,
                      data=json.dumps(prompt),
                      headers=headers_prompt)
    text_emb = r.json()['vector']

    return text_emb


def get_cosine_similarity(vector1, vector2):
    """
    Get cosine similarity value between two embedded vectors
    Using sklearn
    """
    dot_product = 0
    length = min(len(vector1), len(vector2))

    for i in range(length):
        dot_product += vector1[i] * vector2[i]

    cosine_similarity = dot_product / (math.sqrt(sum(x * x for x in vector1))
                                       * math.sqrt(sum(x * x for x in vector2)))

    return cosine_similarity


def get_similar_images_using_prompt(prompt, image_files, list_emb):
    """
    Get similar umages using a prompt with Azure Computer Vision 4 Florence
    """
    prompt_emb = text_embedding(prompt)
    idx = 0
    results_list = []

    for emb_image in list_emb:
        simil = get_cosine_similarity(prompt_emb, list_emb[idx])
        results_list.append(simil)
        idx += 1

    df_files = pd.DataFrame(image_files, columns=['image_file'])
    df_simil = pd.DataFrame(results_list, columns=['similarity'])
    df = pd.concat([df_files, df_simil], axis=1)
    df.sort_values('similarity',
                   axis=0,
                   ascending=False,
                   inplace=True,
                   na_position='last')

    return df


def get_results_using_prompt(query, image_files, list_emb, topn, disp=False):
    """
    Get the topn results from a visual search using a text query
    Will generate a df, display the topn images and return the df
    """
    df = get_similar_images_using_prompt(query, image_files, list_emb)

    return df.head(topn)


def video_details(video_filename):
    """
    Video information
    """
    cap = cv2.VideoCapture(video_filename)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    nbframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = nbframes / fps

    print(f"Video filename: {video_filename}")
    print(f"Video duration in secs = {duration:.2f} seconds")
    print(f"Frames per second: {fps}")
    print(f"Total number of frames: {nbframes}")

    return duration, fps, nbframes


def extract_frames(video_file, fps, FRAMES_DIR):

    if os.path.exists(FRAMES_DIR):
        print("Deleting the frames dir...\n")
        shutil.rmtree(FRAMES_DIR)
        print("Done")

    print("Creating directory")
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print("Done")

    frame_count = 0  # do not change
    duration = 0  # do not change

    jpg_quality = 100  # quality percent of the jpg files

    video = cv2.VideoCapture(video_file)
    print("Extracting frames from the video...")

    while True:
        ret, frame = video.read()

        if not ret:
            break

        if frame_count % (fps) == 0:  # 1 frame per each second of the video
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            # videofile name
            cv2.putText(
                frame,
                f"{video_file}",
                (50, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )
            # timeframe
            cv2.putText(
                frame,
                f"{hours:02d} hour {minutes:02d} min {seconds:02d} secs",
                (50, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

            # Saving frames
            time_string = f"{hours:02d}_{minutes:02d}_{seconds:02d}"
            cv2.imwrite(
                FRAMES_DIR + "/" + f"frame_{time_string}.jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, jpg_quality],
            )

            duration += 1

        frame_count += 1

    nb_frames = len(os.listdir(FRAMES_DIR))
    return nb_frames

def process_one_image(image_file, max_retries=20):
    """
    Process image with error management
    """
    num_retries = 0

    while num_retries < max_retries:
        try:
            embedding, response = image_embedding_batch(image_file)

            if response.status_code == 200:
                return embedding

            else:
                num_retries += 1
                print(
                    f"Error processing {image_file}: {response.status_code}.\
                Retrying... (attempt {num_retries} of {max_retries})"
                )

        except Exception as e:
            print(f"An error occurred while processing {image_file}: {e}")
            print(f"Retrying... (attempt {num_retries} of {max_retries})")
            num_retries += 1

    return None

def process_all_images(image_files, max_workers=4, max_retries=20):
    """
    Running the full process using pool
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        embeddings = list(
            tqdm(
                executor.map(lambda x: process_one_image(x, max_retries), image_files),
                total=len(image_files),
            )
        )

    return [emb for emb in embeddings if emb is not None]