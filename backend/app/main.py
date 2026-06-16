from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, stripe_router, shopify_router
from app.routers import quickbooks_router, reconciliation, discrepancies, reports
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title='ReconFlow API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(stripe_router.router)
app.include_router(shopify_router.router)
app.include_router(quickbooks_router.router)
app.include_router(reconciliation.router)
app.include_router(discrepancies.router)
app.include_router(reports.router)


@app.get('/health')
def health(): return {'status': 'ok'}
