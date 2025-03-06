"""An Agent."""

from langchain_openai import ChatOpenAI
from langchain import hub
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
import bs4
from langchain_core.tools import tool
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing_extensions import List, TypedDict
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
from langchain_community.tools import TavilySearchResults
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings

import os
from datetime import datetime 

# model initialization
# Initialize model
model = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


# db initialization
db = SQLDatabase.from_uri("sqlite:///src/react_agent/db/product_demo.db")

# Document Loading
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index = pc.Index('agent-hackathon')
vector_store = PineconeVectorStore(embedding=embeddings, index=index)

# # Index chunks
# _ = vector_store.add_documents(documents=all_splits)


# Tools

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

sql_toolkit = SQLDatabaseToolkit(db=db, llm=model)

web_search = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
        # include_domains=[...],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )


# [Supervisor Agent]
# │
# ├── [Web Research Agent]
# │   ├── Tavily Search Integration
# │   ├── Information Retrieval
# │   └── Data Collection
# │
# ├── [SQL Agent]
# │   ├── Database Querying
# │   ├── Data Extraction
# │   └── Structured Analysis
# │
# ├── [RAG Agent]
# │   ├── Knowledge Base Retrieval
# │   ├── Context Augmentation
# │   └── Semantic Processing
# │
# ├── [Analysis Agent]
# │   ├── Data Aggregation
# │   ├── Pattern Recognition
# │   └── Insight Generation
# │
# ├── [Writing Agent]
# │   ├── Content Synthesis
# │   ├── Report Formatting
# │   └── Summarization
# │
# ├── [Verification Agent]
# │   ├── Fact-Checking
# │   ├── Source Validation
# │   └── Consistency Review
# │
# └── [Optimization Agent]
#     ├── Prompt Engineering
#     ├── Performance Monitoring
#     └── Workflow Refinement

research_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="research_expert",
    prompt="You are a world class researcher with access to web search. Do not do any math."
)

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")  
system_message = prompt_template.format(dialect="SQLite", top_k=5) 

sql_agent = create_react_agent(
    model=model, 
    name='sql_agent',
    tools=sql_toolkit.get_tools(),
    prompt=system_message
)

rag_agent = create_react_agent(model, [retrieve], name="rag_agent")




# Create supervisor workflow
workflow = create_supervisor(
    [research_agent, sql_agent, rag_agent],
    model=model,
    prompt=(
        "You are a team supervisor managing a research expert and a sql expert connected to a product database and a rag agent that has information on an article LLM Powered Autonomous Agents."
        "For current events, use research_agent. "
        "For learning about products from database use sql_agent."
        "For questions on the LLM Powered Autonomous Agents paper use rag_agent."
    )
)

app = workflow.compile()
