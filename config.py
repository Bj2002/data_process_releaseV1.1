import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-me'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-hardcode'
    UPLOAD_ALLOWED_EXT = {'zip'}
    UPLOAD_TMP_DIR = os.path.join(BASE_DIR, 'tmp_uploads')
    FUNCTIONS_DIR = os.path.join(BASE_DIR, 'functions')