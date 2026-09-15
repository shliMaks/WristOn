from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.main_router import router_handler

app = FastAPI(title="WristOn")
app.include_router(router_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
