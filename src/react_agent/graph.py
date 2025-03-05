"""An Agent."""

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain import hub 

from datetime import datetime 

# model initialization
model = ChatOpenAI(
    model="gpt-4o-mini"
)

# db initialization
db = SQLDatabase.from_uri("sqlite:///src/react_agent/db/product_demo.db")

# Tools
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

# math_agent = create_react_agent(
#     model=model,
#     tools=[add, multiply],
#     name="math_expert",
#     prompt="You are a math expert. Always use one tool at a time."
# )

research_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="research_expert",
    prompt="You are a world class researcher with access to web search."
)

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")  
system_message = prompt_template.format(dialect="SQLite", top_k=5) 

sql_agent = create_react_agent(
    model=model, 
    name='sql_agent',
    tools=sql_toolkit.get_tools(),
    prompt=system_message
)

# Create supervisor workflow
workflow = create_supervisor(
    [research_agent, sql_agent],
    model=model,
    prompt=(
        "You are a team supervisor managing a research expert and a sql expert connected to a product database."
        "For current events, use research_agent. "
        "For learning about products from database use sql_agent."
    )
)

app = workflow.compile()
