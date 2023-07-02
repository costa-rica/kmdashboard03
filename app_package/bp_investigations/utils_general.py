
from km03_models import sess, engine, text, Base, Users, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app, request, flash
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd


def category_list_dict_util():
    categories_excel=os.path.join(current_app.config['DIR_DB_FILES_UTILITY'], 'categories.xlsx')
    df=pd.read_excel(categories_excel)
    category_list_dict={}
    for i in range(0,len(df.columns)):
        category_list_dict[df.columns[i]] =df.iloc[:,i:i+1][df.columns[i]].dropna().tolist()
    return category_list_dict



def remove_category_util(formDict, query_file_name):
    for i,j in formDict.items():
        if 'remove' in i:
            print('remove_category_util(formDict):::', i)
            remove_name = 'sc' + i[6:]
    return remove_name
    

def search_criteria_dictionary_util(formDict, query_file_name):   
    print('START search_criteria_dictionary_util')

    
    #make search dict with only 'sc_' items but take out 'sc_' :["", "string_contains"]
    search_query_dict={i[3:] :[j,"string_contains"] for i,j in formDict.items() if "sc_" in i}
    
    #make match_type dict, remove 'match_type' from key and keep value
    match_type_dict={i[11:]: j for i,j in formDict.items() if "match_type_" in i}
    
    #Loop over match_type dict, for key in in match_type dict, replace value in search_dict with [search_dict[key][0],value]
    search_query_dict = {i:([j[0],match_type_dict[i]] if i in match_type_dict.keys() else j) for i,j in search_query_dict.items() }
    


    # query_file_name='current_query_re.txt'
    with open(os.path.join(current_app.config['DIR_DB_QUERIES'],query_file_name),'w') as dict_file:
        json.dump(search_query_dict,dict_file)
    print('END search_criteria_dictionary_util(formDict), returns query_file_name')
    return query_file_name
    
    
