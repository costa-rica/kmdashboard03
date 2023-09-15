from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
from flask_login import login_required, login_user, logout_user, current_user
import os
import logging
from logging.handlers import RotatingFileHandler
import jinja2
from app_package.bp_main.utils import create_categories_xlsx, existing_report
from km03_models import sess, engine, text, Base, Users, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import shutil

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
    if request.method == 'POST':
        # session.permanent = True
        formDict = request.form.to_dict()
        # print(f"formDict: {formDict}")
        # login_as_guest = formDict.get('login_as_guest')
        # print(login_as_guest)

        guest_user = sess.query(Users).filter_by(email=current_app.config.get('GUEST_EMAIL')).first()
        login_user(guest_user)
        return redirect(url_for('bp_main.user_home'))

    return render_template('main/home.html')

@bp_main.route("/user_home", methods=["GET","POST"])
def user_home():
    logger_bp_main.info(f"-- in user_home page route --")
    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))

    logger_bp_main.info(f"- DIR_DB_FILES_UTILITY: {current_app.config.get('DIR_DB_FILES_UTILITY')}")
    logger_bp_main.info(f"- DIR_DB_FILES_UTILTIES_TEST: {current_app.config.get('DIR_DB_FILES_UTILTIES_TEST')}")
    return render_template('main/user_home.html')



# Custom static data
@bp_main.route('/<dir_name>/<filename>')
def recall_or_investigation_file(dir_name, filename):
    # print("-- enterd custom static -")
    # name_no_spaces = ""
    # dir_name = 
    
    return send_from_directory(os.path.join(current_app.config.get('DB_ROOT'),"files", dir_name), filename)



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



########################
####### Reports ########
########################

@bp_main.route("/reports", methods=["GET","POST"])
@login_required
def reports():
    excel_file_name_inv='investigation_report.xlsx'
    excel_file_name_re='recalls_report.xlsx'
    
    #get columns from each reports
    #Id/RECORD_ID removed from options -- if not included causes problems building excel file
    column_names_inv=Investigations.__table__.columns.keys()[1:]
    column_names_re=Recalls.__table__.columns.keys()[1:]

    categories_dict_inv={}
    categories_dict_re={}
    if os.path.exists(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],excel_file_name_inv)):
        categories_dict_inv,time_stamp_inv=existing_report(excel_file_name_inv, 'investigations')
        # print('categories_dict_inv:::', type(categories_dict_inv), categories_dict_inv)
    else:
        time_stamp_inv='no current file'
    if os.path.exists(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],excel_file_name_re)):
        categories_dict_re,time_stamp_re=existing_report(excel_file_name_re,'recalls')
    else:
        time_stamp_re='no current file'

    print('categories_dict_inv:::',categories_dict_inv)
    # print('time_stamp_inv_df:::', time_stamp_inv, type(time_stamp_inv))
    if request.method == 'POST':
        print("---- POST ---- ")
        formDict = request.form.to_dict()
        print('reports - formDict::::',formDict)
        # print("--------- ")
        if formDict.get('build_excel_report_inv'):
            
            column_names_for_df = [i for i in column_names_inv if i in list(formDict.keys())]
            
            column_names_for_df.insert(0,'id')
            print('column_names_for_df:::',column_names_for_df)
            create_categories_xlsx(excel_file_name_inv, column_names_for_df, formDict, 'investigations')
            
        elif formDict.get('build_excel_report_re'):
            column_names_for_df=[i for i in column_names_re if i in list(formDict.keys())]
            column_names_for_df.insert(0,'RECORD_ID')
            create_categories_xlsx(excel_file_name_re, column_names_for_df, formDict, 'recalls')
        # logger_bp_inv.info('in search page')
        # return redirect(url_for('bp_admin.reports'))
        return redirect(request.url)
    return render_template('main/reports.html', excel_file_name_inv=excel_file_name_inv, time_stamp_inv=time_stamp_inv,
        column_names_inv=column_names_inv,column_names_re=column_names_re, categories_dict_inv=categories_dict_inv,
        categories_dict_re=categories_dict_re,time_stamp_re=time_stamp_re, excel_file_name_re=excel_file_name_re)



@bp_main.route("/files_zip", methods=["GET","POST"])
@login_required
def files_zip():
    if os.path.exists(os.path.join(current_app.config['DIR_DB_FILES_UTILITY'],'Investigation_files')):
        os.remove(os.path.join(current_app.config['DIR_DB_FILES_UTILITY'],'Investigation_files'))
    shutil.make_archive(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],'Investigation_files'), "zip", os.path.join(
        current_app.config['DIR_DB_FILES']))

    return send_from_directory(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY']),'Investigation_files.zip', as_attachment=True)

