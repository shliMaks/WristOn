from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

pages_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@pages_router.get("/")
async def welcome_page(request: Request):
    return templates.TemplateResponse(request=request, name="main-page.html")


# Заглушка для браузерів, які автоматично шукають favicon.ico в корені
@pages_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.svg")
