from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import agents, alerts, audit_events, auth, dashboard, reports, settings as settings_routes, systems, users, workspaces


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Sentinel Link API", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(agents.router)
app.include_router(systems.router)
app.include_router(audit_events.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(settings_routes.router)
app.include_router(dashboard.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok"}
