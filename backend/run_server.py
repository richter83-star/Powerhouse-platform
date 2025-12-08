"""
Simple script to run the FastAPI server.
"""
import sys
sys.path.insert(0, '/home/ubuntu/powerhouse_b2b_platform/backend')

if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
