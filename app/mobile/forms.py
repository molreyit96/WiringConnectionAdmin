import re
from types import CoroutineType
from django import forms
from .models import *
from workOrder import models as catalogModel
from django.core.validators import FileExtensionValidator

class DailyMobEmpForm(forms.ModelForm):

    class Meta:
        model = DailyMobEmployee
        fields = [
            'DailyID',
            'EmployeeID',
            'per_to_pay',
            'on_call',
            'bonus',
            'start_time',
            'start_lunch_time',
            'end_lunch_time',
            'end_time',
            'total_hours',
            'billableHours',
            'is_own_vehicle',
            'own_vehicle_pay',
        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['DailyID'].disabled = True
        self.fields['EmployeeID'].queryset = qs

class DailyMobItemForm(forms.ModelForm):
    """ itemID = forms.ModelChoiceField(queryset=itemPrice.objects.filter(location__LocationID = ),required=False)"""

    class Meta:
        model = DailyMobItem
        fields = [
            'DailyID',
            'itemID',
            'quantity',            
        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['DailyID'].disabled = True
        self.fields['itemID'].queryset = qs

class DailyMobDocsForm(forms.ModelForm):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])],
    )
    docType = forms.TypedChoiceField(
        choices=docType_choice,
        coerce=int,  # Ensure value is converted to integer
        initial=1,   # Default value
        widget=forms.Select(attrs={
            'class': 'form-select doc-type-select',
            'style': 'cursor: pointer;',
            'data-testid': 'doc-type-field'
        }),       
        error_messages={
            'required': 'Please select a document type',
            'invalid_choice': 'Invalid document type selected'
        }
    )

    class Meta:
        model = DailyMobDocs
        fields = [
            'DailyID',
            'docType',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['DailyID'].disabled = False
        self.fields['docType'].disabled = True
        

class BulkUploadDocsForm(forms.ModelForm):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])],
        required=False,
    )

    class Meta:
        model = DailyMobDocs
        fields = [
            'DailyID',
            'docType',
            'docName',
            'document',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional since we set them manually
        self.fields['DailyID'].required = False
        self.fields['docType'].required = False
        self.fields['docName'].required = False
        self.fields['document'].required = False

class TimesheetForm(forms.ModelForm):   
    class Meta:
        model = Timesheet
        fields = [
            'id',
            'EmployeeID',
            'date',
            'start_time',
            'start_lunch_time',
            'end_lunch_time',
            'end_time',
            'total_hours',
            'start_mileage',
            'end_mileage',
            'total_mileage',
            'Location',
            'Status', 
            'createdBy',
            'created_date',
            'updated_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['EmployeeID'].disabled = True
        self.fields['Status'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['updated_date'].disabled = True
        self.fields['total_mileage'].disabled = True
        self.fields['total_hours'].disabled = True
        
class TimesheetDisabledForm(forms.ModelForm):   
    class Meta:
        model = Timesheet
        fields = [
            'id',
            'EmployeeID',
            'date',
            'start_time',
            'start_lunch_time',
            'end_lunch_time',
            'end_time',
            'total_hours',
            'start_mileage',
            'end_mileage',
            'total_mileage',
            'Location',
            'Status', 
            'comments',
            'createdBy',
            'created_date',
            'updated_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['EmployeeID'].disabled = True
        self.fields['date'].disabled = True
        self.fields['start_time'].disabled = True
        self.fields['start_lunch_time'].disabled = True
        self.fields['end_lunch_time'].disabled = True
        self.fields['end_time'].disabled = True
        self.fields['total_hours'].disabled = True
        self.fields['start_mileage'].disabled = True
        self.fields['end_mileage'].disabled = True
        self.fields['total_mileage'].disabled = True
        self.fields['Location'].disabled = True
        self.fields['Status'].disabled = True
        self.fields['comments'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['updated_date'].disabled = True
        self.fields['total_mileage'].disabled = True

class TimesheetSuperForm(forms.ModelForm):   
    class Meta:
        model = Timesheet
        fields = [
            'EmployeeID',
            'date',
            'start_time',
            'start_lunch_time',
            'end_lunch_time',
            'end_time',
            'total_hours',
            'start_mileage',
            'end_mileage',
            'total_mileage',
            'Location',
            'comments',
            'Status', 
            'createdBy',
            'created_date',
            'updated_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['updated_date'].disabled = True
        self.fields['total_hours'].disabled = True
        self.fields['total_mileage'].disabled = True


class TimesheetSuperFormApproved(forms.ModelForm):   
    class Meta:
        model = Timesheet
        fields = [
            'EmployeeID',
            'date',
            'start_time',
            'start_lunch_time',
            'end_lunch_time',
            'end_time',
            'start_mileage',
            'end_mileage',
            'total_mileage',
            'Location',
            'comments',
            'Status', 
            'createdBy',
            'created_date',
            'updated_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['EmployeeID'].disabled = True
        self.fields['date'].disabled = True
        self.fields['start_time'].disabled = True
        self.fields['start_lunch_time'].disabled = True
        self.fields['end_lunch_time'].disabled = True
        self.fields['end_time'].disabled = True
        self.fields['start_mileage'].disabled = True
        self.fields['end_mileage'].disabled = True
        self.fields['total_mileage'].disabled = True
        self.fields['Location'].disabled = True
        self.fields['Status'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['updated_date'].disabled = True

class TimesheetRejectedForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = ['EmployeeID',
                  'date',
                  'comments',]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['EmployeeID'].disabled = True
        self.fields['date'].disabled = True


class TimesheetApprovedForm(forms.ModelForm):

    Period = forms.ModelChoiceField(queryset= catalogModel.period.objects.filter(status=1),required=True)
    

    class Meta:
        model = Timesheet
        fields = ['EmployeeID',
                  'date',
                  'comments',
                  'Period',
                  'crew']
        
    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['EmployeeID'].disabled = True
        self.fields['date'].disabled = True
        self.fields['crew'].required = True
        self.fields['crew'].queryset = qs

class DailyMobApprovedForm(forms.ModelForm):

    Period = forms.ModelChoiceField(queryset= catalogModel.period.objects.filter(status=1),required=True)
    

    class Meta:
        model = DailyMob
        fields = [
                  'day',                 
                  'Period',
                  'crew',                  
                  'comments',
                  'daily_production',
                  'daily_Status',
                  'daily_date',
                  'daily_zone',
                  'daily_comments',  
                  'daily_rtb',
                  'daily_wp',
                  'daily_cd',
                  'daily_nfs',
                  'daily_fd',         
                  'daily_rtb_pep',  
                  ]
        
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.fields['day'].disabled = True
        self.fields['Period'].disabled = True
        self.fields['crew'].disabled = True

class DailyMobRejectedForm(forms.ModelForm):

    Period = forms.ModelChoiceField(queryset= catalogModel.period.objects.filter(status=1),required=True)
    

    class Meta:
        model = DailyMob
        fields = [
                  'day',                 
                  'Period',
                  'crew',                  
                  'comments',                           
                  ]
        
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.fields['day'].disabled = True
        self.fields['Period'].disabled = True
        self.fields['crew'].disabled = True
