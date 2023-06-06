from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
from flask_login import login_required, login_user, logout_user, current_user
import os
import logging
from logging.handlers import RotatingFileHandler


bp_main = Blueprint('bp_main', __name__)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_bp_main = logging.getLogger(__name__)
logger_bp_main.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),'logs','bp_main.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

logger_bp_main.addHandler(file_handler)
logger_bp_main.addHandler(stream_handler)


@bp_main.route("/", methods=["GET","POST"])
def home():
    logger_bp_main.info(f"-- in home page route --")

    # #Build db
    # if os.path.exists(os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))):
    #     print(f"db already exists: {os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))}")
    # else:
    #     Base.metadata.create_all(engine)
    #     print(f"NEW db created: {os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))}")

    return render_template('main/home.html')

@bp_main.route("/user_home", methods=["GET","POST"])
def user_home():
    logger_bp_main.info(f"-- in user_home page route --")
    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))
    # #Build db
    # if os.path.exists(os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))):
    #     print(f"db already exists: {os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))}")
    # else:
    #     Base.metadata.create_all(engine)
    #     print(f"NEW db created: {os.path.join(os.environ.get('DB_ROOT'),os.environ.get('DB_NAME'))}")

    return render_template('main/user_home.html')


