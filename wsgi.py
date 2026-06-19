import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['SECRET_KEY'] = 'cheers-club-secret-2024'

from app import create_app
application = create_app()
