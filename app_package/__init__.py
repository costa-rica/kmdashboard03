from flask import Flask
# from app_package.config import config
from ._common.config import config
import os
import logging
from logging.handlers import RotatingFileHandler
from pytz import timezone
from datetime import datetime
from km03_models import Base, engine
from ._common.utilities import login_manager, custom_logger_init, \
    before_request_custom, teardown_request
from flask_mail import Mail

if not os.path.exists(os.path.join(os.environ.get('WEB_ROOT'),'logs')):
    os.makedirs(os.path.join(os.environ.get('WEB_ROOT'), 'logs'))

# timezone 
def timetz(*args):
    return datetime.now(timezone('Europe/Paris') ).timetuple()

logging.Formatter.converter = timetz

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_init = logging.getLogger('__init__')
logger_init.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),'logs','__init__.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

stream_handler_tz = logging.StreamHandler()

logger_init.addHandler(file_handler)
logger_init.addHandler(stream_handler)

logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').addHandler(file_handler)

logger_init.info(f"--- Starting Flask KM Dashboard03 NHTSA---")
# TEMPORARILY_DOWN = "ACTIVE" if os.environ.get('TEMPORARILY_DOWN') == "1" else "inactive"
# # TEMPORARILY_DOWN=1
# logger_init.info(f"- TEMPORARILY_DOWN: {TEMPORARILY_DOWN}")
logger_init.info(f"- SQL_URI: sqlite:///{config.DB_ROOT}{config.DB_NAME}")


mail = Mail()

def create_app(config_for_flask = config):
    app = Flask(__name__)
    app.before_request(before_request_custom)
    app.teardown_request(teardown_request)
    app.config.from_object(config_for_flask)
    login_manager.init_app(app)
    mail.init_app(app)

    ############################################################################
    ## create folders for PROJECT_RESOURCES
    create_folder(config_for_flask.PROJECT_RESOURCES)
    create_folder(config_for_flask.DB_ROOT)

    create_folder(config_for_flask.DIR_DB_FILES_TEMPORARY)
    create_folder(config_for_flask.DIR_DB_FILES_UTILITY)
    create_folder(config_for_flask.DIR_DB_QUERIES)

    #Build db
    database_path_and_name = os.path.join(config_for_flask.DB_ROOT,config_for_flask.DB_NAME)
    if os.path.exists(database_path_and_name):
        print(f"db already exists: {database_path_and_name}")
    else:
        Base.metadata.create_all(engine)
        print(f"NEW db created: {database_path_and_name}")
    # create_folder(config_for_flask.DIR_LOGS)
    # # website files
    # create_folder(config_for_flask.WEBSITE_FILES)
    # create_folder(config_for_flask.DIR_WEBSITE_UTILITY_IMAGES)
    # create_folder(config_for_flask.DIR_WEBSITE_VIDEOS)
    # create_folder(config_for_flask.DB_UPLOAD)
    # # user files
    # create_folder(config_for_flask.USER_FILES)
    # create_folder(config_for_flask.DAILY_CSV)
    # create_folder(config_for_flask.RAW_FILES_FOR_DAILY_CSV)
    ############################################################################


    from app_package.bp_main.routes import bp_main
    from app_package.bp_users.routes import bp_users
    from app_package.bp_admin.routes import bp_admin
    from app_package.bp_investigations.routes import bp_investigations
    from app_package.bp_recalls.routes import bp_recalls
    from app_package.bp_error.routes import bp_error

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_investigations)
    app.register_blueprint(bp_recalls)
    app.register_blueprint(bp_error)

    return app

def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger_init.info(f"created: {folder_path}")

