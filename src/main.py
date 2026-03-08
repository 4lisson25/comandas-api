from fastapi import FastAPI
from src.settings import HOST, PORT, RELOAD
import uvicorn
# import das classes com as rotas/endpoints
from src.routers import FuncionarioRouter
from src.routers import ClienteRouter
from src.routers import ProdutoRouter
app = FastAPI()
# mapeamento das rotas/endpoints
app.include_router(FuncionarioRouter.router)
app.include_router(ClienteRouter.router)
app.include_router(ProdutoRouter.router)

if __name__ == "__main__":
    uvicorn.run('main:app', host=HOST, port=int(PORT), reload=RELOAD)