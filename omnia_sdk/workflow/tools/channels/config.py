from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

INFOBIP_API_KEY = config("INFOBIP_API_KEY", cast=Secret, default="")
INFOBIP_BASE_URL = config("INFOBIP_BASE_URL", cast=str, default="https://api2.infobip.net")
