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
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.utilities.alpha_vantage import AlphaVantageAPIWrapper
from langchain_community.tools.reddit_search.tool import RedditSearchRun
from langchain_community.utilities.reddit_search import RedditSearchAPIWrapper
from langchain_community.tools.reddit_search.tool import RedditSearchSchema
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
import yfinance as yf


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
@tool
def get_stock_information(symbol: str):
    """Get the last 100 days of stock information of a stock symbol"""
    response = AlphaVantageAPIWrapper()._get_time_series_daily(symbol)
    return response

rd_tools = [
        RedditSearchRun(
            api_wrapper=RedditSearchAPIWrapper(
                reddit_client_id=os.getenv("client_id"),
                reddit_client_secret=os.getenv("client_secret"),
                reddit_user_agent=os.getenv("user_agent"),
            )
        )
]



yh_tools = [YahooFinanceNewsTool()]

@tool
def save_to_vec_db(response: str):
    """Save agent response to a vector database."""
    vector = embeddings.embed_query(response)

    index = pc.Index('top-stocks-daily')
    index.upsert([(response[:20], vector, {response})])  
    return 'Saved to vec db'


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
        max_results=10,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
        include_domains=[
            "https://finance.yahoo.com/markets/stocks/most-active/",
            "https://finance.yahoo.com/markets/stocks/trending/",
            "https://finance.yahoo.com/markets/stocks/52-week-gainers/"
        ],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )

