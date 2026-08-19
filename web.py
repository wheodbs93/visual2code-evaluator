import os
from app.server import serve

host = "0.0.0.0"
port = int(os.getenv("PORT", "8080"))

serve(host, port)
