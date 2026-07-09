import re
from types import CoroutineType
from django import forms
from .models import *
from django.core.validators import FileExtensionValidator


class LocationsForm(forms.ModelForm):
    LocationID = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class':'form-control'}))
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    description = forms.CharField(max_length=150, widget=forms.Textarea(attrs={'class':'form-control'}))
    city= forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
    is_active= forms.BooleanField(required=False)

    class Meta:
        model = Locations
        fields = [
            "LocationID",
            "name",           
            "description",
             "city",
             'is_active'
             
        ]

class EmployeesForm(forms.ModelForm):   

    supervisor_name = forms.ModelChoiceField(queryset=Employee.objects.filter(is_supervisor=True, is_active=True),required=False)
    employeeID = forms.CharField(required=False)
    signature = forms.ImageField(label="employee_signature", widget=forms.FileInput(), required=False)

    class Meta:
        model = Employee
        fields = [
            "employeeID",
            "first_name",           
            "last_name",
             "middle_initial",
             "supervisor_name",
             "termination_date",
             "hire_created",
             "hourly_rate",
             "email",
             "Location",
             "user",
             "signature",
             "is_active",
             "is_supervisor",
             "is_admin",
             "is_superAdmin",
             "is_manager",
             "is_mobile",
             "is_read_only",
             "accounts_payable"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employeeID'].disabled = True

class workOrderForm(forms.ModelForm):
    prismID = forms.CharField(label="Prism ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    workOrderId = forms.CharField(label="Work Order ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'})) 
    PO = forms.CharField(label="Purchase Order", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    POAmount= forms.CharField(label="Purchase Order Amount",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstType= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstCoordinator= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control', 'size':60}), required=False)
    WorkOrderDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    EstCompletion= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    IssuedBy= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobAddress= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SiteContactName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SitePhoneNumber= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    Comments= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #Status= forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}))
    CloseDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UploadDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UserName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)

    WCSup = forms.ModelChoiceField(label="Supervisor",queryset=Employee.objects.filter(is_supervisor=True, is_active=True, user__isnull=False), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    createdBy = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    created_date = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)

    class Meta:
        model = workOrder
        fields = [
            'prismID',
            'workOrderId',
            'PO',
            'POAmount',
            'ConstType',
            'ConstCoordinator',
            'WorkOrderDate',
            'EstCompletion',
            'IssuedBy',
            'JobName',
            'JobAddress',
            'SiteContactName',
            'SitePhoneNumber',
            'Comments',
            'Status',
            'CloseDate',
            'WCSup',
            'UploadDate',
            'UserName',
            "Location",
            "created_date",
            "createdBy"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prismID'].disabled = True
        self.fields['workOrderId'].disabled = True
        self.fields['PO'].disabled = True       
        self.fields['created_date'].disabled = True
        self.fields['createdBy'].disabled = True 


class DeletedworkOrderForm(forms.ModelForm):
    prismID = forms.CharField(label="Prism ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    workOrderId = forms.CharField(label="Work Order ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'})) 
    PO = forms.CharField(label="Purchase Order", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    POAmount= forms.CharField(label="Purchase Order Amount",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstType= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstCoordinator= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control', 'size':60}), required=False)
    WorkOrderDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    EstCompletion= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    IssuedBy= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobAddress= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SiteContactName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SitePhoneNumber= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    Comments= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #Status= forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}))
    CloseDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UploadDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UserName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)

    WCSup = forms.ModelChoiceField(label="Supervisor",queryset=Employee.objects.filter(is_supervisor=True, is_active=True, user__isnull=False), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    createdBy = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    created_date = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)

    class Meta:
        model = DeletedWorkOrders
        fields = [
            'prismID',
            'workOrderId',
            'PO',
            'POAmount',
            'ConstType',
            'ConstCoordinator',
            'WorkOrderDate',
            'EstCompletion',
            'IssuedBy',
            'JobName',
            'JobAddress',
            'SiteContactName',
            'SitePhoneNumber',
            'Comments',
            'Status',
            'CloseDate',
            'WCSup',
            'UploadDate',
            'UserName',
            "Location",
            "created_date",
            "createdBy"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prismID'].disabled = True
        self.fields['workOrderId'].disabled = True
        self.fields['PO'].disabled = True       
        self.fields['created_date'].disabled = True
        self.fields['createdBy'].disabled = True 

class workOrderFormAdmin(forms.ModelForm):
    prismID = forms.CharField(label="Prism ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    workOrderId = forms.CharField(label="Work Order ID", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'})) 
    PO = forms.CharField(label="Purchase Order", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    POAmount= forms.CharField(label="Purchase Order Amount",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstType= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    ConstCoordinator= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control', 'size':60}), required=False)
    WorkOrderDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    EstCompletion= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    IssuedBy= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    JobAddress= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SiteContactName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    SitePhoneNumber= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    Comments= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #Status= forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}))
    CloseDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UploadDate= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    UserName= forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)

    WCSup = forms.ModelChoiceField(label="Supervisor",queryset=Employee.objects.filter(is_supervisor=True, is_active=True, user__isnull=False), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    createdBy = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    created_date = forms.DateField(widget=forms.DateInput(format=('%Y-%m-%d'),attrs={'class': 'form-control','type': 'date'}))

    class Meta:
        model = workOrder
        fields = [
            'prismID',
            'workOrderId',
            'PO',
            'POAmount',
            'ConstType',
            'ConstCoordinator',
            'WorkOrderDate',
            'EstCompletion',
            'IssuedBy',
            'JobName',
            'JobAddress',
            'SiteContactName',
            'SitePhoneNumber',
            'Comments',
            'Status',
            'CloseDate',
            'WCSup',
            'UploadDate',
            'UserName',
            "Location",
            "created_date",
            "createdBy"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['prismID'].disabled = True
        #self.fields['workOrderId'].disabled = True
        #self.fields['PO'].disabled = True       
        self.fields['created_date'].disabled = False
        self.fields['createdBy'].disabled = True 


class WorkOrderFileUploadForm(forms.Form):
    invoice_file = forms.FileField(label='Select PDF File', required=True)



class ItemForm(forms.ModelForm):
    itemID = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class':'form-control'}))
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))
    description = forms.CharField(max_length=250, widget=forms.Textarea(attrs={'class':'form-control'}))
    is_active= forms.BooleanField(required=False)
    createdBy = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    created_date = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    class Meta:
        model = item
        fields = [
            "itemID",
            "name",           
            "description",
            "is_active",
            "createdBy",
            "created_date"
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
       

class ItemPriceForm(forms.ModelForm):
    
    class Meta:
        model = itemPrice
        fields = [
           'item',
            'location',
            'pay_perc',
            'price',
            'emp_payout',
            'rate',
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].disabled = True

class InternalPOForm(forms.ModelForm):   
    #poNumber = forms.IntegerField(label = "PO Number", widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True, is_supervisor = True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    pickupEmployee = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    product = forms.CharField(label="Product",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    quantity = forms.CharField(label="Quantity",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    total = forms.DecimalField(label="Total", max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #isAmountRounded = forms.BooleanField(label="Is Amount Rounded",required=False)
    #nonBillable = forms.BooleanField(label="Non-Billable",required=False)

    class Meta:
        model = internalPO
        fields = [
            'poNumber',
            #'woID',
            'supervisor',
            'pickupEmployee',
            'product',
            'quantity',
            'total',
            'isAmountRounded',            
            'created_date',
            'createdBy',
            'updated_date',
            'updatedBy',
            'Status',
            #'transferFromPO',
            'transfer_date',
            'transferBy'         
        ]


    def __init__(self, *args, **kwargs):      
        super().__init__(*args, **kwargs)
        self.fields['poNumber'].disabled = True
        #self.fields['woID'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['updatedBy'].disabled = True
        self.fields['updated_date'].disabled = True
        self.fields['Status'].disabled = True
        #self.fields['transferFromPO'].disabled = True
        self.fields['transfer_date'].disabled = True
        self.fields['transferBy'].disabled = True
        self.fields['total'].disabled = True
 
 
class DeletedInternalPOForm(forms.ModelForm):   
    #poNumber = forms.IntegerField(label = "PO Number", widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True, is_supervisor = True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    pickupEmployee = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    product = forms.CharField(label="Product",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    quantity = forms.CharField(label="Quantity",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    total = forms.DecimalField(label="Total", max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #isAmountRounded = forms.BooleanField(label="Is Amount Rounded",required=False)
    #nonBillable = forms.BooleanField(label="Non-Billable",required=False)

    class Meta:
        model = DeletedInternalPO
        fields = [
            'poNumber',
            #'woID',
            'supervisor',
            'pickupEmployee',
            'product',
            'quantity',
            'total',
            'isAmountRounded',            
            'created_date',
            'createdBy',            
            'Status',
            #'transferFromPO',
            'transfer_date',
            'transferBy'         
        ]


    def __init__(self, *args, **kwargs):      
        super().__init__(*args, **kwargs)
        self.fields['poNumber'].disabled = True
        #self.fields['woID'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['Status'].disabled = True
        #self.fields['transferFromPO'].disabled = True
        self.fields['transfer_date'].disabled = True
        self.fields['transferBy'].disabled = True
        self.fields['total'].disabled = True
        
 
class InternalPOFormAccounPay(forms.ModelForm):   
    #poNumber = forms.IntegerField(label = "PO Number", widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True, is_supervisor = True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    pickupEmployee = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    product = forms.CharField(label="Product",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    quantity = forms.CharField(label="Quantity",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    total = forms.DecimalField(label="Total", max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #isAmountRounded = forms.BooleanField(label="Is Amount Rounded",required=False)
    #nonBillable = forms.BooleanField(label="Non-Billable",required=False)

    class Meta:
        model = internalPO
        fields = [
            'poNumber',
            #'woID',
            'supervisor',
            'pickupEmployee',
            'product',
            'quantity',
            'total',
            'isAmountRounded',            
            'created_date',
            'createdBy',
            'updated_date',
            'updatedBy',
            'Status',
            #'transferFromPO',
            'transfer_date',
            'transferBy'         
        ]


    def __init__(self, *args, **kwargs):      
        super().__init__(*args, **kwargs)
        self.fields['poNumber'].disabled = True
        #self.fields['woID'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['Status'].disabled = True
        #self.fields['transferFromPO'].disabled = True
        self.fields['transfer_date'].disabled = True
        self.fields['transferBy'].disabled = True        
        self.fields['updated_date'].disabled = True
        self.fields['updatedBy'].disabled = True

class InternalPOFormAdmin(forms.ModelForm):   
    #poNumber = forms.IntegerField(label = "PO Number", widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True, is_supervisor = True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    pickupEmployee = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    product = forms.CharField(label="Product",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    quantity = forms.CharField(label="Quantity",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    total = forms.DecimalField(label="Total",max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    invoices = forms.CharField(label="Invoices",max_length=350, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #isAmountRounded = forms.BooleanField(label="Is Amount Rounded",required=False)
    nonBillable = forms.BooleanField(label="Non-Billable",required=False)

    class Meta:
        model = internalPO
        fields = [
            'poNumber',
            #'woID',
            'supervisor',
            'pickupEmployee',
            'product',
            'quantity',
            'total',
            'invoices',
            'isAmountRounded',
            'nonBillable',
            'created_date',
            'createdBy',
            'updated_date',
            'updatedBy',
            'Status',
            #'transferFromPO',
            'transfer_date',
            'transferBy'         
        ]


    def __init__(self, *args, **kwargs):      
        super().__init__(*args, **kwargs)
        self.fields['poNumber'].disabled = True
        #self.fields['woID'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        self.fields['Status'].disabled = True
        #self.fields['transferFromPO'].disabled = True
        self.fields['transfer_date'].disabled = True
        self.fields['transferBy'].disabled = True 
        self.fields['updated_date'].disabled = True
        self.fields['updatedBy'].disabled = True


class InternalPOFormAdminUpdate(forms.ModelForm):   
    #poNumber = forms.IntegerField(label = "PO Number", widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True, is_supervisor = True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    pickupEmployee = forms.ModelChoiceField(queryset=Employee.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    product = forms.CharField(label="Product",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    quantity = forms.CharField(label="Quantity",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    total = forms.DecimalField(label="Total",max_digits=10, decimal_places=2, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    invoices = forms.CharField(label="Invoices",max_length=350, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #isAmountRounded = forms.BooleanField(label="Is Amount Rounded",required=False)
    nonBillable = forms.BooleanField(label="Non-Billable",required=False)

    class Meta:
        model = internalPO
        fields = [
            'poNumber',
            #'woID',
            'supervisor',
            'pickupEmployee',
            'product',
            'quantity',
            'total',
            'invoices',
            'isAmountRounded',
            'nonBillable',
            'created_date',
            'createdBy',
            'updated_date',
            'updatedBy',
            'Status',
            #'transferFromPO',
            'transfer_date',
            'transferBy'         
        ]


    def __init__(self, *args, **kwargs):      
        super().__init__(*args, **kwargs)
        self.fields['poNumber'].disabled = True
        #self.fields['woID'].disabled = True
        self.fields['createdBy'].disabled = True
        self.fields['created_date'].disabled = True
        #self.fields['Status'].disabled = True
        #self.fields['transferFromPO'].disabled = True
        self.fields['transfer_date'].disabled = True
        self.fields['transferBy'].disabled = True 
        self.fields['updated_date'].disabled = True
        self.fields['updatedBy'].disabled = True
        


class periodForm(forms.ModelForm):

    class Meta:
        model = period
        fields = [
            'periodID',
            'periodYear',
            'fromDate',
            'toDate',
            'payDate',
            'weekRange',
            'status'
        ]


class dailydForm(forms.ModelForm):   

    class Meta:
        model = Daily
        fields = [
            'crew',
            'Period',
            'Location',
            'day',
            'pdfDaily'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['crew'].disabled = True

class dailySupForm(forms.ModelForm):   

    class Meta:
        model = Daily
        fields = [
            'woID',
            'supervisor',
            'Location',
            'day',
            'pdfDaily'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True        


class DailyEmpForm(forms.ModelForm):

    class Meta:
        model = DailyEmployee
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

class DailyItemForm(forms.ModelForm):
    """ itemID = forms.ModelChoiceField(queryset=itemPrice.objects.filter(location__LocationID = ),required=False)"""

    class Meta:
        model = DailyItem
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



class DailyDocsForm(forms.ModelForm):
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
        model = DailyDocs
        fields = [
            'DailyID',
            'docType',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class vendorForm(forms.ModelForm):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))   
    address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contact = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contactPosition = forms.CharField(label="Contact Position",max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contactPhone = forms.CharField(label="Contact Phone",max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    description = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #is_active = forms.BooleanField(label="Is Active", required=False)
    created_date = forms.CharField(label="Created Date",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    createdBy = forms.CharField(label="Created By",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)


    class Meta:
        model = vendor
        fields = [
            'name',
            'address',
            'contact', 
            'contactPosition',
            'contactPhone',
            'description',
            'is_active',
            'created_date',
            'createdBy'        
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].disabled = True
        self.fields['createdBy'].disabled = True





class subcontractorForm(forms.ModelForm):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))   
    address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contact = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contactPosition = forms.CharField(label="Contact Position",max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    contactEmail = forms.EmailField(label="Contact Email",max_length=50, widget=forms.EmailInput(attrs={'class':'form-control'}), required=False)
    contactPhone = forms.CharField(label="Contact Phone",max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    description = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    #is_active = forms.BooleanField(label="Is Active", required=False)
    #pay70Percent = forms.BooleanField()
    payPercent = forms.CharField(label="Pay Percent", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)  
    created_date = forms.CharField(label="Created Date",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
    createdBy = forms.CharField(label="Created By",max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)


    class Meta:
        model = subcontractor
        fields = [
            'name',
            'address',
            'contact', 
            'contactPosition',
            'contactEmail',
            'contactPhone',
            'description',
            'is_active',
            'pay70Percent',
            'payPercent',
            'created_date',
            'createdBy'        
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].disabled = True
        self.fields['createdBy'].disabled = True




      
class extProdForm(forms.ModelForm):
    
    woID = forms.ModelChoiceField(label = "Selected Work Order", queryset=workOrder.objects.filter(Status__in=(2,8)), widget=forms.Select(attrs={'class':'form-control'}))
    subcontractor = forms.ModelChoiceField(queryset=subcontractor.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'})) 
    invoiceNumber = forms.CharField(label="Invoice Number", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))  
    total_invoice = forms.CharField(label="Total Invoice", max_length=200, widget=forms.TextInput(attrs={'class':'form-control'}))  
    invoice_date = forms.DateField(label="Invoice Date", widget=forms.DateInput(format=('%Y-%m-%d'),attrs={'class': 'form-control','type': 'date'}))
    class Meta:
        model = externalProduction
        fields = [
            'woID',
            'subcontractor',
            'invoiceNumber',
            'total_invoice',
            'invoice_date'          
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True

class extProdItemForm(forms.ModelForm):
    """ itemID = forms.ModelChoiceField(queryset=itemPrice.objects.filter(location__LocationID = ),required=False)"""

    class Meta:
        model = externalProdItem
        fields = [
            'externalProdID',
            'itemID',
            'quantity',            
        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['externalProdID'].disabled = True
        self.fields['itemID'].queryset = qs

class authorizedBillingForm(forms.ModelForm):

    class Meta:
        model = authorizedBilling
        fields = [
            'woID',
            'itemID',
            'quantity', 
            'comment'           
        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True
        self.fields['itemID'].queryset = qs


class TrauthorizedBillingForm(forms.ModelForm):

    class Meta:
        model = authorizedBilling
        fields = [
            'woID',
            'itemID',
            'quantity', 
            'comment',
            'transferFrom',
            'transferTo',
            'transferQty',
            'transfer_date',
            'transferBy',

        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True
        self.fields['itemID'].queryset = qs
        

class EmployeeLocationForm(forms.ModelForm):

    class Meta:
        model = employeeLocation
        fields = [
            'employeeID',
            'LocationID'         
        ]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('qs')
        super().__init__(*args, **kwargs)
        self.fields['employeeID'].disabled = True
        self.fields['LocationID'].queryset = qs


class billingAddressForm(forms.ModelForm):

    class Meta:
        model = billingAddress
        fields = [
            'zipCode',
            'state' ,
            'city',
            'address',
            'description',
            'created_date',
            'createdBy'        
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].disabled = True
        self.fields['createdBy'].disabled = True



class woCommentLogForm(forms.ModelForm):

    class Meta:
        model = woCommentLog
        fields = [
           'woID',
            'comment',

        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True


class woAdjustEstimateForm(forms.ModelForm):

    invoiceNumber = forms.CharField(required=False)
    estimateNumber = forms.CharField(required=False)

    class Meta:
        model = woAdjustment
        fields = [
           'woID',
           'estimateNumber',
           'invoiceNumber',
            'adjustment',

        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True
        self.fields['estimateNumber'].disabled = True
        self.fields['invoiceNumber'].disabled = True

class woEstimateCommentForm(forms.ModelForm):
   
    estimateNumber = forms.CharField(required=False)

    class Meta:
        model = woEstimate
        fields = [
           'woID',
           'estimateNumber',           
            'comment',

        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['woID'].disabled = True
        self.fields['estimateNumber'].disabled = True