def get_stock_data(ticker):
    """Fetches real-time stock data from Yahoo Finance."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    return {
        "ticker": ticker,
        "price": data['Close'].iloc[-1] if not data.empty else None,
        "volume": data['Volume'].iloc[-1] if not data.empty else None,
        "52_week_high": stock.info.get("fiftyTwoWeekHigh"),
        "52_week_low": stock.info.get("fiftyTwoWeekLow"),
        "market_cap": stock.info.get("marketCap"),
        "pe_ratio": stock.info.get("trailingPE"),
        "dividend_yield": stock.info.get("dividendYield"),
    }


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

web_search_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="web_search_agent",
    prompt="You are a financial data researcher with access to up-to-date stock market information. Your task is to search for and retrieve data on trending stocks, most active stocks, and stocks with significant 52-week gains. For each stock, collect the stock symbol, current price, and basic company information. Do not analyze the data or make recommendations - focus solely on gathering accurate, comprehensive information."
)

rd_agent = create_react_agent(
    model=model,
    name="reddit_agent",
    tools=rd_tools,
    prompt="You are a social media data collector focused on stock discussions. Search Reddit for mentions and discussions about stocks identified by the web search agent. Document the frequency of mentions, general sentiment trends, and common discussion topics. Do not interpret this data or draw conclusions - simply collect and organize the raw social sentiment data."
)

get_stock_info_agent = create_react_agent(
    model=model,
    name="get_stock_info_agent",
    tools=[get_stock_information],
    prompt="You are a technical data collector. Using the stock symbols provided, retrieve the following data: _get_time_series_daily and _get_time_series_weekly over the last 100 data points. Also collect 50-day and 200-day moving averages, RSI values, trading volumes, and other technical indicators. Present this as raw data without interpretation or analysis."
)

yh_agent = create_react_agent(
    name="yh_agent",
    model=model,
    tools=yh_tools,
    prompt="You are a financial news data collector. For each stock symbol identified, gather the latest news headlines, publication dates, sources, and brief article summaries. Document recent analyst ratings changes, earnings report dates, and any major company announcements. Collect this information without analyzing its impact or significance."
)

compiler_agent = create_react_agent(
    model=model,
    name="compiler_agent",
    tools=[],
    prompt="You are a data compilation specialist. Compile all the raw data collected by the research agents into a comprehensive, well-structured table. The table should include columns for: Stock Symbol, Company Name, Current Price, 52-Week Change (%), Technical Indicators (RSI, MAs), Trading Volume, Key Fundamentals (P/E, Market Cap), Recent News Headlines, and Social Media Mention Frequency. Ensure the table is properly formatted and contains only factual data without any analysis, recommendations, or interpretations."
)


# Long-Term, Low-Risk Investor (Conservative Wealth Builder)  
agent_lli = create_react_agent(
    model=model,
    tools=[],
    name="research_expert_lli",
    prompt="As an AI financial assistant for a long-term, low-risk investor,"
    "your goal is to recommend stable and reliable investment options with a"
    "strong history of steady growth and minimal volatility. "
    "Fetch real-time stock data before making recommendations. "
    "Use metrics like P/E ratio, market cap, and dividend yield to identify strong candidates."
    "Using the given data, you have to"
    "Focus on blue-chip stocks,"
    "ETFs, and dividend-paying companies with solid fundamentals. Prioritize assets with low debt,"
    "high profitability, and a strong competitive moat. Avoid speculative stocks, volatile assets,"
    "and high-risk investments. Analyze historical performance, financial statements,"
    "and macroeconomic trends before making recommendations."
    "Example Investments:"
    " - S&P 500 ETFs (VOO, VTI)"
    " - Dividend Aristocrats (JNJ, KO, PG)"
    " - Government Bonds & REITs"
)

agent_lhi = create_react_agent(
    model=model,
    tools=[],
    name="research_expert_lhi",
    prompt="Long-Term, High-Risk Investor (Growth-Oriented)"
    "As an AI financial advisor for a long-term, high-risk investor,"
    "focus on identifying companies and sectors with high growth potential."
    "Using the given data, you have to"
    "Analyze disruptive technologies, AI, biotech, and innovative startups."
    "Evaluate revenue growth rates, scalability, and market trends to suggest investments."
    "While risk is acceptable, prioritize companies with a competitive edge, strong management,"
    "and long-term sustainability. Consider future trends like AI, renewable energy, and blockchain."
    "Provide risk assessments, but allow for high volatility investments."
    "Example Investments:"
    " - Growth Stocks (NVDA, TSLA, AMZN)"
    " - AI & Tech Startups"
    " - Cryptocurrencies & Blockchain ETFs"
)

agent_sli = create_react_agent(
    model=model,
    tools=[],
    name="research_expert_sli",
    prompt="Short-Term, Low-Risk Investor (Safe Trader)"
    "As an AI trading assistant for a short-term, low-risk investor,"
    "Using the given data,"
    "your task is to identify safe, short-term opportunities with low volatility."
    "Focus on short-term bonds, defensive stocks, and index fund ETFs."
    "Use market trend analysis to find steady assets that provide predictable,"
    "low-risk returns within a 6-month to 2-year horizon. Avoid speculative trades and highly volatile stocks."
    "Incorporate macroeconomic indicators such as interest rates and inflation trends into investment decisions."
    "Example Investments:"
    " - Short-Term Treasury Bonds (SHY, BIL)"
    " - Defensive Stocks (Consumer Staples, Healthcare)"
    " - Low-Volatility ETFs"
)

agent_shi = create_react_agent(
    model=model,
    tools=[],
    name="research_expert_shi",
    prompt="Short-Term, High-Risk Investor (Aggressive Trader)."
    "As an AI trading assistant for a short-term, high-risk investor,"
    "your goal is to find high-potential short-term trades with significant upside."
    "Use technical indicators like RSI, MACD, and moving averages to identify breakout stocks and"
    "momentum trades. Prioritize high-volatility sectors such as tech, biotech, and"
    "cryptocurrencies. Incorporate market sentiment analysis, earnings reports, and"
    "macroeconomic news to optimize trade timing. Suggest risk management strategies,"
    "including stop-loss and position sizing."
    "Example Investments:"
    " - Meme Stocks & IPOs"
    " - High-Beta Growth Stocks (Tesla, Palantir)"
    " - Crypto & Options Trading"
)


agent_moderator = create_react_agent(
    model=model,
    tools=[get_stock_data],
    name="analytics_moderator",
    prompt="As the moderator of an AI-powered financial analytics debate team, "
    "you must verify whether stock recommendations are supported by real-time data. "
    "Check market trends, P/E ratios, and volatility before finalizing an investment strategy."
)

# Create supervisor workflow
research_team = create_supervisor(
    [web_search_agent, yh_agent, rd_agent, get_stock_info_agent, compiler_agent],
    model=model,
    prompt=(
        "You are a research coordinator managing a team of specialized data collection agents. Your role is to efficiently coordinate these agents to gather comprehensive stock market data.\n\n"
        "1. Always get the top 20 stocks from trending, active stocks and 52-week performance metrics and focus solely on data collection:\n"
        "2. For each identified stock, task the get_stock_info_agent to retrieve technical data and historical price information.\n"
        "3. Simultaneously, have the yh_agent collect all recent news headlines and analyst actions.\n"
        "4. Direct the reddit_agent to gather data on social media mentions and discussion volumes.\n"
        "5. Finally, have the compiler_agent organize all collected data into a comprehensive table.\n\n"
        "The final output must be a factual data table containing all relevant stock information without any analysis, recommendations, or interpretations. Ensure all data points are properly labeled and organized for easy transfer to an analysis team. Your task is complete when you have delivered comprehensive, organized raw data on the requested stocks."
    ),
).compile(name="research_team")

debate_team = create_supervisor(
    [agent_lli, agent_lhi, agent_sli, agent_shi, agent_moderator],
    model=model,
    prompt="Manage an AI-powered financial analytics debate team with real-time market data validation. "
    "Ensure recommendations are fact-checked against live stock data before finalizing an investment strategy."
).compile(name="debate_team")

main_supervisor = create_supervisor(
    [research_team, debate_team],
    supervisor_name="main_supervisor",
    model=model,
    prompt="You are the main supervisor and have a research and debate team under you. Your primary purpose is to manage these teams and their respective agents to research stocks and provide the user with a detailed analysis of the stock recommendations"
)

app = main_supervisor.compile()
