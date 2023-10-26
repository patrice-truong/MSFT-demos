import os, tiktoken, json, csv, time, openai

import streamlit as st
from dotenv import load_dotenv

from cosmosdb_mongodb import count_products, create_mongo_objects, insert_many, insert_one, insert_one_if_not_exists, similar
from product import Product

BATCH_SIZE = 100
MIN_SCORE = 0.8
EMBEDDING_ENCODING = 'cl100k_base'

load_dotenv()
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")

def get_embedding(text: str, engine="text-embedding-ada-002") -> list[float]:
    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")
    EMBEDDING_ENCODING = 'cl100k_base' if engine == 'text-embedding-ada-002' else 'gpt2'
    encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)
    result = openai.Embedding.create(input=encoding.encode(text), engine=engine)
    return result["data"][0]["embedding"]

def search_for(search_text):
    # create embedding
    start = time.time()
    query_vector = get_embedding(search_text)
    end = time.time()
    st.write(f"Vector generated in {end - start} sec, using text-embedding-ada-002")

    # search for embedding
    start = time.time()
    st.write(f"Searching for documents similar to '{search_text}'")
    matching_products = similar(query_vector, limit=5, min_score=MIN_SCORE)
    end = time.time()
    st.write(f"Search completed in {end - start} sec")

    # display matching images
    sas = os.getenv("BLOB_SAS_TOKEN")

    found = False
    if len(matching_products) > 0:
        st.markdown(f"<span class='green bold'>Found article(s) </span>", unsafe_allow_html=True)
        found = True
        # Create a table with 5 columns
        columns = st.columns(5)
        # Display each image in a separate column
        for i, image in enumerate(matching_products):
            with columns[i]:
                st.image(f"{image['image_path']}{sas}", width=200)

        st.json(matching_products)
    
    if not found:
        st.markdown("<span class='red bold'>No Match</span>", unsafe_allow_html=True)



title = "Product catalog search, using embeddings in Cosmos DB for MongoDB"
styles = """
            <style>
            .green { color: green }
            .red { color: red }
            .bold { font-weight: bold }
            </style>
            """
st.markdown(styles, unsafe_allow_html=True)
st.header(title)

st.write("#### Scenario")
st.write("This page demonstrates how to use Cosmos DB for MongoDB to search for products in a product catalog. The product catalog is stored in a Cosmos DB database. The product catalog is enriched with embeddings computed by OpenAI. The search is performed by Cosmos DB for MongoDB vcore")

st.write(f"There are embeddings for <span class='red bold'>{count_products()}</span> products in the Cosmos DB for MongoDB collection", unsafe_allow_html=True)

if st.button("Load products into Cosmos DB for MongoDB"):
    engine = "text-embedding-ada-002"
    products_file = "100K_products.csv"
    IMAGE_BASE = f"https://{os.getenv('BLOB_ACCOUNT_NAME')}.blob.core.windows.net/{os.getenv('BLOB_CONTAINER_NAME')}/assets"
    products = []

    create_mongo_objects("productsDb", "products_1536", "vectorIndex1536")
    
    # Open the CSV file
    with open(products_file, 'r', encoding="utf-8") as file:
        csv_reader = csv.reader(file, delimiter=',', quotechar='"')

        # Skip the first row
        next(csv_reader)

        # Create a list to store the Product objects
        for linenumber, row in enumerate(csv_reader):
            # Create a Product object from the row data
            product = Product(*row)
            product.image_path = f"{IMAGE_BASE}/{product.article_id[:3]}/{product.article_id}.jpg"
            print(product.article_id)
            embeddings = get_embedding(product.to_json())
            product.embedding = embeddings
            insert_one_if_not_exists(product.__dict__)

        st.write("Finished !")
            
    # article_id,product_code,prod_name,product_type_no,product_type_name,product_group_name,graphical_appearance_no,graphical_appearance_name,colour_group_code,colour_group_name,perceived_colour_value_id,perceived_colour_value_name,perceived_colour_master_id,perceived_colour_master_name,department_no,department_name,index_code,index_name,index_group_no,index_group_name,section_no,section_name,garment_group_no,garment_group_name,detail_desc


        

# ---------------- Search articles ----------------
st.write("#### Search product catalog")

search_text = st.text_input("Look for similar products. Try sunglasses, beige cargo pants, pink t-shirt, handbag with shoulder strap...", placeholder="Look for similar products")

# create a table with 6 columns
# in each column, add a button
# when the button is clicked, search for the text in the button
columns = st.columns(6)
if columns[0].button("Search"):
    st.write(f"Generating embedding for '{search_text}'")
    search_for(search_text)
if columns[1].button("Beige pants"):
    search_for("Beige cargo pants")
if columns[2].button("Pink T-Shirt"):
    search_for("Pink T-Shirt")
if columns[3].button("Sunglasses"):
    search_for("Sunglasses")
if columns[4].button("handbag with shoulder strap"):
    search_for("handbag with shoulder strap")
    