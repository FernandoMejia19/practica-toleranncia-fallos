import socket
import platform
from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Reservation Service",
    version="2.0"
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "service": "reservation-service",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "service": "reservation-service",
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
        "service": "reservation-service",
        "hostname": hostname,
        "ip": ip_address,
        "os": platform.system()
    }