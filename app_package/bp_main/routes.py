from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
from flask_login import login_required, login_user, logout_user, current_user
import os
import logging
from logging.handlers import RotatingFileHandler
import jinja2


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

@bp_main.before_request
def before_request():
    logger_bp_main.info(f"-- ***** in before_request route --")
    ###### TEMPORARILY_DOWN: redirects to under construction page ########
    if os.environ.get('TEMPORARILY_DOWN') == '1':
        if request.url != request.url_root + url_for('bp_main.temporarily_down')[1:]:
            # logger_bp_users.info("*** (logger_bp_users) Redirected ")
            logger_bp_main.info(f'- request.referrer: {request.referrer}')
            logger_bp_main.info(f'- request.url: {request.url}')
            return redirect(url_for('bp_main.temporarily_down'))

@bp_main.route("/", methods=["GET","POST"])
def home():
    logger_bp_main.info(f"-- in home page route --")


    return render_template('main/home.html')

@bp_main.route("/user_home", methods=["GET","POST"])
def user_home():
    logger_bp_main.info(f"-- in user_home page route --")
    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))


    return render_template('main/user_home.html')


@bp_main.route("/temporarily_down", methods=["GET","POST"])
def temporarily_down():
    logger_bp_main.info(f"-- in temporarily_down page route --")
    # if not current_user.is_authenticated:
    #     return redirect(url_for('bp_main.home'))


    return render_template('main/temporarily_down.html')



@bp_main.route("/test_404", methods=["GET","POST"])
def test_404():
    raise FileNotFoundError("File not found") 

@bp_main.route("/test_404_2", methods=["GET","POST"])
def test_404_2():
    abort(404) 

@bp_main.route("/test_undef", methods=["GET","POST"])
def test_undef():
    try:
        undefined_variable = some_undefined_variable
    except NameError:
        raise jinja2.exceptions.UndefinedError("Variable is undefined")

@bp_main.route("/test_error", methods=["GET","POST"])
def test_error():
    raise AttributeError("This is a custom AttributeError")

