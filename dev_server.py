from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

app = Starlette()
app.mount('/', StaticFiles(directory='./'))
app.add_middleware(CORSMiddleware, allow_origins='*')