def record_remover_util(current_record_type,linked_record_type,id_for_dash):
    #this function: 1)removes records from dropdown;
    #2)makes list of records dashboard, directly taken from removed records in #1
    
    investigation_id_list=[]
    recalls_id_list=[]
    
    # determine current_record_type and #get record query and linked_records
    if current_record_type=='investigations':
        current_record= sess.query(Investigations).get(int(id_for_dash))
        # investigation_id_list.append(int(id_for_dash))
    elif current_record_type=='recalls':
        current_record= sess.query(Recalls).get(int(id_for_dash))
        # recalls_id_list.append(int(id_for_dash))

    #if linked_records>0 then make lists of existing links from 
    if current_record.linked_records != None and current_record.linked_records != '':
        linked_dict=json.loads(current_record.linked_records)
        for i,j in linked_dict.items():
            if 'investigations' in i:
                investigation_id_list.append(int(i[14:]))
            elif 'recalls' in i:
                recalls_id_list.append(int(i[7:]))
    
    
    #prepare Inv AND Re df for 1)dropdown list by removing the id's from previous section
    #2)linked_records list for current record
    inv_list_identifiers=sess.query(
        Investigations.id, Investigations.NHTSA_ACTION_NUMBER, Investigations.MAKE, Investigations.MODEL, Investigations.COMPNAME).all()
    df_inv=pd.DataFrame(inv_list_identifiers,columns = ['id', 'NHTSA_No', 'MAKE','MODEL','Component'])
    
    df_inv_for_dropdown=df_inv[~df_inv['id'].isin(investigation_id_list)]#df for dropdown if investigations
    if current_record_type=='investigations':
        df_inv_for_dropdown=df_inv_for_dropdown.drop(df_inv_for_dropdown[df_inv_for_dropdown.id==int(
            id_for_dash)].index)#remove current record from list
    
    #make list of Investigations linked to current record - if any
    records_array_inv=[]
    if len(investigation_id_list)>0:
        df_inv_for_dashboard_list=df_inv[df_inv['id'].isin(investigation_id_list)]#df for linked investigations
        inv_records_list_array= df_inv_for_dashboard_list.values.tolist()#list for linked investigations

        #make investigations list ['Investigation', 'id', NHTSA_ACTION_NUMBER, Make, Model, component]
        for i in inv_records_list_array:
            i.insert(0,'Investigations')

        records_array_inv=[]
        for i in inv_records_list_array:
            thing=F"{i[0]}|{i[1]}|{i[2]}|{i[3]}|{i[4]}"
            records_array_inv.append(thing)
    #END make list of Investigations linked to current record - if any
    
    re_list_identifiers=sess.query(
        Recalls.RECORD_ID,Recalls.CAMPNO,Recalls.MAKETXT,Recalls.MODELTXT,Recalls.COMPNAME).all()
    df_re=pd.DataFrame(re_list_identifiers,columns=['RECORD_ID','CAMPNO','MAKETXT','MODELTXT','COMPNAME'])
    
    df_re_for_dropdown=df_re[~df_re['RECORD_ID'].isin(recalls_id_list)]#df for dropdown if recalls
    if current_record_type=='recalls':
        df_re_for_dropdown=df_re_for_dropdown.drop(df_re_for_dropdown[df_re_for_dropdown.RECORD_ID==int(
            id_for_dash)].index)#remove current record from list
    
    #make list of Recalls linked to current record - if any
    records_array_re=[]
    if len(recalls_id_list)>0:
        df_re_for_dashboard_list=df_re[df_re['RECORD_ID'].isin(recalls_id_list)]#df for linked recalls
        re_records_list_array= df_re_for_dashboard_list.values.tolist()#list for linked recalls
        
        for i in re_records_list_array:
            i.insert(0,'Recalls')

        records_array_re=[]
        for i in re_records_list_array:
            thing=F"{i[0]}|{i[1]}|{i[2]}|{i[3]}|{i[4]}"
            records_array_re.append(thing)
    #END make list of Recalls linked to current record - if any

    #convert df dropdowns to
    if linked_record_type=='investigations':
        identifiers_list=df_inv_for_dropdown.values.tolist()
    else:
        identifiers_list=df_re_for_dropdown.values.tolist()
    
    #format dropdown list i.e. records_array
    records_array=[]
    for i in identifiers_list:
        list_obj = {}
        list_obj['id']=i[0]
        list_obj['shows_up']=F"{i[0]}|{i[1]}|{i[2]}|{i[3]}|{i[4]}"
        records_array.append(list_obj)

    
    all_records=records_array_inv+records_array_re
    
    return (records_array, all_records)




def update_files_util(filesDict, id_for_dash,record_type):
    if record_type=='investigation':
        dash_record= sess.query(Investigations).get(id_for_dash)
        uploaded_file=request.files['investigation_file']
        current_files_dir_name = 'Investigation_' +str(id_for_dash)
    else:
        dash_record= sess.query(Recalls).get(id_for_dash)
        uploaded_file=request.files['recall_file']
        current_files_dir_name = 'Recall_' +str(id_for_dash)
    
    
    if dash_record.files !=None:
        if uploaded_file.filename in dash_record.files:
            flash('File already uploaded or file with same file name is associated to record.', 'warning')
            return 'file_not_added'
    
    
    current_files_dir=os.path.join(current_app.config['DIR_DB_FILES'], current_files_dir_name)

    if not os.path.exists(current_files_dir):
        os.makedirs(current_files_dir)
    uploaded_file.save(os.path.join(current_files_dir,uploaded_file.filename))

    ##Investigations database files column - set value as string comma delimeted
    if dash_record.files =='' or dash_record.files ==None:
        dash_record.files =uploaded_file.filename
    else:
        dash_record.files =dash_record.files +','+ uploaded_file.filename
    sess.commit()
    
    flash('File added!', 'success')
    return 'file_added'


def track_util(record_type, update_field,update_from, update_to,id_for_dash):
    #update tracking
    if record_type=='recalls':
        newTrack=Tracking_re(field_updated=update_field,updated_from=update_from,
            updated_to=update_to, updated_by=current_user.id,recalls_table_id=id_for_dash)
    else:
        newTrack=Tracking_inv(field_updated=update_field,updated_from=update_from,
            updated_to=update_to, updated_by=current_user.id,
            investigations_table_id=id_for_dash)
    sess.add(newTrack)
    sess.commit()






