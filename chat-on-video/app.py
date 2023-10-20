import streamlit as st
import os, openai, json, random, uuid, requests, time
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
from moviepy.editor import *
from azure.cosmos import CosmosClient
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

from dotenv import load_dotenv
load_dotenv()
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")

cosmos_endpoint=os.environ['AZURE_COSMOSDB_ENDPOINT']
cosmos_database=os.environ['AZURE_COSMOSDB_NAME']
cosmos_container=os.environ['AZURE_COSMOSDB_CONTAINER_NAME']
connection_string=os.environ['AZURE_COSMOSDB_CONNECTION_STRING']

# Initialize the Cosmos DB client
client = CosmosClient.from_connection_string(connection_string)

# Define the Cosmos DB container where you want to store the data
database = client.get_database_client(cosmos_database)
container = database.get_container_client(cosmos_container)

video_file = None
audio_file = None
question = None
transcript = None

queries = [    
"Quel est le sujet discuté?",
"A quoi sert l'application de La Poste?",
"Fais-moi une liste en 5 points des caractéristiques de l'application de La Poste",
"L'application prend-elle en charge les colis d'autres transporteurs ?",
"L'application prend-elle en charge les colis d'autres transporteurs ? Réponds en un seul mot par Oui ou Non",
]

summary_queries_fr = [    
"Fais-moi un résumé",
"Fais-moi un résumé en moins de 20 mots",
"Fais-moi un résumé pour un enfant en classe de 6e",
"Summarize the transcript for a 6-year old kid",
"Fais-moi un résumé en français, en anglais et en allemand",
"""Fais-moi un résumé.
Ajoute un titre au résumé

Commence la réponse par un paragraphe d'introduction qui donne un apercu du sujet. 
Fournis ensuite une liste des points les plus importants.

Termine le résumé par une conclusion qui résume les points couverts 
TITRE: {{titre}} 
INTRODUCTION: {{introduction}} 

{{points}} 
CONCLUSION: {{ conclusion}}
""",
"""
Taches:
    1. Fais un résumé court et concis du transcript.
    2. Determine si le ton du transcript est positif ou négatif.
    3. Classifie le transcript dans un sujet.
""",
"""
Génère un blog post fun pour LinkedIn. 
- Inclue au moins 5 emojis dans le post. 
- Le post doit faire au plus 200 mots.
- Inclue un titre et une conclusion.
- Le post doit être en français.
- Le post doit être écrit dans un ton positif.
- Inclue au moins 4 hashtags
"""
    ]

summary_queries_en = [    
"Summarize the transcript",
"Summarize the transcript in less than 20 words",
"What is the tone of the transcript?",
"Extract the 5 most important points from the transcript",
"Summarize the transcript for a 6-years old kid",
"Create a summary of the transcript in French, English and German",
"""Summarize the transcript.
Add a title to the summary

Start the answer with an introductory paragraph that gives an overview of the topic.
Then provide a list of the most important points.

End the summary with a conclusion that summarizes the points covered

TITLE: {{title}} 
INTRODUCTION: {{introduction}} 

{{points}} 
CONCLUSION: {{ conclusion}}
""",
"""
Tasks:
    1. Create a short and concise summary of the transcript.
    2. Determine if the tone of the transcript is positive or negative.
    3. Classify the transcript into a topic.
""",
"""
You are a highly skilled assistant to the Marketing and Communication department at Spie. Your objective is to generate interest and excitement around new SPIE initiatives. 

Using the transcript, generate a fun and catchy press release for journalists, with an introduction summarizing the transcript and 2 detailed paragraphs with a title and at least 1000 words each. Each paragraph should be have a title. 

All inquiries should be sent to press@spie.com
----
Use these past press releases as inspiration:
https://www.spie.com/en/news/condition-monitoring-spie-digitalises-technical-facility-management-values-real-estate-germany
https://www.spie.com/en/news/switzerland-spie-contributes-modernisation-pont-rouge-district-geneva
https://www.spie.com/en/news/spie-assists-maintenance-frances-first-offshore-wind-farm-saint-nazaire
""",
"""
Extract the following information from the transcript
1. Classification (key: classification)
2. Company (key: company)
3. Number of words (key: length)
4. Keywords as an array (key: keywords)
5. A short summary in less than 100 words (key: summary)

Please answer in a JSON machine-readable format, using the keys above. Format the outpout as JSON object called "insights". Pretty print the JSON and make sure that it is valid and properly closed at the end
""",
"""
Generate a fun blog post for LinkedIn. 
- Include at least 5 emojis in the post. 
- The post should be at most 200 words long. 
- Include a title and a conclusion. 
- The post should be in English. 
- The post should be written in a positive tone. 
- Include at least 4 hashtags
"""
    ]

