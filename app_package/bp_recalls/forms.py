from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed #used for image uploading
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    TextAreaField, FloatField,SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField



class DatabaseForm(FlaskForm):
    excelFile = FileField('excelFile', validators = [FileAllowed(['xlsx'])])
    uploadExcel = SubmitField('Upload Excel File')

class ReForm(FlaskForm):
    record_type=SelectField('record_type',choices=[('recalls','Recalls'),('investigations','Investigations')])
    #select field choices (values, choice that shows up)
    records_list=SelectField('records_list',choices=[])