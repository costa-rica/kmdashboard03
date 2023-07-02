# from app_package import db
from km03_models import sess, engine, text, Base, Users, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd
import re
from app_package.bp_investigations.utils_general import track_util


def lookup_util(problem_dict_tup1,df_lookup_inv, df_lookup_re):
    count=0
    for i,j in problem_dict_tup1.items():
        if i[0]=='r':#lookup recalls
            temp_add=list(df_lookup_re.loc[df_lookup_re.RECORD_ID==int(i[7:])].CAMPNO)[0]
        else:
            temp_add=list(df_lookup_inv.loc[df_lookup_inv.id==int(i[14:])].NHTSA_ACTION_NUMBER)[0]
        if count==0:
            temp_add_string_list=temp_add
        else:
            temp_add_string_list=temp_add_string_list+', ' +temp_add
        count+=1
    return temp_add_string_list

def create_categories_xlsx(excel_file_name, column_names_for_df, formDict, db_table):
    #create excel object to store the report
    excelObj=pd.ExcelWriter(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],excel_file_name))

    # Make df for column Names
    colNamesDf=pd.DataFrame([column_names_for_df],columns=column_names_for_df)
    colNamesDf.to_excel(excelObj,sheet_name=db_table.capitalize() + ' Data', header=False, index=False)

    queryDf = pd.read_sql_table(db_table, engine)
    queryDf=queryDf[column_names_for_df].copy()
    # 2011 ODATE filter removed 8/2/2021 per request
    # queryDf=queryDf[(queryDf['ODATE']>datetime(2011,1,1,0,0,0))]

    #if linked_records in column_names_for_df:
    if 'linked_records' in column_names_for_df:
        print('Adjusting linked_records')
        #make df's for looking up ids'record id's 
        
        # new_id_column='CAMPNO' if db_table=='recalls' else 'NHTSA_ACTION_NUMBER'
        # df_lookup=pd.read_sql_table(db_table, db.engine)
        # df_lookup=df_lookup[[id_column,new_id_column]].copy()
        df_lookup_inv=pd.read_sql_table('investigations', engine)
        df_lookup_inv=df_lookup_inv[['id','NHTSA_ACTION_NUMBER']].copy()
        df_lookup_re=pd.read_sql_table('recalls', engine)
        df_lookup_re=df_lookup_re[['RECORD_ID','CAMPNO']].copy()
        
        #Make dictionary df id to CAMPNO/NHTSA_ACTION_NUMBER
        id_column='RECORD_ID' if db_table=='recalls' else 'id'
        converted_dict={}
        print("queryDf:")
        print(queryDf)
        for tup in list(zip(queryDf.__getattr__(id_column),queryDf.linked_records)):
            print("-------- ISSUE --------------")
            print("tup[0]: ",tup[0])
            print("tup[1]: ",tup[1])
            print("-------------------------------")
            # file1 = open("converted_dict_progress.txt","a")
            # file1.write(str(tup[0]) + "\n")
            # file1.close()
            if tup[1]==None or tup[1]=='{}' or tup[1]=='':
                print("--- Are we getting none????? ---")
                converted_dict[tup[0]]=None
            else:
                print("--- tup[1] is NOT none ---")
                check_value=tup[1]
                converted_dict[tup[0]]=lookup_util(json.loads(tup[1]),df_lookup_inv, df_lookup_re)
        
        #convert dictinoary to DF then merge with desired table
        converted_dict_df=pd.DataFrame.from_dict(converted_dict,orient='index',columns=['linked_records_new'])
        concat_df=pd.concat([queryDf.set_index([id_column]),converted_dict_df], axis=1)
        # concat_df.to_excel(db_table+'_linked_records_conversion.xlsx')#file to check conversion
        
        #remove old lined records column
        position_linked_records=column_names_for_df.index('linked_records')
        column_names_for_df[position_linked_records]='linked_records_new'
        concat_df.reset_index(inplace=True)
        concat_df.rename(columns={'index':id_column},inplace=True)
        queryDf=concat_df[column_names_for_df].copy()
        
        
        queryDf.rename(columns={'linked_records_new':'linked_records'},inplace=True)
        # queryDf.reset_index(inplace=True)
    
    
    queryDf.to_excel(excelObj,sheet_name=db_table.capitalize() + ' Data', header=False, index=False,startrow=1)
    inv_data_workbook=excelObj.book
    notes_worksheet = inv_data_workbook.add_worksheet('Notes')
    notes_worksheet.write('A1','Created:')
    notes_worksheet.set_column(1,1,len(str(datetime.now())))
    time_stamp_format = inv_data_workbook.add_format({'num_format': 'mmm d yyyy hh:mm:ss AM/PM'})
    notes_worksheet.write('B1',datetime.now(), time_stamp_format)
    excelObj.close()


def existing_report(excel_file_name, db_table):
    # Read Excel and turn entire sheet to a df
    time_stamp_df = pd.read_excel(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],excel_file_name),
        'Notes',header=None)
    categories_df =pd.read_excel(os.path.join(
        current_app.config['DIR_DB_FILES_UTILITY'],excel_file_name),
        db_table.capitalize() + ' Data')
    categories_dict={i:'checked' for i in list(categories_df.columns)}
    print('categories_dict (existing_report):::', categories_dict)
    time_stamp = time_stamp_df.loc[0,1].to_pydatetime().strftime("%Y-%m-%d %I:%M:%S %p")
    return (categories_dict,time_stamp)



