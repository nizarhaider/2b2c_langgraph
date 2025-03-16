import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

from react_agent.graph_ import create_graph
from react_agent.types import ChatInputType

# Load environment variables from .env file
load_dotenv()


def start() -> None:
    app = FastAPI(
        title="Travel Buddy",
        version="1.0",
        description="A simple api server using Langchain's Runnable interfaces",
    )

    # Configure CORS
    origins = [
        "http://localhost",
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    graph = create_graph()

    runnable = graph.with_types(input_type=ChatInputType, output_type=dict)

    add_routes(app, runnable, path="/chat", playground_type="default")
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=6969)

if __name__ == "__main__":
    start()