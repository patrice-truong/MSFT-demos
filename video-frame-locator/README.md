# Video frame locator using Azure Computer Vision
![Illustration!](video_frame_locator.jpg)
## Features
- Video to images, using opencv
- Create embeddings using Azure Computer Vision 4 Florence
- Chatbot using GPT 3.5 Turbo

## Requirements
- Streamlit application
- Tested only with Python 3.10.9. May not work with Python 3.11+ !
- Azure OpenAI account
- Azure Computer Vision account

## Setup
- Create virtual environment: <code>python -m venv .venv</code>
- Activate virtual ennvironment: <code>.venv\scripts\activate</code>
- Install required libraries: <code>pip install -r requirements.txt</code>

- Copy .env template to .env
- Replace keys with your own values
- Make sure that GPT 3.5 Turbo is deployed in your Azure OpenAI account
- Create a "videos" folder and download the test video from this location: https://uvsportalstorage.blob.core.windows.net/multifileindex-video-search-samples/video-search/6/samplevideo.mp4?sv=2021-10-04&se=2024-04-18T06%3A09%3A27Z&sr=b&sp=r&sig=up6qUC4WOdYCEMDyvtAYDRvToki6Wi3FH23A%2Fo%2BwSHE%3D

## Demo script
- Run demo: <code>streamlit run app.py</code>
- Change the location of the video in app.py to point to your own video
<code>video_file = "videos/retail_video.mp4"</code>
- If this is the first time running the demo, you will need to click on the "Extract frames" button to extract frames from the video
- Compute the embeddings (once) 
- You are now ready to ask questions on your video

