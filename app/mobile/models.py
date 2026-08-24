from contextlib import nullcontext
from operator import truediv
from pyexpat import model
from random import choices
from statistics import mode
from unittest.util import _MAX_LENGTH
from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime
from workOrder import models as catalogModel

prodStatus_choice = (
    (1, 'Draft'),
    (2, 'Sent'),
    (3, 'Pending'),
    (4, 'Approved'),
    (5, 'Rejected'),
    (6, 'Deleted'),
)


docType_choice = (
    (1, 'Maps'),
    (2, 'Pictures'),
    (3, 'Material Backup'),
)

dailyStatus_choice = (
    (1, 'Work in Progress'),    
    (2, 'Done'),    
    
)
 

class Timesheet(models.Model):
    EmployeeID = models.ForeignKey(catalogModel.Employee, on_delete=models.CASCADE, db_column ='EmployeeID', null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    start_time = models.IntegerField(null=True, blank=True)
    start_lunch_time = models.IntegerField(null=True, blank=True)
    end_lunch_time = models.IntegerField(null=True, blank=True)
    end_time = models.IntegerField(null=True, blank=True)
    total_hours = models.FloatField(null=True, blank=True)
    regular_hours = models.FloatField(null=True, blank=True)
    ot_hour = models.FloatField(null=True, blank=True)
    double_time = models.FloatField(null=True, blank=True)
    start_mileage = models.IntegerField(null=True, blank=True)
    end_mileage = models.IntegerField(null=True, blank=True)
    total_mileage = models.IntegerField(null=True, blank=True)
    Status = models.IntegerField(default=1, choices = prodStatus_choice)   
    Location = models.ForeignKey(catalogModel.Locations, on_delete=models.CASCADE, db_column ='Location', null=False, blank=False)  
    comments = models.CharField(max_length=200, blank=True, null=True)
    created_date = models.DateTimeField(null=True, blank=True)
    createdBy = models.CharField(max_length=60, blank=True, null=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    updatedBy = models.CharField(max_length=60, blank=True, null=True)
    Period = models.ForeignKey(catalogModel.period, on_delete=models.CASCADE, db_column ='Period', null=True, blank=True)
    crew = models.ForeignKey(catalogModel.Daily, on_delete=models.CASCADE, db_column ='crew', null=True, blank=True)
    #crew = models.IntegerField(null=True, blank=True)
    transferred_date = models.DateTimeField(null=True, blank=True)
    tranferredBy = models.CharField(max_length=60, blank=True, null=True)
    

    def __str__(self):
        return  str(self.date)
    
    class Meta:
        unique_together = ('EmployeeID','date')
    #COnsultar cuantas veces puede enviar el empleado información al dia


class DailyMob(models.Model):
    crew = models.IntegerField(null=False, blank=False)
    Location = models.ForeignKey(catalogModel.Locations, on_delete=models.CASCADE, db_column ='Location', null=False, blank=False)
    Period = models.ForeignKey(catalogModel.period, on_delete=models.CASCADE, db_column ='Period', null=False, blank=False)
    day = models.DateField(null=False, blank=False)
    woID = models.ForeignKey(catalogModel.workOrder, on_delete=models.CASCADE, db_column ='woID', null=True, blank=True)
    supervisor = models.CharField(max_length=200, blank=True, null=True)
    own_vehicle = models.FloatField(blank=True, null=True)
    total_pay = models.FloatField(blank=True, null=True) 
    split_paymet = models.BooleanField(default=False)
    pdfDaily = models.FileField(null=True, upload_to="dailys") 
    Status = models.IntegerField(default=1, choices = prodStatus_choice)     
    comments = models.CharField(max_length=800, blank=True, null=True)
    daily_rtb = models.BooleanField(default=False)
    daily_wp = models.BooleanField(default=False)
    daily_cd = models.BooleanField(default=False)
    daily_nfs = models.BooleanField(default=False)
    daily_fd = models.BooleanField(default=False)
    daily_rtb_pep = models.BooleanField(default=False)
    daily_production = models.BooleanField(default=False)
    daily_Status = models.IntegerField(default=1, choices = dailyStatus_choice, null=True, blank=True)  
    daily_date = models.DateField(null=True, blank=True)
    daily_zone = models.CharField(max_length=100, blank=True, null=True)
    daily_comments = models.CharField(max_length=800, blank=True, null=True) # Tech Comments
    created_date = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=60, blank=True, null=True)
    crew_by_user = models.IntegerField(null=True , blank=True)
    send_date =  models.DateTimeField(null=True, blank=True)
    approved_date =  models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=60, blank=True, null=True)
    rejected_date =  models.DateTimeField(null=True, blank=True)
    rejected_by = models.CharField(max_length=60, blank=True, null=True)    
    deleted_date =  models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=60, blank=True, null=True)  

    def __str__(self):
        return str(self.crew) + " - " + str(self.day)
    
    class Meta:
        unique_together = ('Period','Location','day', 'crew')

