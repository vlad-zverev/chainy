import faulthandler

from src.http.server import app
from src.utils import get_env_var

faulthandler.enable()

HOST = get_env_var('HOST', '0.0.0.0')
PORT = get_env_var('PORT', 5000)
DEBUG = bool(get_env_var('DEBUG', 0))

app.run(host=HOST, port=PORT, debug=DEBUG)
