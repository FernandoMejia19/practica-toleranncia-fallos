import socket
import platform
from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Notification Service",
    version="1.0"
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "service": "notifications-service",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "service": "notifications-service",
        "status": "healthy"
    }

@app.get("/server")
def server():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except Exception:
        hostname = "unknown"
        ip_address = "127.0.0.1"
    return {
        "service": "notifications-service",
        "hostname": hostname,
        "ip": ip_address,
        "os": platform.system()
    }
