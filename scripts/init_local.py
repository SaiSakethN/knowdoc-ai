"""Initialize ignored local settings without displaying secrets."""
import secrets
from pathlib import Path

path = Path('.env')
if path.exists():
    print('.env already exists; preserved.')
else:
    password = secrets.token_hex(24)
    path.write_text(Path('.env.example').read_text().replace('replace-with-a-long-random-local-password', password))
    print('Created ignored .env with random local database credentials.')