def video_to_audio(video_file):
    audio_file = video_file.name.replace(".mp4", ".wav").replace(".mkv", ".wav")

    #load the video clip 
    video = VideoFileClip(video_file.name)

    #extract the audio from the video
    audio = video.audio

    # Set the desired audio parameters
    audio_params = {
        "codec": "pcm_s16le",
        "fps": 16000,  # Set the desired sampling rate: 16000 Hz
        # "fps": 8000,  # Alternatively, set the sampling rate to 8000 Hz
        "nchannels": 1,  # Mono audio
        "bitrate": "16k"  # Set the desired bitrate
    }

    audio.write_audiofile(audio_file, codec=audio_params["codec"],fps=audio_params["fps"],nbytes=2,bitrate=audio_params["bitrate"])
    return audio_file

def audio_to_text_whisper(sound_file):
    """
    Speech to text with Azure Open AI Whisper
    """

    WHISPER_MODEL = "whisper"
    start = time.time()

    # Prepare the headers
    headers = {
        "api-key": openai.api_key,
    }

    # Prepare the data for the multipart/form-data request
    json = {
        "file": (sound_file, open(sound_file, "rb"), "audio/mp3"),
        "locale": "fr-FR",
    }

    # Define the API endpoint URL
    url = f"{openai.api_base}/openai/deployments/{WHISPER_MODEL}/audio/transcriptions?api-version=2023-09-01-preview&"
    # Send the POST request
    response = requests.post(url, headers=headers, files=json)
    # Check the response
    if response.status_code == 200:
        print("Transcription request was successful.")
        transcription_data = response.json()

        elapsed = time.time() - start
        print(
            "Elapsed time: "
            + time.strftime(
                "%H:%M:%S.{}".format(str(elapsed % 1)[2:])[:15], time.gmtime(elapsed)
            )
        )
        return transcription_data
    else:
        print(f"Error: {response.status_code}")
        
def audio_to_text(audio_file):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["fr-FR", "en-US"])
    transcript_file = audio_file.replace(".wav", ".txt")

    # audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        auto_detect_source_language_config=auto_detect_source_language_config,
        audio_config=audio_config
    )

    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))

    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(
            speech_recognition_result.no_match_details))
        
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(
            cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(
                cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")

    st.write(speech_recognition_result.text)
    with open(transcript_file, "w") as file:
        # file.write(f"Transcript de la vidéo: ${transcript_file.replace('.txt', '')}\n")
        file.write(speech_recognition_result.text)
    
    return transcript_file, speech_recognition_result.text

def audio_to_text_continuous(audio_file):
    """
    Azure Speech to text
    """
    print("Running the speech to text...")
    
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region
    )
    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
    languages=["fr-FR", "en-US"])
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat(1)

    # Creates a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        auto_detect_source_language_config=auto_detect_source_language_config,
        audio_config=audio_config
    )

    # Variable to monitor status
    done = False

    # Service callback for recognition text
    transcript_display_list = []
    transcript_ITN_list = []
    confidence_list = []
    words = []

    def parse_azure_result(evt):
        import json

        response = json.loads(evt.result.json)
        transcript_display_list.append(response["DisplayText"])
        confidence_list_temp = [item.get("Confidence") for item in response["NBest"]]
        max_confidence_index = confidence_list_temp.index(max(confidence_list_temp))
        confidence_list.append(response["NBest"][max_confidence_index]["Confidence"])
        transcript_ITN_list.append(response["NBest"][max_confidence_index]["ITN"])
        words.extend(response["NBest"][max_confidence_index]["Words"])


    # Service callback that stops continuous recognition upon receiving an event `evt`
    def stop_cb(evt):
        print("CLOSING on {}".format(evt))
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True

        # Do something with the combined responses
        # print(transcript_display_list)
        # print(confidence_list)
        # print(words)


    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(
        lambda evt: print(evt.result.text)
    )

    speech_recognizer.recognized.connect(parse_azure_result)
    speech_recognizer.session_started.connect(
        lambda evt: print("SESSION STARTED: {}".format(evt))
    )
    speech_recognizer.session_stopped.connect(
        lambda evt: print("SESSION STOPPED {}".format(evt))
    )
    speech_recognizer.canceled.connect(
        lambda evt: print("CANCELED {}".format(evt))
    )
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(0.5)

    print("Done")
    # return transcript
    transcript_file = audio_file.replace(".wav", ".txt")
    with open(transcript_file, "w") as file:
        transcript_display_string = ' '.join(transcript_display_list)
        file.write(transcript_display_string)
    
    return transcript_file, transcript_display_string
    # return transcript_display_list, confidence_list, words

