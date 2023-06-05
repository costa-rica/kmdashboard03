from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory, jsonify
from app_package import mail
from km03_models import sess, engine, text, Base, Users, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
# from PIL import Image
from datetime import datetime, date, time
import datetime
from sqlalchemy import func, desc
import pandas as pd
import io
from wsgiref.util import FileWrapper
import xlsxwriter
from flask_mail import Message
from app_package.bp_recalls.utils import recalls_query_util, queryToDict, \
    update_recall,  column_names_dict_re_util, \
    column_names_re_util
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import shutil
from app_package.bp_users.forms import RegistrationForm, LoginForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm
import re
# import logging
from app_package.bp_investigations.utils_general import category_list_dict_util, remove_category_util, \
    search_criteria_dictionary_util,record_remover_util, track_util, update_files_util
from app_package.bp_recalls.forms import ReForm

import logging
from logging.handlers import RotatingFileHandler



#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_main = logging.getLogger(__name__)
logger_main.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('WEB_ROOT'),"logs",'bp_recalls.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_main.addHandler(file_handler)
logger_main.addHandler(stream_handler)

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# file_handler = logging.FileHandler('app_package_bp_recalls_log.txt')
# logger.addHandler(file_handler)
# logger = logging.getLogger(__name__)

# this_app = create_app()
# this_app.logger.addHandler(file_handler)

bp_recalls = Blueprint('bp_recalls', __name__)


