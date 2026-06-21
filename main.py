"""
Main entry point - Run the FastAPI server
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Story-to-Scene Generator API Server...")
    print("API will be available at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)