import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CATNAME_URL = os.environ.get("CATNAME_URL")
CATLOG_URL = os.environ.get("CATLOG_URL")
GOOGLE_FORM = os.environ.get("GOOGLE_FORM")
CAT_WEIGHT_URL = os.environ.get("CAT_WEIGHT_URL")