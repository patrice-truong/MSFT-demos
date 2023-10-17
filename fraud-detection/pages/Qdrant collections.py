import streamlit as st
from dotenv import load_dotenv
from qdrant import get_collections, getVectorsCount, refresh_collections, create_collection, delete_collection, get_collection_info

load_dotenv()

COLLECTION_NAME = "embeddings"
DISTANCE_METRIC = "Cosine"
VECTORS_COUNT = 1536
BATCH_SIZE = 100

title = "QDrant collections management"
st.set_page_config(page_title=title, layout="wide")
styles = """
            <style>
            .green { color: green }
            .red { color: red }
            .bold { font-weight: bold }
            </style>
            """
st.markdown(styles, unsafe_allow_html=True)
st.title(title)

# Display collections ----------------
st.header("Display collections")
st.session_state["collections"] = get_collections().json()

if st.session_state["collections"] is not None:
    collections = st.session_state["collections"]["result"]["collections"]
    collection_names = [collection["name"] for collection in collections]
    st.session_state["selected_collection"] = st.selectbox("Choose a collection", collection_names, key="collections_names")

    # display selected collection
    if st.session_state.get('selected_collection', None) is not None:
        selected_collection = st.session_state['selected_collection']
        if selected_collection is not None:
            st.json(get_collection_info(selected_collection).json(), expanded=False)
            st.markdown(f"#### Vectors in this collection: <span class='red'>{getVectorsCount(selected_collection)}</span>", unsafe_allow_html=True)

            if st.button("Refresh"):
                refresh_collections()

            st.header("Delete selected collection")
            if st.button(f"Delete {selected_collection}"):
                delete_collection(selected_collection)


# Create a collection ----------------
st.header("Create a collection")
collection_name = st.text_input("Create a collection", placeholder="Enter collection name")
if st.button("Create collection"):
    vectors_count = VECTORS_COUNT if collection_name == 'articles' else 1024
    create_collection(collection_name, vectors_count, DISTANCE_METRIC)   