from fastapi import APIRouter
from routers.pages import pages_router
from routers.api import api_router

router_handler = APIRouter()
router_handler.include_router(pages_router)
router_handler.include_router(api_router)
