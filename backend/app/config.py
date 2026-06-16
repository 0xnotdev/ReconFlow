from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_CLIENT_ID: str = ""
    SHOPIFY_API_KEY: str
    SHOPIFY_API_SECRET: str
    SHOPIFY_REDIRECT_URI: str = ""
    QUICKBOOKS_CLIENT_ID: str
    QUICKBOOKS_CLIENT_SECRET: str
    QUICKBOOKS_REDIRECT_URI: str = ""
    OPENROUTER_API_KEY: str
    SECRET_KEY: str = 'change-me-in-production'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    class Config:
        env_file = ('.env', 'backend/.env')

settings = Settings()
