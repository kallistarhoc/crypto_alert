import os

class Config:
    SECRET_KEY = os.urandom(24)
    # Database Configuration
    DB_NAME = "database.db"

    # Mail Configuration
    MAIL_SERVER = "sandbox.smtp.mailtrap.io"
    MAIL_PORT = 2525
    MAIL_USERNAME = "0175f0790c03d2"
    MAIL_PASSWORD = "8c9d119700267c"
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # CoinAPI Configuration
    COINAPI_API_KEY = "CA2C99A8-9F7E-47A4-9B44-1F6FA1C81AED"

    # Other Configurations
    DEBUG = True

    HEADERS = {
    "X-CoinAPI-Key": COINAPI_API_KEY,
    "Accept": "application/json",
    "Accept-Encoding": "deflate, gzip",
}



class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


config = DevelopmentConfig() if os.environ.get("FLASK_ENV") == "development" else ProductionConfig()