@bp_recalls.route("/search_recalls", methods=["GET","POST"])
@login_required
def search_recalls():
    print('*TOP OF def search_recalls()*')
    logger.info('in search_recalls page')
    category_list =[y for x in category_list_dict_util().values() for y in x]
    column_names=column_names_re_util()
    column_names_dict=column_names_dict_re_util()
    limit_flag=request.args.get('limit_flag')
    
    if request.args.get('category_dict'):
        category_dict=request.args.get('category_dict')
    else:
        category_dict={'category1':''}
    
    #user_list for searching userlist
    user_list=sess.query(Tracking_re.updated_to).filter(Tracking_re.field_updated=='verified_by_user').distinct().all()
    user_list=[i[0] for i in user_list]
    
    #Get/identify query to run for table
    if request.args.get('query_file_name'):
        query_file_name=request.args.get('query_file_name')
        print('query_file_name:::', query_file_name)
        recalls_query, search_criteria_dictionary, category_dict = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True
    elif request.args.get('no_hits_flag')==True:
        recalls_query, search_criteria_dictionary = ([],{})
    else:
        query_file_name= 'default_query_re.txt'
        recalls_query, search_criteria_dictionary, category_dict = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True        
    
    #Make recalls to dictionary for bit table bottom of home screen
    recalls_data = queryToDict(recalls_query, column_names)#List of dicts each dict is row
    
    print('limit_flag::::',limit_flag)
    #if limit flag
    if limit_flag=='true':
        print('limit_flag:::: FIRED?', limit_flag)
        recall_data_list=recalls_data[:100]
    else:
        print('limit_flag NOT fired')
        recall_data_list=recalls_data
        
    

    #make make_list drop down options
    with open(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'make_list_recalls.txt')) as json_file:
        make_list=json.load(json_file)
        json_file.close()

    if request.method == 'POST':
        print('!!!!in POST method no_hits_flag:::', no_hits_flag)
        formDict = request.form.to_dict()
        limit_flag=formDict.get('limit_flag')
        if formDict.get('refine_search_button'):
            print('@@@@@@ refine_search_button')
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_re.txt')
            return redirect(url_for('bp_recalls.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                limit_flag=limit_flag))
      
        elif formDict.get('view'):
            re_id_for_dash=formDict.get('view')
            return redirect(url_for('bp_recalls.recalls_dashboard',re_id_for_dash=re_id_for_dash))
        elif formDict.get('add_category'):
            new_category='sc_category' + str(len(category_dict)+1)
            formDict[new_category]=''
            # del formDict['add_category']
            # formDict['add_category']=''
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_re.txt')
            return redirect(url_for('bp_recalls.search_recalls', query_file_name=query_file_name,
                no_hits_flag=no_hits_flag, limit_flag=limit_flag))
        elif formDict.get('remove_category'):
            
            category_for_remove = 'sc_'+formDict['remove_category']
            # del category_dict[formDict['remove_category']]
            form_dict_cat_element = 'sc_' + formDict['remove_category']
            # print('form_dict_cat_element:::',form_dict_cat_element)
            
            del formDict[form_dict_cat_element]
            # print('formDict:::',formDict)
            
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_re.txt')
            return redirect(url_for('bp_recalls.search_recalls', query_file_name=query_file_name,
                no_hits_flag=no_hits_flag,limit_flag=limit_flag))
            
    return render_template('search_recalls.html',table_data = recall_data_list, 
        column_names_dict=column_names_dict, column_names=column_names,
        len=len, make_list = make_list, query_file_name=query_file_name,
        search_criteria_dictionary=search_criteria_dictionary,str=str,
        category_list=category_list,category_dict=category_dict,
        user_list=user_list, limit_flag=limit_flag)






@bp_recalls.route("/recalls_dashboard", methods=["GET","POST"])
@login_required
def recalls_dashboard():
    print('*TOP OF def dashboard()*')
    re_form=ReForm()
        
    #view, update
    if request.args.get('re_id_for_dash'):
        # print('request.args.get(re_id_for_dash, should build verified_by_list')
        re_id_for_dash = int(request.args.get('re_id_for_dash'))
        dash_re= sess.query(Recalls).get(re_id_for_dash)
        verified_by_list =sess.query(Tracking_re.updated_to, Tracking_re.time_stamp).filter_by(
            recalls_table_id=re_id_for_dash,field_updated='verified_by_user').all()
        verified_by_list=[[i[0],i[1].strftime('%Y/%m/%d %#I:%M%p')] for i in verified_by_list]
        # print('verified_by_list:::',verified_by_list)
    else:
        verified_by_list=[]

    #for viewing and deleting files
    current_re_files_dir_name = 'Recall_'+str(re_id_for_dash)
    current_re_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_re_files_dir_name)


    #pass check or no check for current_user
    if any(current_user.email in s for s in verified_by_list):
        checkbox_verified = 'checked'
    else:
        checkbox_verified = ''
    
    #FILES This turns the string in files column to a list if something exists
    if dash_re.files==''  or dash_re.files==None:
        dash_re_files=''
    else:
        dash_re_files=dash_re.files.split(',')
        
    #Categories from previous update
    if dash_re.categories=='' or dash_re.categories==None:
        dash_re_categories=''
        has_category_flag=False
        print('dash_re_categories - [None]:::',dash_re_categories)
    else:
        dash_re_categories=dash_re.categories.split(',')
        dash_re_categories=[i.strip() for i in dash_re_categories]
        has_category_flag=True
        print('dash_re_categories:::',dash_re_categories)
    
    
    #------start get linked reocrds----
    current_record_type='recalls'
    linked_record_type='recalls'
    id_for_dash=re_id_for_dash
    records_util=record_remover_util(current_record_type,linked_record_type,id_for_dash)
    
    records_array=records_util[0]#list for dropdown
    # insert list of choices for linked records -- entering dashbaord from search:
    re_form.records_list.choices = [(r.get('id'),r.get('shows_up')) for r in records_array]
    
    dash_re_linked_records=records_util[1] #list of linked records for dashboard
    #------End of linked reocrds----
    
    
    dash_re_BGMAN=None if dash_re.BGMAN==None else dash_re.BGMAN.strftime("%Y-%m-%d")
    dash_re_ODATE= None if dash_re.ODATE == None else dash_re.ODATE.strftime("%Y-%m-%d")
    dash_re_RCDATE=None if dash_re.RCDATE==None else dash_re.RCDATE.strftime("%Y-%m-%d")
    dash_re_DATEA=None if dash_re.DATEA==None else dash_re.DATEA.strftime("%Y-%m-%d")
    
    
    dash_re_list = [dash_re.RECORD_ID, dash_re.CAMPNO, dash_re.MAKETXT, dash_re.MODELTXT, dash_re.YEAR,
        dash_re.MFGCAMPNO, dash_re.COMPNAME, dash_re.MFGNAME, dash_re_BGMAN,
        dash_re.ENDMAN, dash_re.RCLTYPECD, dash_re.POTAFF, dash_re_ODATE,
        dash_re.INFLUENCED_BY, dash_re.MFGTXT, dash_re_RCDATE, #RCDATE is dash_re_list[15]
        dash_re_DATEA, dash_re.RPNO, dash_re.FMVSS, dash_re.DESC_DEFECT, dash_re.CONSEQUENCE_DEFCT,
        dash_re.CORRECTIVE_ACTION,dash_re.NOTES, dash_re.RCL_CMPT_ID,dash_re.km_notes,
        dash_re.date_updated.strftime('%Y/%m/%d %I:%M%p'), dash_re_files, dash_re_categories,
        dash_re_linked_records]
    print('dash_re_list[27]:::',dash_re_list[27])
    if 'FIRES_OTHER' in dash_re_list[27]:
        print('FIRES_OTHER is in dash_re_list[27]')

#files 24

    #Make lists for investigation_entry_top
    re_entry_top_names_list=['Record ID', 'CAMPNO', 'Make', 'Model', 'Year', 'MFGCAMPNO',
       'COMPNAME', 'Manufacturer Name', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
       'Open Date', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
       'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION', 'NOTES','RCL_CMPT_ID']
    

    re_entry_top_list=zip(re_entry_top_names_list[:19],dash_re_list[:19])
    re_entry_top2_list=zip(re_entry_top_names_list[19:],dash_re_list[19:])
    
    #make dictionary of category lists from excel file
    category_list_dict=category_list_dict_util()
    print('category_list_dict:::', category_list_dict)
    
    category_group_dict_no_space={i:re.sub(r"\s+","",i) for i in list(category_list_dict)}
    print('category_group_dict_no_space:::', category_group_dict_no_space)
    
    print('****category items found:')
    for category, no_space in category_group_dict_no_space.items():
        if category =='Fire Issues':
            print('--',category,'--')
            print(category_list_dict[category])
        for i in category_list_dict[category]:
            # if category == 'Fire Issues':
                # print('---->',i)
            # if i in dash_re_list[27]:
                # print(i)
            if i=='FIRES_OTHER':
                print('FIRES_OTHER -- found:')
                print(category)
            
    
    if request.method == 'POST':
        print('!!!!in POST method')
        formDict = request.form.to_dict()
        argsDict = request.args.to_dict()
        filesDict = request.files.to_dict()
        record_type=formDict['record_type']
        verified_by_list_util=[i[0] for i in verified_by_list]
        
        if formDict.get('update_re'):
            # print('formDict:::',formDict)
            # print('argsDict:::',argsDict)
            # print('filesDict::::',filesDict)
            # print('formsDict.Keys():::',formDict.keys())
            #update file
            if request.files.get('recall_file'):
                #updates file name in database
                
                update_from=dash_re.files 
                uploaded_file = request.files['recall_file']
                file_added_flag=update_files_util(filesDict, id_for_dash,'recall')
                
                if file_added_flag == 'file_added':
                    track_util('recalls', 'files',update_from, dash_re.files,re_id_for_dash)
                
            #Update triggered if 1) notes or verified user in formDict
            #2)'cat_' in formDict.keys()
            #3) if has_category_flag but no 'cat_' in formDict.keys()
            update_data_list=['re_km_notes','verified_by_user'] 
            if any(key in update_data_list for key in formDict.keys()) or any(
                'cat_' in key[:4] for key in formDict.keys()) or (
                has_category_flag and not any('cat_' in key[:4] for key in formDict.keys())):
                print('*****item in update_data_list and formDict.keys')
                print(':::formDict:::',formDict)
                update_recall(formDict, re_id_for_dash, verified_by_list_util)
            
            #This can only be case if update + user verified previously but no unchecked
            if (current_user.email in verified_by_list_util) and (
                formDict.get('verified_by_user')==None):
                sess.query(Tracking_re).filter_by(recalls_table_id=int(re_id_for_dash),
                    field_updated='verified_by_user',updated_to=current_user.email).delete()
                sess.commit()
            
            
            return redirect(url_for('bp_recalls.recalls_dashboard', re_id_for_dash=re_id_for_dash,
                current_re_files_dir_name=current_re_files_dir_name))
        
        elif formDict.get('link_record'):
            print('LINKED RECORD formDict:::::', formDict)
            record_list_item=formDict.get('records_list')
            record_list_id=record_list_item[:record_list_item.find('|')]
            #make list in current record to specified record ['type', 'id']
            current_to_specified={
                'record_type':formDict.get('record_type'),
                'record_id':formDict.get('records_list')
                }
            specified_to_current={
                'record_type':'recalls',
                'record_id':str(re_id_for_dash)
                }
                
            #if existing record has something in linked_records then convert to dict
            if dash_re.linked_records!=None and dash_re.linked_records!='':
                linked_records_dict_current=json.loads(dash_re.linked_records)
                linked_records_dict_current[formDict.get('record_type')+record_list_id]=current_to_specified
            else:
                linked_records_dict_current={formDict.get('record_type')+record_list_id:current_to_specified}
              

            
            #check if linked record has
            if formDict.get('record_type')=='investigations':
                #get query of linked record:
                dash_re_linked= sess.query(Investigations).get(int(record_list_id))
                if dash_re_linked.linked_records!=None and dash_re_linked.linked_records!='':
                    linked_records_dict_for_linked=json.loads(dash_re_linked.linked_records)
                    linked_records_dict_for_linked['recalls'+str(re_id_for_dash)]=specified_to_current
                else:
                    linked_records_dict_for_linked={'recalls'+str(re_id_for_dash):specified_to_current}
            elif formDict.get('record_type')=='recalls':
                #get query of linked record:
                dash_re_linked= sess.query(Recalls).get(int(record_list_id))
                if dash_re_linked.linked_records!=None and dash_re_linked.linked_records!='':
                    linked_records_dict_for_linked=json.loads(dash_re_linked.linked_records)
                    linked_records_dict_for_linked['recalls'+str(re_id_for_dash)]=specified_to_current
                else:
                    linked_records_dict_for_linked={'recalls'+str(re_id_for_dash):specified_to_current}
                    
            #add list to current record db linked_record
            dash_re.linked_records=json.dumps(linked_records_dict_current)
            dash_re_linked.linked_records=json.dumps(linked_records_dict_for_linked)
            sess.commit()
            
            
            return redirect(url_for('bp_recalls.recalls_dashboard', record_type=record_type, 
                re_id_for_dash=re_id_for_dash,current_re_files_dir_name=current_re_files_dir_name))
        
        
        
        
    return render_template('dashboard_re.html',re_entry_top_list=re_entry_top_list,
        dash_re_list=dash_re_list, str=str, len=len, re_id_for_dash=re_id_for_dash,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, int=int, 
        category_list_dict=category_list_dict, list=list,
        category_group_dict_no_space=category_group_dict_no_space, re_entry_top2_list=re_entry_top2_list,
        current_re_files_dir_name=current_re_files_dir_name, re_form=re_form,
        records_array=records_array)



@bp_recalls.route("/delete_file_re/<re_id_for_dash>/<filename>", methods=["GET","POST"])
# @posts.route('/post/<post_id>/update', methods = ["GET", "POST"])
@login_required
def delete_file_re(re_id_for_dash,filename):
    #update Investigations table files column
    dash_re =sess.query(Recalls).get(re_id_for_dash)
    update_from=dash_re.files
    print('delete_file route - dash_re::::',dash_re.files)
    file_list=''
    
    if (",") in dash_re.files and len(dash_re.files)>1:
        file_list=dash_re.files.split(",")
        file_list.remove(filename)
    dash_re.files=''
    sess.commit()
    if len(file_list)>0:
        for i in range(0,len(file_list)):
            if i==0:
                dash_re.files = file_list[i]
            else:
                dash_re.files = dash_re.files +',' + file_list[i]
    sess.commit()
        
    #update tracking
    track_util('recalls', 'files',update_from,dash_re.files,re_id_for_dash)
    # newTrack=Tracking_re(field_updated='files',
        # updated_to=dash_re.files, updated_by=current_user.id,
        # recalls_table_id=re_id_for_dash)
    # sess.add(newTrack)
    # sess.commit()
    
    #Remove files from files dir
    # current_re_files_dir_name = str(dash_re.RECORD_ID) + '_'+str(re_id_for_dash)
    current_re_files_dir_name = 'Recall_'+str(re_id_for_dash)
    current_re_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_re_files_dir_name)
    files_dir_and_filename=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'],
        current_re_files_dir_name, filename)
    
    if os.path.exists(files_dir_and_filename):
        os.remove(files_dir_and_filename)
    
    if len(os.listdir(current_re_files_dir))==0:
        os.rmdir(current_re_files_dir)
    
    flash('file has been deleted!', 'success')
    return redirect(url_for('bp_recalls.recalls_dashboard', re_id_for_dash=re_id_for_dash))
























