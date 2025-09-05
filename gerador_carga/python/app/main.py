import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Request

from gerador_carga.python.app.gateways.datas_generator import generate_data
from gerador_carga.python.app.schemas.schemas import split_and_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("api")

UPDATE_INTERVAL_SECONDS = int(os.getenv("UPDATE_INTERVAL_SECONDS", "0"))


# --------- Wrapper que lida com sync/async ---------
async def call_generate_data():
    import inspect
    if inspect.iscoroutinefunction(generate_data):
        return await generate_data()                  # async
    return await asyncio.to_thread(generate_data)     # sync


# --------- Tarefas de atualização ---------
async def run_generate_data_once(app: FastAPI) -> None:
    logger.info("Fetching data (generate_data)...")
    raw = await call_generate_data()
    logger.info("Normalizing data with split_and_models...")
    norm = split_and_models(raw)
    app.state.latest_raw = raw
    app.state.latest_norm = norm
    logger.info("Data fetched and normalized successfully.")


async def periodic_updater(app: FastAPI, interval: int) -> None:
    try:
        while True:
            await run_generate_data_once(app)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Periodic updater cancelled.")
        raise


# --------- Ciclo de vida ---------
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.latest_raw: Optional[Dict[str, Any]] = None
    app.state.latest_norm: Optional[Dict[str, Any]] = None

    # roda uma vez no startup
    await run_generate_data_once(app)

    # se quiser atualização periódica
    task = None
    if UPDATE_INTERVAL_SECONDS > 0:
        task = asyncio.create_task(periodic_updater(app, UPDATE_INTERVAL_SECONDS))

    try:
        yield
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


# --------- Criação do app ---------
def create_app() -> FastAPI:
    app = FastAPI(
        title="API",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/data")
    async def data(request: Request):
        # retorna normalizado
        return request.app.state.latest_norm or {}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=False,
        log_level="info",
    )