class DailyMobEmployee(models.Model):
    DailyID = models.ForeignKey(DailyMob, on_delete=models.CASCADE, db_column ='DailyID', null=False, blank=False)
    EmployeeID = models.ForeignKey(catalogModel.Employee, on_delete=models.CASCADE, db_column ='EmployeeID', null=False, blank=False)
    per_to_pay =  models.FloatField(null=True, blank=True)
    on_call = models.FloatField(null=True, blank=True)
    bonus =  models.FloatField(null=True, blank=True)
    start_time = models.IntegerField(null=True, blank=True)
    start_lunch_time = models.IntegerField(null=True, blank=True)
    end_lunch_time = models.IntegerField(null=True, blank=True)
    end_time = models.IntegerField(null=True, blank=True)
    total_hours = models.FloatField(null=True, blank=True)
    regular_hours = models.FloatField(null=True, blank=True)
    rt_pay = models.FloatField(blank=True, null=True)
    ot_hour = models.FloatField(null=True, blank=True)
    ot_pay = models.FloatField(blank=True, null=True)
    double_time = models.FloatField(null=True, blank=True)
    dt_pay = models.FloatField(blank=True, null=True)
    is_own_vehicle = models.BooleanField(default=False)
    own_vehicle_pay = models.FloatField(blank=True, null=True)
    payout =  models.FloatField(null=True, blank=True)
    emp_rate = models.FloatField(blank=True, null=True) 
    production = models.FloatField(blank=True, null=True) 
    billableHours = models.BooleanField(default=False)
    estimate = models.CharField(max_length=50, null=True, blank=True)
    invoice = models.CharField(max_length=50, null=True, blank=True)
    Status = models.IntegerField(default=1, choices = prodStatus_choice)     
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.DailyID) + " - " + str(self.EmployeeID)
    
    class Meta:
        unique_together = ('DailyID','EmployeeID')

class DailyMobItem(models.Model):
    DailyID = models.ForeignKey(DailyMob, on_delete=models.CASCADE, db_column ='DailyID', null=False, blank=False)
    itemID = models.ForeignKey(catalogModel.itemPrice, on_delete=models.CASCADE, db_column ='itemID', null=False, blank=False )
    quantity = models.IntegerField(null=False, blank=False)
    price = models.FloatField(null=True, blank=True)  
    total = models.FloatField(null=True, blank=True) 
    emp_payout = models.FloatField(null=True, blank=True)      
    estimate = models.CharField(max_length=50, null=True, blank=True)
    invoice = models.CharField(max_length=50, null=True, blank=True)
    Status = models.IntegerField(default=1, choices = prodStatus_choice)     
    isAuthorized = models.BooleanField(default=False)
    authorized_date = models.DateTimeField(null=True, blank=True)
    autorizedID = models.ForeignKey(catalogModel.authorizedBilling, on_delete=models.SET_NULL, db_column ='autorizedID', null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    createdBy = models.CharField(max_length=60, blank=True, null=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    updatedBy = models.CharField(max_length=60, blank=True, null=True)

    def __str__(self):
        return str(self.DailyID) + " - " + str(self.itemID)
    
    class Meta:
        unique_together = ('DailyID','itemID')


class DailyMobDocs(models.Model):
    DailyID = models.ForeignKey(DailyMob, on_delete=models.CASCADE, db_column ='DailyID', null=False, blank=False)    
    docType = models.IntegerField(default=1, choices = docType_choice)
    docName = models.CharField(max_length=200, blank=True, null=True)
    docDescription = models.CharField(max_length=200, blank=True, null=True)
    document = models.FileField(null=True, upload_to="dailys") 
    Status = models.IntegerField(default=1, choices = prodStatus_choice)     
    isAuthorized = models.BooleanField(default=False)
    authorized_date = models.DateTimeField(null=True, blank=True)
    autorizedID = models.ForeignKey(catalogModel.authorizedBilling, on_delete=models.SET_NULL, db_column ='autorizedID', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    createdBy = models.CharField(max_length=60, blank=True, null=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    updatedBy = models.CharField(max_length=60, blank=True, null=True)

    class Meta:        
        indexes = [            
            models.Index(fields=['DailyID', 'docType'], name='idx_dailymobdocs_daily_doctype'),            
            models.Index(fields=['created_date'], name='idx_dailymobdocs_created_date'),
        ]

    def __str__(self):
        return str(self.DailyID) + " - " + str(self.docType) + " - " + str(self.docName)