def store_question_and_answer(question, answer):

    question = question.replace('"', '')
    answer = answer.replace('"', '')

    # Define the document to be inserted
    chat_session_id = str(uuid.uuid4())
    chat_session = {
        'id': chat_session_id,
        'ChatSessionId': chat_session_id,
        'Name': '',
        'UserEmail': 'patrice.truong@microsoft.com',
        'UserName': 'Patrice Truong',
        'Type': 'ChatSession',
        'ChatHistory': [],
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    userChatMessage = {
        'id': chat_session["id"],
        'ChatSessionId': chat_session["id"],
        'UserEmail': 'patrice.truong@microsoft.com',
        'UserName': 'Patrice Truong',
        'Type': 'ChatMessage',
        'Sender': 'user',
        'Text': question,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    botChatMessage = {
        'id': chat_session["id"],
        'ChatSessionId': chat_session["id"],
        'UserEmail': "",
        'UserName': "AI Bot",
        'Type': 'ChatMessage',
        'Sender': 'bot',
        'Text': answer,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    chat_session["ChatHistory"].append(userChatMessage)
    chat_session["ChatHistory"].append(botChatMessage)
    container.upsert_item(body=chat_session)
        
def get_answer(qa, question):    


    # st.session_state.messages = [];
    # st.session_state.messages.append({"role": "user", "content": question})
    result = qa({
        "question": question, 
        "chat_history": [(message["role"], message["content"]) for message in st.session_state.messages]
    })
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = result["answer"]
        message_placeholder.markdown(full_response + "|")
    message_placeholder.markdown(full_response)
    print(full_response)
    # st.session_state.messages.append({"role": "assistant", "content": full_response})   
    return full_response 

def azure_openai(prompt, temperature=0.7):
    """
    Get Azure Open AI results
    """
    preprompt = (
        "You are going to give answer based on the transcript of a video file.\n"
    )
    prompt = preprompt + prompt

    results = openai.Completion.create(
        engine="gpt-35-turbo",
        prompt=prompt,
        temperature=temperature,
        max_tokens=400,
    )

    answer = results["choices"][0]["text"].strip("\n")

    return answer

def vectorize(transcript_text):
    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=150,
                        length_function=len
                    )

    # Process the transcript and create the documents list
    documents = text_splitter.split_text(text=transcript_text)

    # Vectorize the documents and create vectorstore
    embeddings = OpenAIEmbeddings(engine=os.getenv("OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME"), chunk_size=1) 
    vector_store = FAISS.from_texts(documents, embedding=embeddings)
    return vector_store

def ask(vector_store, question):
    

    general_system_template = r""" 
Your task is to analyze the transcript of a video and answer questions, using the transcript as context. 

- Reply in the same language as the user's question.

----
{context}
"""
    general_user_template = "Question:```{question}```"
    messages = [
        SystemMessagePromptTemplate.from_template(general_system_template),
        HumanMessagePromptTemplate.from_template(general_user_template)
    ]
    
    qa_prompt = ChatPromptTemplate.from_messages( messages )
    
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("OPENAI_ENGINE_MODEL_NAME"), 
        temperature=0, 
        max_tokens=1000)
    
    qa = ConversationalRetrievalChain.from_llm(llm, vector_store.as_retriever(), combine_docs_chain_kwargs={'prompt': qa_prompt})

    answer = get_answer(qa, question)

    # Store the question and answer in Cosmos DB
    store_question_and_answer(question, answer)

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "video_file" not in st.session_state:
        st.session_state.video_file = None  

    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = ""

    if "question" not in st.session_state:
        st.session_state.question = ""

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None


# ----------------------------- 

def main():
    title = "Azure OpenAI sur vos videos (avec Cosmos DB)"
    st.set_page_config(page_title=title)
    st.markdown(
    """
    <style>
        .right-align {
            display: inline-block;
            text-align: right;
        }
    </style>
    """,unsafe_allow_html=True)    
    col1, col2 = st.columns([1,2])
    with col1:
        st.image("laposte.png", width=100)
    with col2:
        st.write(f"## {title}")    

    
    video_file = st.file_uploader("Upload a video", type=['mp4', 'mkv'])
    audio_file = None

    # Initialize Streamlit chat UI
    init_state()

    if video_file:
        video_file = open(video_file.name, 'rb')
        video_bytes = video_file.read()
        st.session_state.video_file = video_file

        # Afficher le player video
        st.video(video_bytes)

        if st.button("Create transcript"):

            transcript_file = video_file.name.replace(".mp4", ".txt").replace(".mkv", ".txt")

            # convert video to audio
            st.write("### Extracting audio...")
            audio_file_name = video_to_audio(video_file)
            st.write(f"Audio file saved: '{audio_file_name}' !")
            audio_file = open(audio_file_name, 'rb')
            audio_bytes = audio_file.read()

            # Afficher le player audio
            st.audio(audio_bytes, format='audio/wav')

            # test if transcript file exists
            if os.path.exists(transcript_file):
                # read transcript file
                with open(transcript_file, "r") as file:
                    st.session_state.transcript_text = file.read()

            else:       
                st.write("### Creating transcript...")            
                transcript, transcript_text = audio_to_text_whisper(audio_file_name)   
                st.session_state.transcript_text = transcript_text

            st.write(st.session_state.transcript_text)
            st.session_state.vector_store = vectorize(st.session_state.transcript_text)

    if st.session_state.transcript_text:
        st.json(queries, expanded = False)
        st.json(summary_queries_fr, expanded = False)
        st.text_area('Ask me anything: ', key="question", height=200)

    if st.session_state.question:
        with st.spinner("Generating..."):
            ask(st.session_state.vector_store, question=st.session_state.question)
                
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

                    
            

if __name__ == "__main__":
    main()

