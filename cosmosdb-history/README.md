# Bing Chat with Cosmos DB history

![Illustration!](bing_chat_cosmosdb_history.png)

## Features
- This demo shows how to connect the Bing search API to Langchain tools to get up to date answers
- The chat messages are stored in a Cosmos DB for NoSQL database

## Requirements
- Streamlit application
- Tested only with Python 3.10.9. May not work with Python 3.11+ !
- Azure OpenAI account
- Bing search API resource
- Azure Cosmos DB for NoSQL account


## Setup
- Create virtual environment: <code>python -m venv .venv</code>
- Activate virtual ennvironment: <code>.venv\scripts\activate</code>
- Install required libraries: <code>pip install -r requirements.txt</code>

- Create a Bing resource in the Azure portal

![Illustration!](bing_resource.png)

- Create an Azure Cosmos DB for NoSQL account in the Azure portal

- Copy .env template to .env
- Replace keys with your own values
- Make sure that the model referenced in your .env file has been deployed to your Azure OpenAI account

## Demo script
- Run demo: <code>streamlit run app.py</code>

- Chat messages are stored in Cosmos DB for NoSQL

![Illustration!](cosmosdb_history.png)