@bp_recalls.route('/get_record_recall/<record_type>/<re_id_for_dash>')
@login_required
def get_record_recall(record_type,re_id_for_dash):
    
    current_record_type='recalls'
    print('In Recalls get_record def and current record is:::', current_record_type)
    linked_record_type=record_type
    id_for_dash=re_id_for_dash
    records_array=record_remover_util(current_record_type,linked_record_type,id_for_dash)[0]
        
    return jsonify({'records':records_array})



@bp_recalls.route('/delete_linked_record_recalls/<re_id_for_dash>/<linked_record>', methods=["GET","POST"])
@login_required
def delete_linked_record_recalls(re_id_for_dash,linked_record):
    print('ENTER -delete_linked_record')
    print('re_id_for_dash::::', re_id_for_dash)
    print('linked_record::::',linked_record)
    #get current record sqlalchemy
    current_record=sess.query(Recalls).get(int(re_id_for_dash))
    
    #get linked_record_type
    #get linked_record id
    if linked_record[0:3]=="Inv":
        linked_record_type=linked_record[:14]
        linked_record_id=linked_record[15:15+linked_record[15:].find('|')]
    elif linked_record[0:3]=="Rec":
        linked_record_type=linked_record[:7].lower()
        linked_record_id=linked_record[8:8+linked_record[8:].find('|')]
    
    #make linked_record_key= linked_record_type + id
    linked_record_key=linked_record_type.lower()+linked_record_id
    
    #delete linked_record from current.linked_record using linked_record_key
    cur_records_dict=json.loads(current_record.linked_records)
    print('cur_records_dict::::',cur_records_dict)
    del cur_records_dict[linked_record_key]
    
    current_record.linked_records=json.dumps(cur_records_dict)
    print('cur_records_dict after deleted and should be in 317s linked_records::::',cur_records_dict)
    #Edit LINKED_RECORD's linked record
    #get linked reocrd sqlalchemy
    if linked_record[0:3]=="Inv":
        linked_record_sql=sess.query(Investigations).get(int(linked_record_id))
    elif linked_record[0:3]=="Rec":
        linked_record_sql=sess.query(Recalls).get(int(linked_record_id))
        
    #make current_record_key= 'recalls' + id
    current_record_key='recalls' + re_id_for_dash
    #delete linked_record from linked_record.linked_record using current_record_key
    linked_records_dict=json.loads(linked_record_sql.linked_records)
    print('linked_records_dict::::',linked_records_dict)
    del linked_records_dict[current_record_key]
    linked_record_sql.linked_records=json.dumps(linked_records_dict)
    sess.commit()
    print('linked_records_dict after deleted and should be in selected linked_records::::',linked_records_dict)
    return redirect(url_for('bp_recalls.recalls_dashboard', re_id_for_dash=re_id_for_dash))










