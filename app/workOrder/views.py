from ast import Try, parse
from django.contrib.auth.decorators import login_required
import xlwt
from django.core.mail import send_mail, EmailMessage
from django.core.files.base import ContentFile
from io import BytesIO
from contextlib import nullcontext, redirect_stderr
from ctypes.wintypes import WORD
from datetime import datetime, timedelta
from multiprocessing import context
from os import WIFCONTINUED, dup
import re
import os
import ssl
import smtplib
from django.conf import settings
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
from telnetlib import WONT
from unittest import TextTestResult
from urllib import response
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, redirect
from .models import *
from .resources import workOrderResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponse, FileResponse, HttpRequest
from django.db import IntegrityError
from .forms import * 
from sequences import get_next_value, Sequence
from datetime import date
from django.utils.dateparse import parse_date
import logging 
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.template.loader import get_template
from xhtml2pdf import pisa
from .classes import itemPriceList
from decimal import Decimal
from django.db.models import Max
from django.db.models import Sum
from .models import status_choice, prodStatus_choice, estimateStatus_choice
from mobile import models as MobileModel
from django.views.generic import View
from django.views.generic import CreateView
from django.http import JsonResponse
from django.db import transaction
from workOrder import models as catalogModel
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, F
import json
from dateutil import parser


@login_required(login_url='/home/')
def simple_upload(request):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    opType = "Access Option"
    opDetail = "upload Orders"
    logInAuditLog(request, opType, opDetail)

    countInserted = 0
    countRejected = 0
    duplicateRejected = 0
    if request.method == 'POST':
        #workOrder.objects.all().delete()
        workOrder_resource = workOrderResource()
        dataset = Dataset()
        new_workOrder = request.FILES['myfile']

        if not new_workOrder.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request,'upload.html', {'countInserted':countInserted, 'countRejected':countRejected})

        imported_data = dataset.load(new_workOrder.read(),format='xlsx', read_only = False)
    
        # return render(request,'upload.html',
        # {'imported_data':imported_data})

        for data in imported_data:  
            rowExist = workOrder.objects.filter(prismID=data[0]).first()
            if rowExist:
                countRejected = countRejected + 1
                try:
                    valueDuplicate = workOrderDuplicate(prismID = data[0],
                        workOrderId = data[1],
                        PO = data[2],
                        POAmount = data[3],
                        ConstType = data[4],
                        ConstCoordinator = data[5],
                        WorkOrderDate = data[6],
                        EstCompletion = data[7],
                        IssuedBy = data[8],
                        JobName = data[9],
                        JobAddress = data[10],
                        SiteContactName = data[11],
                        SitePhoneNumber = data[12],
                        Comments = data[13],
                        Status = data[14],
                        CloseDate = data[15],
                        WCSup = data[16],
                        UploadDate = data[17],
                        UserName = data[18]) 
                    valueDuplicate.save()
                except Exception as e:
                    duplicateRejected = duplicateRejected + 1
            else:
                try:         
                    value = workOrder(
                        prismID = data[0],
                        workOrderId = data[1],
                        PO = data[2],
                        POAmount = data[3],
                        ConstType = data[4],
                        ConstCoordinator = data[5],
                        WorkOrderDate = data[6],
                        EstCompletion = data[7],
                        IssuedBy = data[8],
                        JobName = data[9],
                        JobAddress = data[10],
                        SiteContactName = data[11],
                        SitePhoneNumber = data[12],
                        Comments = data[13],
                        Status = '1',
                        CloseDate = data[15],
                        UploadDate = data[17],
                        UserName = data[18],
                        uploaded = True,
                        createdBy = request.user.username,
                        created_date = datetime.now()
                    )
                    value.save()

                    log = woStatusLog( 
                                        woID = value,
                                        nextStatus = 1,
                                        createdBy = request.user.username,
                                        created_date = datetime.now()
                                    )
                    log.save()


                    countInserted = countInserted + 1
                except Exception as e:
                    countRejected = countRejected + 1
                    try:
                        valueDuplicate = workOrderDuplicate(prismID = data[0],
                            workOrderId = data[1],
                            PO = data[2],
                            POAmount = data[3],
                            ConstType = data[4],
                            ConstCoordinator = data[5],
                            WorkOrderDate = data[6],
                            EstCompletion = data[7],
                            IssuedBy = data[8],
                            JobName = data[9],
                            JobAddress = data[10],
                            SiteContactName = data[11],
                            SitePhoneNumber = data[12],
                            Comments = data[13],
                            Status = data[14],
                            CloseDate = data[15],
                            WCSup = data[16],
                            UploadDate = data[17],
                            UserName = data[18]) 
                        valueDuplicate.save()
                    except Exception as e:
                        duplicateRejected = duplicateRejected + 1            
    return render(request,'upload.html', {'countInserted':countInserted, 'countRejected':countRejected,'duplicateRejected':duplicateRejected, 'emp': emp, 'per':per})
    

@login_required(login_url='/home/')
def upload_payroll(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    


    opType = "Access Option"
    opDetail = "upload Payroll"
    logInAuditLog(request, opType, opDetail)


    countInserted = 0
    countRejected = 0
    countUpdated = 0
    if request.method == 'POST':
        dataset = Dataset()
        new_payroll = request.FILES['myfile']

        if not new_payroll.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request,'upload_payroll.html', {'countInserted':countInserted, 'countRejected':countRejected, 'countUpdated' : countUpdated  })

        imported_data = dataset.load(new_payroll.read(),format='xlsx')
      

        for data in imported_data:             
            try:         
                value = payroll(
                    location = data[0],
                    employee = data[3],
                    date =  data[2],
                    prismID = data[18],
                    workOrderId= data[19],
                    PO = data[20],
                    RT = data[5],
                    OT = data[6],
                    DT = data[7],
                    IT = data[8],
                    RTPrice = data[9],
                    OTPrice = data[10],
                    bonus = data[11],
                    production = data[12],
                    ownVehicle = data[13],
                    onCall = data[14],
                    payroll = data[15],
                    supervisor = data[16],
                    address = data[21],
                    itemTotal = data[46],
                    invoice = data[47],
                    pdfDaily = data[48]
                )
                value.save()

                if (data[23] != 0 and data[23] != " " and data[23] is not None):
                    value2 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[22],
                        quantity = data[23],
                        )
                    value2.save()

                if (data[25] != 0 and data[25] != " " and data[25] is not None):
                    value3 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[24],
                        quantity = data[25],
                        )
                    value3.save()

                if (data[27] != 0 and data[27] != " " and data[27] is not None):
                    value4 = payrollDetail(
                       location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[26],
                        quantity = data[27],
                        )
                    value4.save()

                if (data[29] != 0 and data[29] != " " and data[29] is not None):
                    value5 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[28],
                        quantity = data[29],
                        )
                    value5.save()

                if (data[31] != 0 and data[31] != " " and data[31] is not None):
                    value6 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[30],
                        quantity = data[31],
                        )
                    value6.save()
                
                if (data[33] != 0 and data[33] != " " and data[33] is not None):
                    value7 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[32],
                        quantity = data[33],
                        )
                    value7.save()
                
                if (data[35] != 0 and data[35] != " " and data[35] is not None):
                    value8 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[34],
                        quantity = data[35],
                        )
                    value8.save()

                if (data[37] != 0 and data[37] != " " and data[37] is not None):
                    value9 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[36],
                        quantity = data[37],
                        )
                    value9.save()

                if (data[39] != 0 and data[39] != " " and data[39] is not None):
                    value10 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[38],
                        quantity = data[39],
                        )
                    value10.save()
                
                if (data[41] != 0 and data[41] != " " and data[41] is not None):
                    value11 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[40],
                        quantity = data[41],
                        )
                    value11.save()

                if (data[43] != 0 and data[43] != " " and data[43] is not None):
                    value12 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[42],
                        quantity = data[43],
                        )
                    value12.save()

                if (data[45] != 0 and data[45] != " " and data[45] is not None):
                    value13 = payrollDetail(
                        location = data[0],
                        employee = data[3],
                        date =  data[2],
                        prismID = data[18],
                        workOrderId= data[19],
                        PO = data[20],
                        item = data[44],
                        quantity = data[45],
                        )
                    value13.save()

                # get de WO to update Location and Supervisor
                try:
                    wo = workOrder.objects.filter(prismID = data[18], workOrderId = data[19], PO = data[20]).first()
                    loc = Locations.objects.filter(LocationID = data[0]).first()
                    emp = Employee.objects.filter(employeeID = data[16] ).first()
                    if (wo and loc and emp):
                        wo.Location = loc
                        wo.WCSup = emp
                        wo.Status = '2'
                        wo.save()

                        # update WorkOrderId on Payroll
                        value.woId = wo
                        value.save()

                        countUpdated =  countUpdated + 1
                except Exception as e:
                    countUpdatedR =  countUpdatedR + 1

                countInserted = countInserted + 1
            except Exception as e:
                countRejected = countRejected + 1                
                       
    return render(request,'upload_payroll.html', {'countInserted':countInserted, 'countRejected':countRejected, 'countUpdated' : countUpdated, 'emp':emp, 'per': per})



@login_required(login_url='/home/')
def DeletedlistOrders(request):   
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    
    orders = DeletedWorkOrders.objects.all()
    context={}
    context["orders"]=orders
    
    return render(request,'deleted_order_list.html',context)
    
    

@login_required(login_url='/home/')
def listOrders(request):   
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    estatus = "0"
    loc = "0"
    pid = ""
    addR = ""
    invNumber=""
    invAmount=""
    invAmountF=""
    
    if emp:
        if emp.is_admin:
            locaList = employeeLocation.objects.filter(employeeID = emp)
                
            locationList = []
            locationList.append({'LocationID': emp.Location.LocationID, 'name':emp.Location.name })
            
            for i in locaList:
                locationList.append({'LocationID': i.LocationID.LocationID, 'name': i.LocationID.name} )
        else:
            locationList = Locations.objects.all()
    else:
        locationList = Locations.objects.all()

    opType = "Access Option"
    opDetail = "Order List"
    logInAuditLog(request, opType, opDetail)


    """ Adding  Order List with Problems
    woProblemList = []
    woPList = []
    if emp:
        if emp.is_superAdmin and request.user.username == "pismalej":
            ab = authorizedBilling.objects.filter(Status=1)       
            for i in ab:
                if i.quantity != 0:
                    iPriceA =  validate_decimals(i.total) / validate_decimals(i.quantity) 
                else:
                    iPriceA = 0

                woA = workOrder.objects.filter(id = i.woID.id).first()  
                itemD = DailyItem.objects.filter(DailyID__woID = woA, itemID = i.itemID).first()

                
                if itemD:
                    if  validate_decimals(iPriceA) != validate_decimals(itemD.price):
                        woProblemList.append(i.woID.id)
                    
            woPList = workOrder.objects.filter(id__in = woProblemList, Status = 2)
     """   


    """try:"""
    context={}

    if request.method == "POST":
        estatus = request.POST.get('status')
        loc = request.POST.get('location') 
        pid = request.POST.get('pid')
        invNumber = request.POST.get('invoiceNumber')
        invAmount = request.POST.get('invoiceAmount')
        invAmountF = request.POST.get('invoiceAmountF')
        addR = request.POST.get('address')
        if loc == None or loc =="":
            loc = "0"
        locationObject = Locations.objects.filter(LocationID=loc).first()
    
    context["selectEstatus"] = estatus    
    context["emp"]=emp
    context["location"]=locationList
    context["per"]=per    
    context["selectLoc"]=loc
    context["selectPID"]=pid
    context["selectedAddress"]=addR
    context["selectedAmount"]=invAmount
    context["selectedAmountF"]=invAmountF
    context["selectedInvoice"]=invNumber

    if pid == None or pid =="":
        context["selectPIDd"]="-1"
    else:
        context["selectPIDd"]=pid

    if addR == None or addR == "":
        context["selectedAddressd"]="-1"
    else:
        context["selectedAddressd"]=addR   

    if invAmount == None or invAmount == "":
        context["selectedAmountd"]="-1"
    else:
        context["selectedAmountd"]=invAmount

    if invAmountF == None or invAmountF == "":
        context["selectedAmountFd"]="-1"
    else:
        context["selectedAmountFd"]=invAmountF

    if invNumber == None or invNumber == "":
        context["selectedInvoiced"]="-1"
    else:
        context["selectedInvoiced"]=invNumber

    if emp:
        if emp.is_superAdmin:                
            if estatus == "0" and loc == "0":   
                if pid != None and pid != "":
                    orders = workOrder.objects.filter(prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)    
                elif addR != None and addR !="":
                    orders = workOrder.objects.filter(JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif invNumber !="" and invNumber != None:
                    
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                    
                elif  invAmount !="" and invAmount != None and invAmountF !="" and invAmountF != None:      
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                    
                elif  invAmount !="" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                else:  
                    #orders = woPList 
                    orders = workOrder.objects.filter(id = -1)   
                    
                    
            else:
                if estatus != "0" and loc != "0":
                    orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )     
                else:
                    if estatus != "0":
                        orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False ) 
                    else:
                        orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False ) 
            context["orders"]=orders
            context["day_diff"]=date_difference(orders)
            return render(request,'order_list.html',context)
        
        if emp.is_admin:  
            context["perfil"]="Admin"  
            
            locaList = employeeLocation.objects.filter(employeeID = emp)
                
            locationList = []
            locationList.append(emp.Location.LocationID)
            
            for i in locaList:
                locationList.append(i.LocationID.LocationID)
                    
            if emp.Location!= None:
                if estatus == "0" and loc == "0":                     
                    #orders = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False) 
                    if pid != None and pid != "":
                        orders = workOrder.objects.filter(prismID__exact = pid, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)    
                    elif addR != None and addR !="":
                        orders = workOrder.objects.filter(JobAddress__contains = addR, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                    elif invNumber !="" and invNumber != None:
                        
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                        
                    elif  invAmount !="" and invAmount != None and invAmountF !="" and invAmountF != None:      
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                        
                    elif  invAmount !="" and invAmount != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                    else:  
                        orders = workOrder.objects.filter(id = -1)   

                else:
                    if estatus != "0" and loc != "0":                          
                        orders = workOrder.objects.filter(Status = estatus, Location = loc).exclude(linkedOrder__isnull = False, uploaded = False )     
                    else:
                        if estatus != "0":                              
                            #orders = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 
                            #If estatus is 1 get all the locations

                            LocationExclude = Locations.objects.all().exclude(LocationID__in = locationList )

                            if estatus == "1":
                                orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False , Location__in = LocationExclude ) 
                            else:
                                orders = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 

                        else:                             
                            orders = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )                             
                            
            else:
                orders = None

            context["orders"]=orders
            if orders != None:
                context["day_diff"]=date_difference(orders)
            else:
                context["day_diff"] = None

            return render(request,'order_list.html',context)

    if request.user.is_staff:        
        if estatus == "0" and loc == "0":    
            
            if pid != None and pid != "":
                orders = workOrder.objects.filter(prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)    
            elif addR != None and addR !="":
                orders = workOrder.objects.filter(JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif invNumber !="" and invNumber != None:
                
                #Getting the OrderList by Invoice Number
                
                woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                woInvLits = []
                
                for i in woInv:
                    woInvLits.append(i.woID.id)
                orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                
            elif  invAmount !="" and invAmount != None and invAmountF !="" and invAmountF != None:      
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)  
            elif  invAmount !="" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)     
                
            else:  
                #orders = workOrder.objects.filter(id = -1)   
                last_date = date(2025, 3, 3)
                orders = workOrder.objects.filter(created_date__gte = last_date).exclude(linkedOrder__isnull = False, uploaded = False)
        
        else:
            if estatus != "0" and loc != "0":
                orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  
            else:
                if estatus != "0":
                    orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )  
                else:
                    orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  

        context["orders"]=orders

        context["day_diff"]=date_difference(orders)

        return render(request,'order_list.html',context)

    
    if estatus == "0" and loc == "0":   
        orders = workOrder.objects.filter(WCSup__isnull=True).exclude(linkedOrder__isnull = False, uploaded = False )
    else:
        if estatus != "0" and loc != "0":
            orders = workOrder.objects.filter(WCSup__isnull=True, Location = locationObject, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
        else:
            if estatus != "0":
                orders = workOrder.objects.filter(WCSup__isnull=True, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
            else:
                orders = workOrder.objects.filter(WCSup__isnull=True, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )
    
    """except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})"""
        

    return render(request,'order_list.html',context)

def get_optimized_orders(orders_queryset):
    """Apply prefetch_related to any orders queryset"""
    return orders_queryset.prefetch_related('woinvoice_set')

   
@login_required(login_url='/home/')
def order_list_location(request, userID):
    emp = Employee.objects.filter(user__username__exact = userID).first()
    per = period.objects.filter(status__in=(1,2)).first()
    if emp:
        orders = workOrder.objects.filter(Location__LocationID__exact=emp.Location.LocationID, WCSup__isnull=True)
        return render(request,'order_list_location.html',
        {'orders': orders, 'emp': emp, 'per': per })
    else:
        orders = workOrder.objects.filter(Location__LocationID__exact=0, WCSup__isnull=True)
        return render(request,'order_list_location.html',
        {'orders': orders, 'emp': emp, 'per': per })
    
@login_required(login_url='/home/')
def order_list_sup(request):      

    # emp = Employee.objects.filter(user__username__exact = userID).first()
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    opType = "Access Option"
    opDetail = "Orders Lists by Supervisor"
    logInAuditLog(request, opType, opDetail)

    locaList = employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append({'LocationID': emp.Location.LocationID, 'name':emp.Location.name })
    
    for i in locaList:
        locationList.append({'LocationID': i.LocationID.LocationID, 'name': i.LocationID.name} )


    estatus = "0"
    loc = "0"
    pid = ""
    invNumber = ""
    invAmount = ""
    invAmountF = ""
    addR=""
    
    """try:"""
    context={}

    if request.method == "POST":
        estatus = request.POST.get('status')
        loc = request.POST.get('location') 
        pid = request.POST.get('pid')
        invNumber = request.POST.get('invoiceNumber')
        invAmount = request.POST.get('invoiceAmount')
        invAmountF = request.POST.get('invoiceAmountF')
        addR = request.POST.get('address')
    
    
        if loc == None or loc =="":
            loc = "0"
        locationObject = Locations.objects.filter(LocationID=loc).first()
    
    context["selectEstatus"] = estatus    
    context["emp"]=emp
    context["location"]=locationList
    context["per"]=per    
    context["selectLoc"]=loc
    context["selectPID"]=pid
    context["selectedAddress"]=addR
    context["selectedAmount"]=invAmount
    context["selectedAmountF"]=invAmountF
    context["selectedInvoice"]=invNumber
    context["sup"]='True'


    if pid == None or pid =="":
        context["selectPIDd"]="-1"
    else:
        context["selectPIDd"]=pid

    if addR == None or addR == "":
        context["selectedAddressd"]="-1"
    else:
        context["selectedAddressd"]=addR   

    if invAmount == None or invAmount == "":
        context["selectedAmountd"]="-1"
    else:
        context["selectedAmountd"]=invAmount

    if invAmountF == None or invAmountF == "":
        context["selectedAmountFd"]="-1"
    else:
        context["selectedAmountFd"]=invAmountF

    if invNumber == None or invNumber == "":
        context["selectedInvoiced"]="-1"
    else:
        context["selectedInvoiced"]=invNumber


    if emp.is_manager:
        context["perfil"]="Manager" 
        locaList = employeeLocation.objects.filter(employeeID = emp)
                
        locationList = []
        locationList.append(emp.Location.LocationID)
        
        for i in locaList:
            locationList.append(i.LocationID.LocationID)

        if emp.Location!= None:
            if estatus == "0" and loc == "0":                   
                if pid != None and pid != "":
                    orders = workOrder.objects.filter(prismID__exact = pid, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif addR != None and addR !="":
                    orders = workOrder.objects.filter(JobAddress__contains = addR, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif invNumber !="" and invNumber != None:
                    
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)
                    orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                elif  invAmount !="" and invAmount != None and invAmountF !="" and invAmountF != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits , Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)  
                elif  invAmount !="" and invAmount != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False)    
                else:     
                    orders = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )            
            else:
                if estatus != "0" and loc != "0":
                    orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )                 
                else:
                    if estatus != "0":
                        orders = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )
                    else:    
                        orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )
        else:
            orders = None    
        
        context["orders"]=orders
        if orders != None:
            context["day_diff"]=date_difference(orders)
        else:
            context["day_diff"] = None

        return render(request,'order_list_sup.html',context)
    elif emp.is_supervisor:
        context["perfil"]="Supervisor" 
        if estatus == "0" and loc == "0":     
            if pid != None and pid != "":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif addR != None and addR !="":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif invNumber !="" and invNumber != None:
                
                #Getting the OrderList by Invoice Number
                
                woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                woInvLits = []
                
                for i in woInv:
                    woInvLits.append(i.woID.id)
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
            elif  invAmount !="" and invAmount != None and invAmountF !="" and invAmountF != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)  
            elif  invAmount !="" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)    
            else:     
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID).exclude(linkedOrder__isnull = False, uploaded = False )            
                #orders = None
                           
        else:
            if estatus != "0" and loc != "0":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )                 
            else:
                if estatus != "0":
                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
                else:    
                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )
        context["orders"]=orders
        if orders != None:
            context["day_diff"]=date_difference(orders)
        else:
            context["day_diff"] = None

        return render(request,'order_list_sup.html',context)
    else:
        orders = workOrder.objects.filter(WCSup__employeeID__exact=0, Location__isnull=False).exclude(linkedOrder__isnull = False, uploaded = False )
        context["orders"]=orders

        if orders != None:
            context["day_diff"]=date_difference(orders)
        else:
            context["day_diff"] = None

        return render(request,'order_list_sup.html',context)

def listOrdersFilter(request):
    orders = workOrder.objects.all()
    return render(request,'order_list.html',
    {'orders': orders})

@login_required(login_url='/home/')
def truncateData(request):
    workOrder.objects.all().delete()
    workOrderDuplicate.objects.all().delete()
    payroll.objects.all().delete()
    payrollDetail.objects.all().delete()
    # Locations.objects.all().delete()
    # Employee.objects.all().delete()
    return HttpResponse('<p>Data deleted successfully</p>')

@login_required(login_url='/home/')
def duplicatelistOrders(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    orders = workOrderDuplicate.objects.all().exclude(prismID = None, workOrderId = None, PO = None)

    opType = "Access Option"
    opDetail = "Duplicate Orders"
    logInAuditLog(request, opType, opDetail)


    per = period.objects.filter(status__in=(1,2)).first()
    return render(request,'duplicate_order_list.html',{'orders': orders, 'emp':emp, 'per':per})

@login_required(login_url='/home/')
def checkOrder(request, pID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    duplicateOrder = workOrderDuplicate.objects.filter(id=pID).first()

    orders = workOrder.objects.filter(prismID=duplicateOrder.prismID).first()

    opType = "Access Option"
    opDetail = "Check Orders"
    logInAuditLog(request, opType, opDetail)


    per = period.objects.filter(status__in=(1,2)).first()
    return render(request,'checkOrder.html',{'order': orders, 'dupOrder': duplicateOrder, 'emp':emp, 'per':per})

@login_required(login_url='/home/')
def order(request, orderID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    obj = get_object_or_404(workOrder, id = orderID)
 

    if emp.is_superAdmin or request.user.is_staff:
        form = workOrderFormAdmin(request.POST or None, instance = obj)
    else:
        form = workOrderForm(request.POST or None, instance = obj)

    status_update = (
    ('1', 'Not Started'),
    ('2', 'Work in Progress'),
    ('7', 'Ready to Bill'),
    ('8', 'RTB / Pending External Production'),
    ('3', 'Pending Docs'),
    ('4', 'Pending Revised WO'),
    ('5', 'Invoiced'),
    ('6', 'Transferred'),        
    )

    if obj.Status != '5':
        form.fields['Status'].choices = status_update

    is_used = False
    included_in = ""   


    #validate if WO is used in any Payroll   
    PayObj = catalogModel.payroll.objects.filter(woId = obj)
    if PayObj:
        is_used = True
        included_in = "Payroll"

    #validate if WO is used in any Authorized Billing   
    authorized_billing = authorizedBilling.objects.filter(woID = obj)
    if authorized_billing:
        is_used = True
        included_in = "Authorized Billing"

    #validate if WO is used in any Daily   
    daily = Daily.objects.filter(woID = obj)
    if daily:
        is_used = True
        included_in = "Daily"

    #validate if WO is used in any Status Log   
    """status_log = woStatusLog.objects.filter(woID = obj)
    if status_log:
        is_used = True
        included_in = "Status Log"""

    #validate if WO is used in any Comment Log   
    comment_log = woCommentLog.objects.filter(woID = obj)
    if comment_log:
        is_used = True
        included_in = "Comment Log"

    #validate if WO is used in any internalPO   
    internal_PO = internalPO.objects.filter(woID = obj)
    if internal_PO:
        is_used = True
        included_in = "Internal PO"

    
    #validate if WO is used in any External Production   
    external_production = externalProduction.objects.filter(woID = obj)
    if external_production:
        is_used = True
        included_in = "External Production"    

    #validate if WO is used in any woEstimate   
    wo_Estimate = woEstimate.objects.filter(woID = obj)
    if wo_Estimate:
        is_used = True
        included_in = "Estimate"    

    #validate if WO is used in any woInvoice   
    wo_Invoice = woInvoice.objects.filter(woID = obj)
    if wo_Invoice:
        is_used = True
        included_in = "Invoice"    

    #validate if WO is used in any woAdjustment    
    wo_Adjustment = woAdjustment.objects.filter(woID = obj)
    if wo_Adjustment:
        is_used = True
        included_in = "Adjustment"    

    #validate if WO is used in any DailyMobile     
    daily_Mobile = MobileModel.DailyMob.objects.filter(woID = obj)
    if daily_Mobile:
        is_used = True
        included_in = "Daily Mobile"    



    if form.is_valid(): 
        anterior = workOrder.objects.filter(id = orderID).first()    
         
        if form.instance.Status != anterior.Status:
            form.instance.UploadDate = datetime.now()
            log = woStatusLog( 
                            woID = anterior,
                            currentStatus = anterior.Status,
                            nextStatus = form.instance.Status,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
            log.save()
        form.save()       
        return HttpResponseRedirect('/order_detail/' + str(form.instance.id) + '/False')
 
    context["form"] = form
    context["emp"] = emp
    context["is_used"] = is_used
    context["included_in"] = included_in
    return render(request, "order.html", context)

@login_required(login_url='/home/')
@transaction.atomic
def delete_order(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    try:       
                
        obj = get_object_or_404(workOrder, id = id)
        
        #Moving WO to Deleted WO table
        delWO = DeletedWorkOrders.objects.create(
            prismID = obj.prismID,
            workOrderId = obj.workOrderId,
            PO = obj.PO,
            POAmount = obj.POAmount,
            ConstType = obj.ConstType,
            ConstCoordinator = obj.ConstCoordinator,
            WorkOrderDate = obj.WorkOrderDate,           
            EstCompletion = obj.EstCompletion,
            IssuedBy = obj.IssuedBy,
            JobName = obj.JobName,
            JobAddress = obj.JobAddress,
            SiteContactName = obj.SiteContactName,
            SitePhoneNumber = obj.SitePhoneNumber,
            Comments = obj.Comments,                        
            Status = obj.Status,
            CloseDate = obj.CloseDate,
            WCSup = obj.WCSup,
            UploadDate = obj.UploadDate,
            UserName = obj.UserName,
            Location = obj.Location,
            uploaded = obj.uploaded,
            linkedOrder = obj.linkedOrder,
            pre_invoice = obj.pre_invoice,
            invoice = obj.invoice,
            invoiceFile = obj.invoiceFile,
            created_date = obj.created_date,
            createdBy = obj.createdBy,
            deleted_date = datetime.now(),
            deletedBy = request.user.username
        )
        
        
        #If Everything is ok then delete the WO and all the related records                
        
        status_log = woStatusLog.objects.filter(woID = obj)
        status_log.delete()

        obj.delete()
        
        return HttpResponseRedirect('/order_list/')
    except Exception as e:
        
        context["message"] = "Somenthing went Wrong! " + str(e)
        return render(request, "order.html", context)

@login_required(login_url='/home/')
@transaction.atomic    
def restore_delete_order(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    try:       
                
        obj = get_object_or_404(DeletedWorkOrders, id = id)
        
        #Moving Deleted WO to WO table
        WO = workOrder.objects.create(
            prismID = obj.prismID,
            workOrderId = obj.workOrderId,
            PO = obj.PO,
            POAmount = obj.POAmount,
            ConstType = obj.ConstType,
            ConstCoordinator = obj.ConstCoordinator,
            WorkOrderDate = obj.WorkOrderDate,           
            EstCompletion = obj.EstCompletion,
            IssuedBy = obj.IssuedBy,
            JobName = obj.JobName,
            JobAddress = obj.JobAddress,
            SiteContactName = obj.SiteContactName,
            SitePhoneNumber = obj.SitePhoneNumber,
            Comments = obj.Comments,                        
            Status = obj.Status,
            CloseDate = obj.CloseDate,
            WCSup = obj.WCSup,
            UploadDate = obj.UploadDate,
            UserName = obj.UserName,
            Location = obj.Location,
            uploaded = obj.uploaded,
            linkedOrder = obj.linkedOrder,
            pre_invoice = obj.pre_invoice,
            invoice = obj.invoice,
            invoiceFile = obj.invoiceFile,
            created_date = obj.created_date,
            createdBy = obj.createdBy            
        )
        
        
        #If Everything is ok then delete the WO restored

        obj.delete()
        
        return HttpResponseRedirect('/deleted_order_list/')
    except Exception as e:
        
        context["message"] = "Somenthing went Wrong! " + str(e)
        return render(request, "deleted_order_detail.html", context)
    
def restore_delete_internal_po(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    try:       
                
        obj = get_object_or_404(DeletedInternalPO, id = id)
        
        #Moving Deleted Internal PO to Internal PO  table
        
        internalPO.objects.create(
            poNumber = obj.poNumber,
            woID = obj.woID_d,
            vendor = obj.vendor,
            supervisor= obj.supervisor_d,
            pickupEmployee = obj.pickupEmployee_d,
            product = obj.product,
            quantity = obj.quantity,
            total = obj.total,
            nonBillable = obj.nonBillable,
            isAmountRounded = obj.isAmountRounded,
            estimate = obj.estimate,
            invoice = obj.invoice,
            Status = obj.Status,
            receipt = obj.receipt,
            transferFromPO = obj.transferFromPO_d,
            transferToPO = obj.transferToPO_d,
            transfer_date = obj.transfer_date,
            transferBy = obj.transferBy,
            created_date = obj.created_date,
            createdBy = obj.createdBy            
        )
        
        #If Everything is ok then delete the WO restored

        obj.delete()
        
        return HttpResponseRedirect('/deleted_internal_po_list/')
    except Exception as e:
        
        context["message"] = "Somenthing went Wrong! " + str(e)
        return render(request, "update_deleted_po.html", context)
    

@login_required(login_url='/home/')
def order_supervisor(request, orderID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(workOrder, id = orderID)
 
    form = workOrderForm(request.POST or None, instance = obj)

    if form.is_valid(): 
        form.save()       
        return HttpResponseRedirect('/order_list_sup/')
 
    context["form"] = form
    context["emp"] = emp
    return render(request, "order_supervisor.html", context)

@login_required(login_url='/home/')
def updateDupOrder(request,pID, dupID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
   

    try:
        dupOrder = workOrderDuplicate.objects.filter(id=dupID).first()

        primaryOrder = workOrder.objects.filter(id = pID).first()
        
        enabled_status = ['2','3','4','5','7','8']

        if str(primaryOrder.Status) in enabled_status:
            order = workOrder.objects.filter(id = pID).first()
            primaryOrder.prismID = dupOrder.prismID
            primaryOrder.workOrderId = dupOrder.workOrderId
            primaryOrder.PO = dupOrder.PO
            primaryOrder.POAmount = dupOrder.POAmount
            primaryOrder.ConstType = dupOrder.ConstType
            primaryOrder.ConstCoordinator = dupOrder.ConstCoordinator
            primaryOrder.WorkOrderDate = dupOrder.WorkOrderDate
            primaryOrder.EstCompletion = dupOrder.EstCompletion
            primaryOrder.IssuedBy = dupOrder.IssuedBy
            primaryOrder.JobName = dupOrder.JobName
            primaryOrder.JobAddress = dupOrder.JobAddress
            primaryOrder.SiteContactName = dupOrder.SiteContactName
            primaryOrder.SitePhoneNumber = dupOrder.SitePhoneNumber
            primaryOrder.Comments = "Original: " + order.prismID + "-" + order.workOrderId + "-" + order.PO + ". " + str(dupOrder.Comments)                   
            primaryOrder.CloseDate = dupOrder.CloseDate
            primaryOrder.UploadDate = datetime.now()
            primaryOrder.UserName = dupOrder.UserName
            primaryOrder.uploaded = True
            primaryOrder.createdBy = request.user.username
            primaryOrder.created_date = datetime.now()      
            primaryOrder.save()        
            dupOrder.delete()

        else:
            order = workOrder(  id = pID,
                                prismID = dupOrder.prismID,
                                workOrderId = dupOrder.workOrderId,
                                PO = dupOrder.PO,
                                POAmount = dupOrder.POAmount,
                                ConstType = dupOrder.ConstType,
                                ConstCoordinator = dupOrder.ConstCoordinator,
                                WorkOrderDate = dupOrder.WorkOrderDate,
                                EstCompletion = dupOrder.EstCompletion,
                                IssuedBy = dupOrder.IssuedBy,
                                JobName = dupOrder.JobName,
                                JobAddress = dupOrder.JobAddress,
                                SiteContactName = dupOrder.SiteContactName,
                                SitePhoneNumber = dupOrder.SitePhoneNumber,
                                Comments = "Original: " + primaryOrder.prismID + "-" + primaryOrder.workOrderId + "-" + primaryOrder.PO + ". " + str(dupOrder.Comments) ,
                                Location = dupOrder.Location,
                                Status = '1',
                                CloseDate = dupOrder.CloseDate,
                                UploadDate = datetime.now(),
                                UserName = dupOrder.UserName,
                                uploaded = True,
                                createdBy = request.user.username,
                                created_date = datetime.now() )        
            order.save()        
            dupOrder.delete()

            log = woStatusLog( 
                                woID = order,
                                nextStatus = 1,
                                createdBy = request.user.username,
                                created_date = datetime.now()
                                )
            log.save()

        return render(request,'landing.html',{'message':'Order Updated Successfully', 'alertType':'success', 'emp':emp, 'per': per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong! ' + str(e), 'alertType':'danger', 'emp':emp, 'per':per})

@login_required(login_url='/home/')
def insertDupOrder(request, dupID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    try:
        dupOrder = workOrderDuplicate.objects.filter(id=dupID).first()
         
        order = workOrder(  prismID = dupOrder.prismID,
                            workOrderId = dupOrder.workOrderId,
                            PO = dupOrder.PO,
                            POAmount = dupOrder.POAmount,
                            ConstType = dupOrder.ConstType,
                            ConstCoordinator = dupOrder.ConstCoordinator,
                            WorkOrderDate = dupOrder.WorkOrderDate,
                            EstCompletion = dupOrder.EstCompletion,
                            IssuedBy = dupOrder.IssuedBy,
                            JobName = dupOrder.JobName,
                            JobAddress = dupOrder.JobAddress,
                            SiteContactName = dupOrder.SiteContactName,
                            SitePhoneNumber = dupOrder.SitePhoneNumber,
                            Comments = dupOrder.Comments,
                            Status = '1',
                            CloseDate = dupOrder.CloseDate,
                            UploadDate = dupOrder.UploadDate,
                            UserName = dupOrder.UserName,
                            uploaded = True,
                            createdBy = request.user.username,
                            created_date = datetime.now() )
        order.save()
        dupOrder.delete()

        log = woStatusLog( 
                            woID = order,
                            nextStatus = 1,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
        log.save()

        return render(request,'landing.html',{'message':'Order Inserted Successfully', 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        print(e)
        return render(request,'landing.html',{'message':'Somenthing went Wrong! ' + str(e), 'alertType':'danger','emp':emp, 'per': per})

@login_required(login_url='/home/')
def deleteDupOrder(request,pID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    try:
        dupOrder = workOrderDuplicate.objects.filter(id=pID).first()
        dupOrder.delete()
        return render(request,'landing.html',{'message':'Order Discarded Successfully', 'alertType':'success', 'emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!', 'alertType':'danger','emp':emp, 'per':per})

@login_required(login_url='/home/')
def create_order(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    woID = 'E-'
    form = workOrderForm(request.POST or None, initial={'prismID': woID,'workOrderId': woID, 'PO': woID})
    if form.is_valid():
        woNumber = Sequence("wo") 
        woID = str(woNumber.get_next_value())
        woID = 'E-' + woID 
        form.instance.prismID = woID
        form.instance.workOrderId = woID
        form.instance.PO = woID
        form.instance.Status = 1
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()


        log = woStatusLog( 
                            woID = form.instance,
                            nextStatus = 1,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
        log.save()

        return HttpResponseRedirect('/order_list/')
         
    context['form']= form
    context['emp'] = emp
    return render(request, "order.html", context)

@login_required(login_url='/home/')
def create_location(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    opType = "Access Option"
    opDetail = "Locations Catalog"
    logInAuditLog(request, opType, opDetail)


    form = LocationsForm(request.POST or None)
    if form.is_valid():
        form.save()
        context["dataset"] = Locations.objects.all()   
        context["emp"]=emp      
        return render(request, "location_list.html", context)
         
    context['form']= form
    context["emp"]=emp
    return render(request, "location.html", context)

@login_required(login_url='/home/')
def location_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    context["dataset"] = Locations.objects.all()
    context["emp"] = emp
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
         
    return render(request, "location_list.html", context)
@login_required(login_url='/home/')
def update_location(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    obj = get_object_or_404(Locations, LocationID = id)
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    form = LocationsForm(request.POST or None, instance = obj)
 
    if form.is_valid():
        form.save()
        context["dataset"] = Locations.objects.all() 
        context["emp"] = emp       
        return render(request, "location_list.html", context)

    context["form"] = form
    context["emp"] = emp
    return render(request, "update_location.html", context)

@login_required(login_url='/home/')
def employee_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 

    opType = "Access Option"
    opDetail = "Employee List"
    logInAuditLog(request, opType, opDetail)




    context["dataset"] = Employee.objects.all()
    context["emp"]= emp
    return render(request, "employee_list.html", context)


@login_required(login_url='/home/')
def create_employee(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()

    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    form = EmployeesForm(request.POST or None, request.FILES)

    if form.is_valid():
        empSeq = Sequence("emp", initial_value=1500) 
        empID = str(empSeq.get_next_value())       
        form.instance.employeeID = empID
        form.save()
        # Return to Locations List
        return HttpResponseRedirect('/employee_list/')
        # context["dataset"] = Employee.objects.all()     
        # context["emp"] = emp    
        # return render(request, "employee_list.html", context)
         
    context['form']= form
    context["emp"] = emp
    return render(request, "create_employee.html", context)

@login_required(login_url='/home/')
def update_employee(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(Employee, employeeID = id)
 
    form = EmployeesForm(request.POST or None, request.FILES or None, instance = obj)
 
    if form.is_valid():
        form.save()
        context["dataset"] = Employee.objects.all()  
        context["emp"] = emp       
        return render(request, "employee_list.html", context)

    context["form"] = form
    context["emp"] = emp
    return render(request, "create_employee.html", context)

@login_required(login_url='/home/')
def linkOrderList(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["order"] = workOrder.objects.filter(id=id).first()
    context["manOrders"] = workOrder.objects.filter(uploaded = False, linkedOrder__isnull = True)
    context["emp"] = emp
    return render(request, "link_order_list.html", context)

@login_required(login_url='/home/')
def linkOrder(request, id, manualid):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["order"] = workOrder.objects.filter(id=id).first()
    context["manOrder"] = workOrder.objects.filter(id=manualid).first()
    context["emp"] = emp
    return render(request, "link_order.html", context)

@login_required(login_url='/home/')
def updateLinkOrder(request, id, manualid):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    try:
        order = workOrder.objects.filter(id=id).first()
        order.linkedOrder = "updated"
        order.save ()

        manOrder = workOrder.objects.filter(id=manualid).first()
        manOrder.linkedOrder = id
        manOrder.save()
        
        order.Status = manOrder.Status
        order.Location = manOrder.Location
        order.save()
        
        #Se traslada produccion si la hay a la nueva orden
        
        prod = Daily.objects.filter(woID = manOrder)
        
        for p in prod:
            temProd = Daily.objects.filter(id = p.id).first()
            temProd.woID = order
            temProd.save()
        
        #Se traslada internal PO
        
        internal = internalPO.objects.filter(woID = manOrder)
        
        for i in internal:
            temInternal = internalPO.objects.filter(id = i.id).first()
            temInternal.woID = order
            temInternal.save()
            
        #Se traslada external Production
        
        external = externalProduction.objects.filter(woID = manOrder)
        
        for e in external:
            temExternal = externalProduction.objects.filter(id = e.id).first()
            temExternal.woID = order
            temExternal.save()
        
        
        # Se traslada Producción Autorizada

        authBilling = authorizedBilling.objects.filter(woID = manOrder)

        for ab in authBilling:
            temAB = authorizedBilling.objects.filter(id = ab.id).first()
            temAB.woID = order
            temAB.save()

        # Se traslada estimate

        estimate = woEstimate.objects.filter(woID = manOrder)

        for es in estimate:
            temEst = woEstimate.objects.filter(id = es.id).first()
            temEst.woID = order
            temEst.save()


        # Se traslada Invoice
        invoice = woInvoice.objects.filter(woID = manOrder)

        for inv in invoice:
            temInv = woInvoice.objects.filter(id = inv.id).first()
            temInv.woID = order
            temInv.save()


        return render(request,'landing.html',{'message':'Order Linked Successfully', 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})

@login_required(login_url='/home/')
def item_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    context["items"] = item.objects.all()
    context["emp"] = emp
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    


    opType = "Access Option"
    opDetail = "Item List"
    logInAuditLog(request, opType, opDetail)


    return render(request, "item_list.html", context)

@login_required(login_url='/home/')
def create_item(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    form = ItemForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/item_list/")
         
    context['form']= form
    context["emp"]=emp
    return render(request, "create_item.html", context)

@login_required(login_url='/home/')
def update_item(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(item, itemID = id)
 
    form = ItemForm(request.POST or None, instance = obj)

    is_used = False
    included_in = ""

    #validate if the item is used in any work order
    item_price = itemPrice.objects.filter(item = id)

    for ip in item_price:

        #validate if item_price is used in any authorizedBilling
        authorized_billing = authorizedBilling.objects.filter(itemID = ip)
        if authorized_billing:
            is_used = True
            included_in = "Authorized Billing"
        #validate if item_price is used in any DailyItem
        daily_item = DailyItem.objects.filter(itemID = ip)
        if daily_item:
            is_used = True
            included_in = "Daily Items"
          #validate if item_price is used in any externalProdItem   
        external_prod_item = externalProdItem.objects.filter(itemID = ip)
        if external_prod_item:
            is_used = True
            included_in = "External Production Items"
        #validate if item_price is used in any DailyMobItem
        daily_mob_item = MobileModel.DailyMobItem.objects.filter(itemID = ip)
        if daily_mob_item:
            is_used = True
            included_in = "Daily Mobile Items"

    if form.is_valid():
        form.save() 
        return HttpResponseRedirect("/item_list/")

    context["form"] = form
    context["emp"] = emp
    context["is_used"] = is_used
    context["included_in"] = included_in   
    
    return render(request, "update_item.html", context)

@login_required(login_url='/home/')
@transaction.atomic
def delete_item(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    try:
        obj = get_object_or_404(item, itemID = id)

        item_price = itemPrice.objects.filter(item = obj)
        
        for ip in item_price:
            #validate if the item is used in any work order
            item_price = itemPrice.objects.filter(id = ip.id)

            item_price.delete()
        

        obj.delete()

        return HttpResponseRedirect("/item_list/")
    except Exception as e:
        return render(request, "update_item.html", context)
    

@login_required(login_url='/home/')
def item_price(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    context["item"] = item.objects.filter(itemID = id).first()
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    context["item_location"] = itemPrice.objects.filter(item = id)
    context["emp"] = emp

    return render(request, "item_price.html", context)

@login_required(login_url='/home/')
def create_item_price(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    it = item.objects.filter(itemID=id).first()
    form = ItemPriceForm(request.POST or None, initial={'item': it})
    if form.is_valid():
        form.save()    
        return HttpResponseRedirect("/item_price/" + id)           
        
         
    context['form']= form
    context["emp"] = emp
    context["itemID"] = id
    return render(request, "create_item_price.html", context)

@login_required(login_url='/home/')
def update_item_price(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(itemPrice, id = id )
 
    form = ItemPriceForm(request.POST or None, instance = obj)
 
    if form.is_valid():
        form.save()       
        return HttpResponseRedirect("/item_price/" + obj.item.itemID)


    context["form"] = form
    context["emp"] = emp
    context["itemID"] = obj.item.itemID
    return render(request, "update_item_price.html", context)

@login_required(login_url='/home/')
def po_list(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    context["po"] = internalPO.objects.filter(woID = wo)
    context["emp"] = emp

    vendorList = vendorSubcontrator(request) 
    context["vendorList"] = vendorList


    return render(request, "po_order_list.html", context)


@login_required(login_url='/home/')
def deleted_internal_po_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()


    context = {}  
    poStatus = "0"
    woStatus = "0"
    poNumber = ""
    pid = ""
    
    context["per"] = per
    context["selectEstatus"] = "-1"
    context["selectWOEstatus"] = "-1"
    context["emp"] = emp

    vendorList = vendorSubcontrator(request) 
    context["vendorList"] = vendorList
    
    context["po"] = DeletedInternalPO.objects.all().order_by('-id')


    return render(request, "deleted_internal_po_list.html", context)

@login_required(login_url='/home/')
def internal_po_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()


    context = {}  
    poStatus = "0"
    woStatus = "0"
    poNumber = ""
    pid = ""
    
    context["per"] = per
    context["selectEstatus"] = "-1"
    context["selectWOEstatus"] = "-1"
    context["emp"] = emp

    vendorList = vendorSubcontrator(request) 
    context["vendorList"] = vendorList

    

    opType = "Access Option"
    opDetail = "Internal PO List"
    logInAuditLog(request, opType, opDetail)


    if request.method == 'POST':       
        poStatus = request.POST.get('status')
        woStatus = request.POST.get('woStatus')
        poNumber = request.POST.get('poNumber')
        pid = request.POST.get('pid')
        context["selectEstatus"] = poStatus
        context["selectWOEstatus"] = woStatus
        context["selectedPO"] = poNumber
        context["selectedPID"] = pid
   

        if poStatus == "0" and woStatus == "0":
            if poNumber != "" and pid != "":
                context["po"] = internalPO.objects.filter(poNumber = poNumber, woID__prismID = pid).order_by('-id')
            else:
                if pid != "":
                    context["po"] = internalPO.objects.filter(woID__prismID = pid).order_by('-id')
                elif poNumber != "":
                    context["po"] = internalPO.objects.filter(poNumber = poNumber).order_by('-id')
                else:
                    context["po"] = internalPO.objects.filter(id = -1).order_by('-id')
        elif poStatus != "0" and woStatus == "0":
            if poNumber != "" and pid != "":
                context["po"] = internalPO.objects.filter(Status=poStatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
            else:
                if pid != "":
                    context["po"] = internalPO.objects.filter(Status=poStatus, woID__prismID = pid).order_by('-id')
                elif poNumber != "":
                    context["po"] = internalPO.objects.filter(Status=poStatus, poNumber = poNumber).order_by('-id')
                else:
                    context["po"] = internalPO.objects.filter(Status=poStatus).order_by('-id')
        elif poStatus == "0" and woStatus != "0":
            if poNumber != "" and pid != "":
                context["po"] = internalPO.objects.filter(woID__Status=woStatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
            else:
                if pid != "":
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus, woID__prismID = pid).order_by('-id')
                elif poNumber != "":
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus, poNumber = poNumber).order_by('-id')
                else:
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus).order_by('-id')
        else:
            if poNumber != "" and pid != "":
                context["po"] = internalPO.objects.filter(woID__Status=woStatus,Status=poStatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
            else:
                if pid != "":
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus, Status=poStatus, woID__prismID = pid).order_by('-id')
                elif poNumber != "":
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus, Status=poStatus, poNumber = poNumber).order_by('-id')
                else:
                    context["po"] = internalPO.objects.filter(woID__Status=woStatus, Status=poStatus).order_by('-id')

        


        """
        if poStatus != "0":
                    if poNumber != "" and pid != "":
                        context["po"] = internalPO.objects.filter(Status=poStatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
                    else:
                        if pid != "":
                            context["po"] = internalPO.objects.filter(Status=poStatus, woID__prismID = pid).order_by('-id')
                        elif poNumber != "":
                            context["po"] = internalPO.objects.filter(Status=poStatus, poNumber = poNumber).order_by('-id')
                        else:
                            context["po"] = internalPO.objects.filter(Status=poStatus).order_by('-id')
                else:
                    if poNumber != "" and pid != "":
                        context["po"] = internalPO.objects.filter(poNumber = poNumber, woID__prismID = pid).order_by('-id')
                    else:
                        if pid != "":
                            context["po"] = internalPO.objects.filter(woID__prismID = pid).order_by('-id')
                        elif poNumber != "":
                            context["po"] = internalPO.objects.filter(poNumber = poNumber).order_by('-id')
                        else:
                            context["po"] = internalPO.objects.filter(id = -1).order_by('-id')
        """
    

    if poStatus == None or poStatus == "":
        context["selectEstatusd"] = "-1"
    else:
        context["selectEstatusd"] = poStatus
    
    if woStatus == None or woStatus == "":
        context["selectWOEstatusd"] = "-1"
    else:
        context["selectWOEstatusd"] = woStatus
    
    if poNumber == None or poNumber =="":        
        context["selectedPOd"] = "-1"
    else:
        context["selectedPOd"] = poNumber

    if pid == None or pid == "":
        context["selectedPIDd"] = "-1"
    else: 
        context["selectedPIDd"] = pid

    context["status_choices"] = status_choice
    context["prodStatus_choices"] = prodStatus_choice

    return render(request, "internal_po_list.html", context)


@login_required(login_url='/home/')
def get_internal_po_list(request,estatus,woEstatus,poNumber, pid):
    

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Internal PO', cell_overwrite_ok = True) 

    # Sheet header, first row
    row_num = 7

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color light_blue;')

    font_style =  xlwt.XFStyle()              

       


    columns = ['Vendor', 'PO', 'WO ID', 'Supervisor','Total','Non Billable','Created Date', 'Created By', 'Status','Transfer From', 'Transfer Date','Transfer By']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
    

    if estatus == "0" and woEstatus == "0":
        if poNumber != "" and pid != "":
            ordenes = internalPO.objects.filter(poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(poNumber = poNumber).order_by('-id')
            else:
                ordenes = internalPO.objects.filter(id = -1).order_by('-id')
    elif str(estatus) != "0" and str(woEstatus) == "0":
        if poNumber != "-1" and pid != "-1":
            ordenes = internalPO.objects.filter(Status=estatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(Status=estatus, woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(Status=estatus, poNumber = poNumber).order_by('-id')
            else:
                ordenes = internalPO.objects.filter(Status=estatus).order_by('-id')
    elif estatus == "0" and woEstatus != "0":
        if poNumber != "-1" and pid != "-1":
            ordenes = internalPO.objects.filter(woID__Status=woEstatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(woID__Status=woEstatus, woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(woID__Status=woEstatus, poNumber = poNumber).order_by('-id')
            else:
                ordenes = internalPO.objects.filter(woID__Status=woEstatus).order_by('-id')
    else:
        if poNumber != "-1" and pid != "-1":
            ordenes = internalPO.objects.filter(woID__Status=woEstatus,Status=estatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(woID__Status=woEstatus, Status=estatus, woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(woID__Status=woEstatus, Status=estatus, poNumber = poNumber).order_by('-id')
            else:
                ordenes = internalPO.objects.filter(woID__Status=woEstatus, Status=estatus).order_by('-id')

    
    """if estatus != "0":
        if poNumber != "-1" and pid != "-1":
            ordenes = internalPO.objects.filter(Status=estatus, poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(Status=estatus, woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(Status=estatus, poNumber = poNumber).order_by('-id')
            else:
               ordenes = internalPO.objects.filter(Status=estatus).order_by('-id')
    else:
        if poNumber != "-1" and pid != "-1":
            ordenes= internalPO.objects.filter(poNumber = poNumber, woID__prismID = pid).order_by('-id')
        else:
            if pid != "-1":
                ordenes = internalPO.objects.filter(woID__prismID = pid).order_by('-id')
            elif poNumber != "-1":
                ordenes = internalPO.objects.filter(poNumber = poNumber).order_by('-id')
            else:
                ordenes = internalPO.objects.filter(id = -1).order_by('-id')"""
                

    for item in ordenes:
        row_num += 1
        ws.write(row_num, 0, item.vendor, font_style) # at 0 row 0 column 
        ws.write(row_num, 1, item.poNumber, font_style) # at 0 row 0 column 
        ws.write(row_num, 2, item.woID.prismID, font_style) # at 0 row 0 column 
        if item.supervisor != None:
            ws.write(row_num, 3, item.supervisor.first_name + " " + item.supervisor.last_name, font_style)
        else:
            ws.write(row_num, 3, " ", font_style)

        ws.write(row_num, 4, item.total, font_style) 
        ws.write(row_num, 5, item.nonBillable, font_style)
        if item.transfer_date != None: 
            ws.write(row_num, 6, item.created_date.strftime("%m/%d/%Y"), font_style) 
        else:
            ws.write(row_num, 6, "", font_style) 
            
        ws.write(row_num, 7, item.createdBy, font_style) 

        if item.Status == 1:
             ws.write(row_num, 8, "Open", font_style) 
        elif item.Status == 2:
             ws.write(row_num, 8, "Estimated", font_style) 
        elif item.Status == 3:
             ws.write(row_num, 8, "Invoiced", font_style)
        else:
             ws.write(row_num, 8, "", font_style)
        
        
        if item.transferFromPO != None:
            ws.write(row_num, 9, item.transferFromPO.prismID + "-" + item.transferFromPO.workOrderId + "-" + item.transferFromPO.PO, font_style) 
        else:
            ws.write(row_num, 9, "", font_style) 

        if item.transfer_date != None:
            ws.write(row_num, 10, item.transfer_date.strftime("%m/%d/%Y"), font_style) 
        else:
            ws.write(row_num, 10, "", font_style) 
            
        ws.write(row_num, 11, item.transferBy, font_style) 

        

        ws.col(3).width = 5000
        ws.col(5).width = 3500
        ws.col(9).width = 7000


    filename = 'Internal PO.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response    

@login_required(login_url='/home/')
def update_po(request, id, woID, selectedvs):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["woID"] = int(woID)

    context["po"] = internalPO.objects.filter(id = id).first()
    context["id"] = id


    vendorList = vendorSubcontrator(request)

    context['vendorList']= vendorList

    obj = get_object_or_404(internalPO, id = id )

    

    # To Unlink the PO 
    if obj.Status == 2:
        if obj.estimate != None:
            woEst = woEstimate.objects.filter(estimateNumber = obj.estimate).first()        

            if woEst:               
                context['unlink']= True
            else:
                context['unlink']= False
        else:
            context['unlink']= False

    elif obj.Status == 3:
        if obj.invoice != None:
            woInv = woInvoice.objects.filter(invoiceNumber = obj.invoice).first()                    
            if woInv:

                # validate if thw WO has a Final Invoice
                finalInv = woInvoice.objects.filter(woID = obj.woID,is_partial = False).count()

                if woInv.is_partial and finalInv == 0:
                    context['unlink']= True
                else:
                    context['unlink']= False
        else:

            context['unlink']= False



    if selectedvs != "0":
        itemResult = next((i for i, item in enumerate(vendorList) if item["id"] == selectedvs), None)
    else:
        itemResult = next((i for i, item in enumerate(vendorList) if item["id"] == obj.vendor), None)


    if itemResult != None:
        context['selectedvs2'] = vendorList[itemResult]
    else:
        context['selectedvs2'] = ""    

    if (request.user.is_staff or emp.is_superAdmin) and obj.Status == 1:
        form = InternalPOFormAdminUpdate(request.POST or None, instance = obj )
    elif request.user.is_staff or emp.is_superAdmin:
        form = InternalPOFormAdmin(request.POST or None, instance = obj )
    elif emp.accounts_payable:
        form = InternalPOFormAccounPay(request.POST or None, instance = obj )
    else:
        form = InternalPOForm(request.POST or None, instance = obj )

    
    status_update = (
    (1, 'Open'),
    (3, 'Invoiced'),
    )

    if obj.Status == 1:
        context["status_update"] = "Permitido de Open a Invoiced"
        form.fields['Status'].choices = status_update


    
    context["order"] = obj.woID.prismID + " - " + obj.woID.workOrderId + " - " + obj.woID.PO
    context["order"] = obj.woID.prismID + " - " + obj.woID.workOrderId + " - " + obj.woID.PO

    if obj.transferFromPO:
        context["transferFromPO"] = obj.transferFromPO.prismID + " - " + obj.transferFromPO.workOrderId + " - " + obj.transferFromPO.PO 
    else: 
        context["transferFromPO"] = ""
 
    if form.is_valid():
        vendor = request.POST.get('vendor') 
        
        if vendor == "0":
            form.instance.vendor = None
        else:
            form.instance.vendor = vendor


        if form.instance.poNumber == None:
            form.instance.poNumber = form.instance.id

        try:         
            newFile = request.FILES['myfile']
            form.instance.receipt = newFile

        except Exception as e:
            None

        form.instance.updatedBy = request.user.username
        form.instance.updated_date = datetime.now()
            
        form.save()

        if int(woID) > 0:
            return HttpResponseRedirect("/po_list/" + str(obj.woID.id))
        elif int(woID) < 0:
            return HttpResponseRedirect("/billing_list/" + str(obj.woID.id) + "/False")
        else:
            return HttpResponseRedirect("/internal_po_list/")

    context["form"] = form
    context["emp"] = emp
    return render(request, "update_po.html", context)

@login_required(login_url='/home/')
def update_deleted_po(request, id, woID, selectedvs):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["woID"] = int(woID)

    context["po"] = DeletedInternalPO.objects.filter(id = id).first()
    context["id"] = id


    vendorList = vendorSubcontrator(request)

    context['vendorList']= vendorList

    obj = get_object_or_404(DeletedInternalPO, id = id )

    if selectedvs != "0":
        itemResult = next((i for i, item in enumerate(vendorList) if item["id"] == selectedvs), None)
    else:
        itemResult = next((i for i, item in enumerate(vendorList) if item["id"] == obj.vendor), None)


    if itemResult != None:
        context['selectedvs2'] = vendorList[itemResult]
    else:
        context['selectedvs2'] = ""    

    
    form = DeletedInternalPOForm(request.POST or None, instance = obj )

    
    status_update = (
    (1, 'Open'),
    (3, 'Invoiced'),
    )

    if obj.Status == 1:
        context["status_update"] = "Permitido de Open a Invoiced"
        form.fields['Status'].choices = status_update


    
    context["order"] = obj.woID_d.prismID + " - " + obj.woID_d.workOrderId + " - " + obj.woID_d.PO
    context["order"] = obj.woID_d.prismID + " - " + obj.woID_d.workOrderId + " - " + obj.woID_d.PO

    
 
    if form.is_valid():
        vendor = request.POST.get('vendor') 
        
        if vendor == "0":
            form.instance.vendor = None
        else:
            form.instance.vendor = vendor


        if form.instance.poNumber == None:
            form.instance.poNumber = form.instance.id

        try:         
            newFile = request.FILES['myfile']
            form.instance.receipt = newFile

        except Exception as e:
            None

        
            
        form.save()

        if int(woID) > 0:
            return HttpResponseRedirect("/po_list/" + str(obj.woID.id))
        elif int(woID) < 0:
            return HttpResponseRedirect("/billing_list/" + str(obj.woID.id) + "/False")
        else:
            return HttpResponseRedirect("/internal_po_list/")

    context["form"] = form
    context["emp"] = emp
    return render(request, "update_deleted_po.html", context)


@login_required(login_url='/home/')
def unlink_po(request, id, woID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["woID"] = int(woID)

    obj = get_object_or_404(internalPO, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':


        if obj.Status == 2:
            estimateID = obj.estimate
            obj.Status = 1
            obj.estimate = None
            obj.invoice = None
            obj.save()

            calculate_estimate_total(request,woID,int(estimateID))

        elif obj.Status == 3:
            invoiceID = obj.invoice

            obj.Status = 1
            obj.estimate = None
            obj.invoice = None
            obj.save()


            calculate_invoice_total(request,woID,int(invoiceID))

        if int(woID) > 0:
            return HttpResponseRedirect("/po_list/" + str(woID))
        else:
            return HttpResponseRedirect("/internal_po_list/") 

   
    return render(request, "unlink_po.html", context)



@login_required(login_url='/home/')
def delete_po(request, id, woID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["woID"] = int(woID)

    obj = get_object_or_404(internalPO, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        
        #Create a copy of the PO in case it needs to be linked again
        
        DeletedInternalPO.objects.create(
            poNumber = obj.poNumber,
            woID_d = obj.woID,
            vendor = obj.vendor,
            supervisor_d = obj.supervisor,
            pickupEmployee_d = obj.pickupEmployee,
            product = obj.product,
            quantity = obj.quantity,
            total = obj.total,
            nonBillable = obj.nonBillable,
            isAmountRounded = obj.isAmountRounded,
            estimate = obj.estimate,
            invoice = obj.invoice,
            Status = obj.Status,
            receipt = obj.receipt,
            transferFromPO_d = obj.transferFromPO,
            transferToPO_d = obj.transferToPO,
            transfer_date = obj.transfer_date,
            transferBy = obj.transferBy,
            created_date = obj.created_date,
            createdBy = obj.createdBy,
            deleted_date = datetime.now(),
            deletedBy = request.user.username
        )
        
        obj.delete()

        if int(woID) > 0:
            return HttpResponseRedirect("/po_list/" + str(woID))
        else:
            return HttpResponseRedirect("/internal_po_list/") 

   
    return render(request, "delete_po.html", context)

@login_required(login_url='/home/')
def create_po(request, id, selectedvs):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    vendorList = vendorSubcontrator(request)
    context['vendorList']= vendorList   
    context['selectedvs']= selectedvs
    context['selectedid']= id

    itemResult = next((i for i, item in enumerate(vendorList) if item["id"] == selectedvs), None)

    if itemResult != None:
        context['selectedvs2'] = vendorList[itemResult]
    else:
        context['selectedvs2'] = ""
    


    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    
    if request.user.is_staff or emp.is_superAdmin:
        form = InternalPOFormAdmin(request.POST or None, initial={'woID': wo})    
    elif emp.accounts_payable:
        form = InternalPOFormAccounPay(request.POST or None, initial={'woID': wo})
    else:
        form = InternalPOForm(request.POST or None, initial={'woID': wo})
    
    
    if form.is_valid():
        form.instance.woID = wo

        vendor = request.POST.get('vendor') 
                
        if vendor == "0":
            form.instance.vendor = None
        else:
            form.instance.vendor = vendor


        poSequence = Sequence("po") 
        poNumber = poSequence.get_next_value()        
        form.instance.poNumber = int(poNumber)

        try:         
            newFile = request.FILES['myfile']
            form.instance.receipt = newFile

        except Exception as e:
            None

        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()

        form.save()               
        return HttpResponseRedirect("/po_list/" + str(id))
         
    context['form']= form
    context["emp"] = emp
    context["selectedWO"] = id
    return render(request, "create_po.html", context)


@require_GET
@login_required(login_url='/home/')
def validate_invoices(request):
    invoices_raw = request.GET.get('invoices','')
    current_id = request.GET.get('current_id','')
    invoices = [i.strip() for i in invoices_raw.split(',') if i.strip()]
    matches = []

    if not invoices:
        return JsonResponse({'matches': []})

    qs = internalPO.objects.all()
    if current_id:
        try:
            qs = qs.exclude(pk=int(current_id))
        except:
            pass

    for inv in invoices:
        for rec in qs:
            if rec.invoices:
                rec_list = [r.strip() for r in rec.invoices.split(',') if r.strip()]
                if inv in rec_list:
                    matches.append({
                        'invoice': inv,
                        'po_id': rec.id,
                        'poNumber': rec.poNumber,
                        'total': rec.total or ''
                    })
    return JsonResponse({'matches': matches})

@login_required(login_url='/home/')
def estimate(request, id, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    context["order"] = wo
    context["emp"] = emp

    context["estimate"] = True
    isPartial = ""

    itemResume = []

    
    authBilling = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)
    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()
    context["woEstimate"] = woEst

    if woEst.is_partial:
        isPartial = "*****  PARTIAL *****"
    else:
        isPartial = "***** FINAL *****"

    for data in authBilling:
        if data.quantity > 0:

            #calculate the Price for each item
            price = Decimal(str(data.total)) / Decimal(str(data.quantity))

            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price': price, 'amount':data.total,'Encontrado':False})
            #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})
    

    itemHtml = ''
    total = 0 
    linea = 0
    try:
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0

            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount
            itemHtml = itemHtml + " <tr>"
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> ' + str(data['item']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">    ' + data['name']  + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data['quantity']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> $' + '{0:,.2f}'.format(float(data['price'])) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(data['amount']) + '</td> '
            itemHtml = itemHtml + ' </tr> '            
    except Exception as e:
        itemHtml = itemHtml + str(e)
        print(e)

    # obtengo las internal PO
    internal = internalPO.objects.filter(woID = wo, nonBillable = False, estimate = estimateID)

    totaPO = 0

    for data in internal:        
        linea = linea + 1
        if data.total != None and data.total != "":
            
            if data.isAmountRounded:    
                amount = int(round(float(str(data.total))))  
            else:
                amount = Decimal(str(data.total))      
            
        else:
            amount = 0
        
        # Sum all the Internal PO's
        totaPO += amount
        

    if totaPO > 0:
        totaPO2 = totaPO + (totaPO * Decimal(str(0.10)))
        
        #if data.isAmountRounded:
        #    total = total + int(round(float(totaPO2)))
        #else:
        total = total + totaPO2
        
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center">NS005 </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Materials and Fees Pass-through </td> '
        
        if data.isAmountRounded:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(int(round(float(totaPO)))) + '</td>'
        else:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(float(totaPO)) + '</td>'
        
        
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center">$1.10 </td> '
        
        #if data.isAmountRounded:
        #    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(totaPO2)))) + '</td>'
        #else:
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(float(totaPO2)) + '</td>'
        
        
        itemHtml = itemHtml + ' </tr> '



    #Adding Billable Hours
    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))

    total += Decimal(totalHoursRate) 

    if totalHours > 0:
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Hours </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHours)) + ' </td>'
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHoursRate)) + ' </td>'
        itemHtml = itemHtml + ' </tr> '


    #Add Partial or final Text
    itemHtml = itemHtml + ' <tr> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> ' + isPartial + ' </td> '
    itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' </tr> '

    for i in range(21-linea):
        itemHtml = itemHtml + '<tr>'
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="20%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="43%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="13%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '</tr> '
        
    context["itemPrice"] = itemHtml

    # If Estimate have an Adjust

    adj = woAdjustment.objects.filter(woID = wo, estimateNumber = estimateID).first()

    if adj:    
        context["total"] = Decimal(total) + Decimal(validate_decimals(adj.adjustment))
    else:
        context["total"] = total 

    #context["total"] = total


    template_path = 'invoice_template.html'
    context["estimateID"] = estimateID
    template= get_template(template_path)

    wo2 = workOrder.objects.filter(id=id).first()
    fileName = "estimate-" + str(estimateID) + ".pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + fileName

    context["order"] = wo2

    html = template.render(context)

    pisa_status = pisa.CreatePDF(
        html, dest=response)


    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response 

@login_required(login_url='/home/')
def partial_estimate(request, id, isPartial, Status, addressID):
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    openEstimate = woEstimate.objects.filter(woID = wo, Status = 1).count()

    if openEstimate == 0 and int(Status) == 1:
        pre = Sequence("preinvoice")
        estimateID = str(pre.get_next_value())

        billAddress = billingAddress.objects.filter(id  = addressID).first()

        #creating the estimate
        estimateObject = woEstimate(
            woID = wo,
            estimateNumber = estimateID,
            Status = 1,
            is_partial = isPartial,
            zipCode = billAddress.zipCode,
            state = billAddress.state,
            city = billAddress.city,
            address = billAddress.address,
            description = billAddress.description,
            created_date = datetime.now(),
            createdBy = request.user.username
        )

        estimateObject.save()

        est = woEstimate.objects.filter(woID = wo, Status = 1).first()

        if est.is_partial == False:
            log = woStatusLog( 
                                woID = wo,
                                currentStatus = wo.Status,
                                nextStatus = 4,
                                createdBy = request.user.username,
                                created_date = datetime.now()
                                )
            log.save()        
        
            wo.Status=4        
            wo.UploadDate = datetime.now()
            wo.save()   

    elif openEstimate > 0 and int(Status) == 1: 
        est = woEstimate.objects.filter(woID = wo, Status = 1).first()
        estimateID = est.estimateNumber

        if est.is_partial == False:
            log = woStatusLog( 
                                woID = wo,
                                currentStatus = wo.Status,
                                nextStatus = 4,
                                createdBy = request.user.username,
                                created_date = datetime.now()
                                )
            log.save()        
        
            wo.Status=4        
            wo.UploadDate = datetime.now()
            wo.save()    

    elif int(Status) == 2:
        est = woEstimate.objects.filter(woID = wo, Status = 1).first()
        
        if est:
            estimateID = est.estimateNumber        

            #Validate if Estimate does have an Invoice
            InvCount = woInvoice.objects.filter(estimateNumber = estimateID).count()

            if InvCount == 0:
                pre = Sequence("invoice")
                invoiceID = str(pre.get_next_value())

                if est.is_partial == False:
                    log = woStatusLog( 
                                        woID = wo,
                                        currentStatus = 4,
                                        nextStatus = 5,
                                        createdBy = request.user.username,
                                        created_date = datetime.now()
                                        )
                    log.save()        
                
                    wo.Status=5        
                    wo.UploadDate = datetime.now()
                    wo.save()    

                    
                #creating the Invoice
                invoiceObject = woInvoice(
                    woID = wo,
                    estimateNumber = estimateID,
                    invoiceNumber = invoiceID,
                    Status = 1,
                    zipCode = est.zipCode,
                    state = est.state,
                    city = est.city,
                    address = est.address,
                    description = est.description,
                    is_partial = est.is_partial,
                    created_date = datetime.now(),
                    createdBy = request.user.username
                )
                invoiceObject.save()
            else:               
                estimateID = 0
                invoiceID = 0
        else:
            estimateID = 0
            invoiceID = 0

    

    
    if int(Status) == 1:
        #Update dailyItems
        dailyI = DailyItem.objects.filter(DailyID__woID = wo, Status = 1)

        for i in dailyI:
            dItem = DailyItem.objects.filter(id = i.id).first()

            dItem.Status = 2
            dItem.estimate = estimateID
            dItem.save()
        

        #Update daily Employees
        dailyE = DailyEmployee.objects.filter(DailyID__woID = wo, Status = 1, billableHours = True)

        for e in dailyE:
            
            if e.total_hours > 0:
                dEmp = DailyEmployee.objects.filter(id = e.id).first()
                
                dEmp.Status = 2
                dEmp.estimate = estimateID
                dEmp.save()
        

        #Update externalProdItem
        epItem = externalProdItem.objects.filter(externalProdID__woID = wo, Status = 1)

        for j in epItem:
            eItem = externalProdItem.objects.filter(id = j.id).first()

            eItem.Status = 2
            eItem.estimate = estimateID
            eItem.save()

        #Update authorizedItem
        authItem = authorizedBilling.objects.filter(woID = wo, Status = 1)

        for k in authItem:
            aItem = authorizedBilling.objects.filter(id = k.id).first()

            aItem.Status = 2
            aItem.estimate = estimateID
            aItem.save()
        
        #Update Internal PO
        internal = internalPO.objects.filter(woID = wo, Status = 1)

        for l in internal:
            iItem = internalPO.objects.filter(id = l.id).first()

            if validate_decimals(iItem.total) > 0:
                iItem.Status = 2
                iItem.estimate = estimateID
                iItem.save()

    elif int(Status) == 2:

        if int(invoiceID) > 0:

            #Update dailyItems
            dailyI = DailyItem.objects.filter(DailyID__woID = wo, estimate = estimateID)

            for i in dailyI:
                dItem = DailyItem.objects.filter(id = i.id).first()

                dItem.Status = 3
                dItem.invoice = invoiceID
                dItem.save()
            

            #Update daily Employees
            dailyE = DailyEmployee.objects.filter(DailyID__woID = wo, estimate = estimateID).exclude(Status=4)

            for e in dailyE:
                
                if e.total_hours > 0:
                    dEmp = DailyEmployee.objects.filter(id = e.id).first()
                    
                    dEmp.Status = 3
                    dEmp.invoice = invoiceID
                    dEmp.save()

            #Update externalProdItem
            epItem = externalProdItem.objects.filter(externalProdID__woID = wo, estimate = estimateID)

            for j in epItem:
                eItem = externalProdItem.objects.filter(id = j.id).first()

                eItem.Status = 3
                eItem.invoice = invoiceID
                eItem.save()

            #Update authorizedItem
            authItem = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)

            for k in authItem:
                aItem = authorizedBilling.objects.filter(id = k.id).first()

                aItem.Status = 3
                aItem.invoice = invoiceID
                aItem.save()
            
            #Update Internal PO
            internal = internalPO.objects.filter(woID = wo, estimate = estimateID)

            for l in internal:
                iItem = internalPO.objects.filter(id = l.id).first()

                iItem.Status = 3
                iItem.invoice = invoiceID
                iItem.save()
            

            #adjustments

            adj = woAdjustment.objects.filter(woID = wo, estimateNumber = estimateID).first() 
            if adj:   
                adj.invoiceNumber = invoiceID
                adj.save()

            est = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()       
            est.Status = 2
            est.save()


            calculate_invoice_total(request,wo.id,int(invoiceID))
        
    return HttpResponseRedirect("/billing_list/" + str(id)+ "/False") 



@login_required(login_url='/home/')
def invoice(request, id, invoiceID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    context["order"] = wo
    context["emp"] = emp

    context["estimate"] = False
    isPartial = ""
    itemResume = []

    authBilling = authorizedBilling.objects.filter(woID = wo, invoice = invoiceID)

    woInv = woInvoice.objects.filter(woID = wo, invoiceNumber = invoiceID).first()
    context["woEstimate"] = woInv

    if woInv.is_partial:
        isPartial = "*****  PARTIAL *****"
    else:
        isPartial = "***** FINAL *****"

    for data in authBilling:
        if data.quantity > 0:

            #calculate the Price for each item
            price = Decimal(str(data.total)) / Decimal(str(data.quantity))

            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':price, 'amount':data.total,'Encontrado':False})
            #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})

    itemHtml = ''
    total = 0 
    linea = 0
    try:
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0
            
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount
            itemHtml = itemHtml + " <tr>"
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> ' + str(data['item']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">   ' + data['name'] + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data['quantity']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> $' + '{0:,.2f}'.format(float(data['price'])) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(data['amount']) + '</td> '
            itemHtml = itemHtml + ' </tr> '            
    except Exception as e:
        print(e)


    # obtengo las internal PO
    internal = internalPO.objects.filter(woID = wo, nonBillable = False, invoice = invoiceID)
    totaPO = 0
    
    vendorList = vendorSubcontrator(request)
    
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            if data.isAmountRounded:
                amount = int(round(float(str(data.total)))) 
            else:
                amount = Decimal(str(data.total))
        else:
            amount = 0

        total = total + amount
        totaPO += amount
        
        vendorSel = next((i for i, item in enumerate(vendorList) if item["id"] == data.vendor), None)
                
        if data.total != None and data.total != "":
            itemHtml = itemHtml + ' <tr> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
            
            if vendorSel != None:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">' + str(vendorList[vendorSel]["name"]) + '</td> '
            else:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> NA </td> '

            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data.quantity) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
            
            if data.isAmountRounded:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(str(data.total))))) + '</td>'
            else:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(data.total)) + '</td>'
            
            itemHtml = itemHtml + ' </tr> '

    if totaPO > 0:
        totaPO = totaPO * Decimal(str(0.10))
        
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO)))
        #else:
        total = total + totaPO
            
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Markup </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"></td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        
        #if data.isAmountRounded:
            #itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(totaPO)))) + '</td>'
        #else:
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(totaPO)) + '</td>'
        
        itemHtml = itemHtml + ' </tr> '

    
    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice = invoiceID).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))

    total += Decimal(totalHoursRate) 

    if totalHours > 0:
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Hours </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHours)) + ' </td>'
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHoursRate)) + ' </td>'
        itemHtml = itemHtml + ' </tr> '


    #Add Partial or final Text
    itemHtml = itemHtml + ' <tr> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> ' + isPartial + ' </td> '
    itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' </tr> '

    for i in range(20-linea):
        itemHtml = itemHtml + '<tr>'
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="20%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="43%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="13%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '</tr> '
        
    context["itemPrice"] = itemHtml
    #context["total"] = total

     # If Estimate have an Adjust

    adj = woAdjustment.objects.filter(woID = wo, invoiceNumber = invoiceID).first()

    if adj:    
        context["total"] = Decimal(total) + Decimal(validate_decimals(adj.adjustment))
    else:
        context["total"] = total 
    

    template_path = 'invoice_template.html'
    
    if woInv.Status == 3:
        context["invoiceID"] = str(invoiceID) + "R"
    else:
        context["invoiceID"] = str(invoiceID)
        
    template= get_template(template_path)

    """if (wo.invoice != 0 and wo.invoice != " " and wo.invoice is None):  

        log = woStatusLog( 
                            woID = wo,
                            currentStatus = wo.Status,
                            nextStatus = 5,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
        log.save()

        pre = Sequence("invoice")
        wo.invoice = str(pre.get_next_value())
        wo.Status=5
        wo.UploadDate = datetime.now()
        wo.save()
    """
    wo2 = workOrder.objects.filter(id=id).first()

    fileName = "invoice-" + str(invoiceID) + ".pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + fileName

    context["order"] = wo2

    html = template.render(context)

    pisa_status = pisa.CreatePDF(
        html, dest=response)


    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response   


@login_required(login_url='/home/')
def download_estimate_preview(request, id, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    context["order"] = wo
    context["emp"] = emp

    context["estimate"] = True
    isPartial = ""

    itemResume = []

    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()
    context["woEstimate"] = woEst

    if int(str(estimateID)) == 0:
        authBilling = authorizedBilling.objects.filter(woID = wo, Status = 1)
        isPartial = ""
    else:
        authBilling = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)
        
        if woEst.is_partial:
            isPartial = "*****  PARTIAL *****"
        else:
            isPartial = "***** FINAL *****"

    for data in authBilling:
        if data.quantity > 0:

            #calculate the Price for each item
            price = Decimal(str(data.total)) / Decimal(str(data.quantity))

            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price': price, 'amount':data.total,'Encontrado':False})
            #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})


    itemHtml = ''
    total = 0 
    linea = 0
    try:        
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0
           
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount
           
            itemHtml = itemHtml + " <tr>"
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> ' + str(data['item']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">    ' + data['name']  + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data['quantity']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> $' + '{0:,.2f}'.format(float(data['price'])) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(data['amount']) + '</td> '
            itemHtml = itemHtml + ' </tr> '          
    except Exception as e:
        itemHtml = itemHtml + str(e)
        print(str(e))

    # obtengo las internal PO
    if int(str(estimateID)) == 0:
        internal = internalPO.objects.filter(woID = wo, nonBillable = False, Status = 1)
    else:
        internal = internalPO.objects.filter(woID = wo, nonBillable = False, estimate = estimateID)

    totaPO = 0
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            
            if data.isAmountRounded:
                amount = int(round(float(str(data.total))))  
            else:
                amount = Decimal(str(data.total)) 
        else:
            amount = 0

        # Sum all the Internal PO's
        totaPO += amount
        

    if totaPO > 0:
        totaPO2 = totaPO + (totaPO * Decimal(str(0.10)))
        
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO2)))
        #else:
        total = total + totaPO2
        
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center">NS005 </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Materials and Fees Pass-through </td> '
        
        if data.isAmountRounded:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(int(round(float(totaPO)))) + '</td>'
        else:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(float(totaPO)) + '</td>'
        
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center">$1.10 </td> '
        
        #if data.isAmountRounded:
        #    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(totaPO2)))) + '</td>'
        #else:
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(totaPO2)) + '</td>'
        
        itemHtml = itemHtml + ' </tr> '
    
    #Adding Billable Hours

    if int(str(estimateID)) == 0:
        bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, Status = 1)        
    else:
        bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))
    
    total += Decimal(totalHoursRate) 

    if totalHours > 0:
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Hours </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHours)) + ' </td>'
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHoursRate)) + ' </td>'
        itemHtml = itemHtml + ' </tr> '



    #Add Partial or final Text
    itemHtml = itemHtml + ' <tr> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> ' + isPartial + ' </td> '
    itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' </tr> '
   
    for i in range(21-linea):     
        itemHtml = itemHtml + '<tr>'
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="20%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="43%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="13%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '</tr> '

    context["estimateID"] = estimateID    
    context["itemPrice"] = itemHtml
    context["total"] = total

    template_path = 'invoice_template_preview.html'
    context["estimateID"] = estimateID
    template= get_template(template_path)

    wo2 = workOrder.objects.filter(id=id).first()
    fileName = "estimate-" + str(estimateID) + ".pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + fileName

    context["order"] = wo2

    html = template.render(context)

    pisa_status = pisa.CreatePDF(
        html, dest=response)


    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response 



    #return render(request, "invoice_template_preview.html", context)

@login_required(login_url='/home/')
def estimate_preview(request, id, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    context["order"] = wo
    context["emp"] = emp

    context["estimate"] = True
    isPartial = ""

    itemResume = []

    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()
    context["woEstimate"] = woEst

    if int(str(estimateID)) == 0:
        authBilling = authorizedBilling.objects.filter(woID = wo, Status = 1)
        isPartial = ""
    else:
        authBilling = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)
        
        if woEst.is_partial:
            isPartial = "*****  PARTIAL *****"
        else:
            isPartial = "***** FINAL *****"

    for data in authBilling:
        if data.quantity > 0:

            #calculate the Price for each item
            price = Decimal(str(data.total)) / Decimal(str(data.quantity))

            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':price, 'amount':data.total,'Encontrado':False})
            #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})


    itemHtml = ''
    total = 0 
    linea = 0
    try:        
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0
           
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount
           
            itemHtml = itemHtml + " <tr>"
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> ' + str(data['item']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">    ' + data['name']  + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data['quantity']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> $' + '{0:,.2f}'.format(float(data['price'])) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(data['amount']) + '</td> '
            itemHtml = itemHtml + ' </tr> '          
    except Exception as e:
        itemHtml = itemHtml + str(e)
        print(str(e))

    # obtengo las internal PO
    if int(str(estimateID)) == 0:
        internal = internalPO.objects.filter(woID = wo, nonBillable = False, Status = 1)
    else:
        internal = internalPO.objects.filter(woID = wo, nonBillable = False, estimate = estimateID)

    totaPO = 0
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            
            if data.isAmountRounded:
                amount = int(round(float(str(data.total))))  
            else:
                amount = Decimal(str(data.total)) 
        else:
            amount = 0

        # Sum all the Internal PO's
        totaPO += amount
        

    if totaPO > 0:
        totaPO2 = totaPO + (totaPO * Decimal(str(0.10)))
        
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO2)))
        #else:
        total = total + totaPO2
        
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center">NS005 </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Materials and Fees Pass-through </td> '
        
        if data.isAmountRounded:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(int(round(float(totaPO)))) + '</td>'
        else:
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">'  + '{0:,.2f}'.format(float(totaPO)) + '</td>'
        
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center">$1.10 </td> '
        
        #if data.isAmountRounded:
        #    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(totaPO2)))) + '</td>'
        #else:
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(totaPO2)) + '</td>'
        
        itemHtml = itemHtml + ' </tr> '
    
    #Adding Billable Hours

    if int(str(estimateID)) == 0:
        bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, Status = 1)        
    else:
        bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))
    
    total += Decimal(totalHoursRate) 

    if totalHours > 0:
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Hours </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHours)) + ' </td>'
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHoursRate)) + ' </td>'
        itemHtml = itemHtml + ' </tr> '



    #Add Partial or final Text
    itemHtml = itemHtml + ' <tr> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> ' + isPartial + ' </td> '
    itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' </tr> '
   
    for i in range(21-linea):     
        itemHtml = itemHtml + '<tr>'
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="20%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="43%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="13%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '</tr> '

    context["estimateID"] = estimateID    
    context["itemPrice"] = itemHtml
    
    # If Estimate have an Adjust

    adj = woAdjustment.objects.filter(woID = wo, estimateNumber = estimateID).first()

    if adj:    
        context["total"] = Decimal(total) + Decimal(validate_decimals(adj.adjustment))
    else:
        context["total"] = total 

    return render(request, "invoice_template_preview.html", context)


@login_required(login_url='/home/')
def invoice_preview(request, id, invoiceID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()

    context["order"] = wo
    context["emp"] = emp

    context["estimate"] = False
    isPartial = ""
    itemResume = []


    authBilling = authorizedBilling.objects.filter(woID = wo, invoice = invoiceID)

    woInv = woInvoice.objects.filter(woID = wo, invoiceNumber = invoiceID).first()
    context["woEstimate"] = woInv

    if woInv.is_partial:
        isPartial = "*****  PARTIAL *****"
    else:
        isPartial = "***** FINAL *****"

    for data in authBilling:
        if data.quantity > 0:
            #calculate the Price for each item
            price = Decimal(str(data.total)) / Decimal(str(data.quantity))

            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':price, 'amount':data.total,'Encontrado':False})
            #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})


    itemHtml = ''
    total = 0 
    linea = 0
    
    try:
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0            
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount
            itemHtml = itemHtml + " <tr>"
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> ' + str(data['item']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">    ' + data['name']  + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data['quantity']) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> $' + '{0:,.2f}'.format(float(data['price'])) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $' + '{0:,.2f}'.format(data['amount']) + '</td> '
            itemHtml = itemHtml + ' </tr> '                 
    except Exception as e:
        print(e)

    # obtengo las internal PO
    internal = internalPO.objects.filter(woID = wo, nonBillable = False, invoice = invoiceID)
    totaPO = 0
    
    vendorList = vendorSubcontrator(request)
    
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            if data.isAmountRounded:
                amount = int(round(float(str(data.total)))) 
            else:
                amount = Decimal(str(data.total))
        else:
            amount = 0

        total = total + amount
        totaPO += amount
        
        vendorSel = next((i for i, item in enumerate(vendorList) if item["id"] == data.vendor), None)
        #Aqui estoy modificando ahora
        
        if data.total != None and data.total != "":
            itemHtml = itemHtml + ' <tr> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center">  </td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left">' + str(vendorList[vendorSel]["name"]) + '</td> '
            itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center">' + str(data.quantity) + '</td> '
            itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center">  </td> '
            
            if data.isAmountRounded:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(str(data.total))))) + '</td>'
            else:
                itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(data.total)) + '</td>'
            
            itemHtml = itemHtml + ' </tr> '

    if totaPO > 0:
        totaPO = totaPO * Decimal(str(0.10))
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO)))
        #else:
        total = total + totaPO
            
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Markup </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"></td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        
        #if data.isAmountRounded:
            #itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(int(round(float(totaPO)))) + '</td>'
        #else:
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> $'  + '{0:,.2f}'.format(float(totaPO)) + '</td>'
        
        itemHtml = itemHtml + ' </tr> '


    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice = invoiceID).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))


    total += Decimal(totalHoursRate) 

    if totalHours > 0:
        itemHtml = itemHtml + ' <tr> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> Hours </td> '
        itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHours)) + ' </td>'
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
        itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> ' + '{0:,.2f}'.format(float(totalHoursRate)) + ' </td>'
        itemHtml = itemHtml + ' </tr> '


    #Add Partial or final Text
    itemHtml = itemHtml + ' <tr> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="20%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px; padding-left: 2px;" width="43%" align="left"> ' + isPartial + ' </td> '
    itemHtml = itemHtml +  ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="13%" align="center"> </td> '
    itemHtml = itemHtml + ' <td style="border-left:1px solid #444; border-right:1px solid #444; padding-top: 3px;" width="12%" align="center"> </td>'
    itemHtml = itemHtml + ' </tr> '

    for i in range(21-linea):
        itemHtml = itemHtml + '<tr>'
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="20%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="43%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="13%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '<td style="border-left:1px solid #444; border-right:1px solid #444;" width="12%" align="center">&nbsp;</td> '
        itemHtml = itemHtml + '</tr> '
        
    context["itemPrice"] = itemHtml
    #context["total"] = total

    # If Estimate have an Adjust

    adj = woAdjustment.objects.filter(woID = wo, invoiceNumber = invoiceID).first()

    if adj:    
        context["total"] = Decimal(total) + Decimal(validate_decimals(adj.adjustment))
    else:
        context["total"] = total 
    
    
    if woInv.Status == 3:
        context["invoiceID"] = str(invoiceID) + "R"
    else:
        context["invoiceID"] = str(invoiceID)

    #return render(request, "pre_invoice.html", context)
    return render(request, "invoice_template_preview.html", context)

@login_required(login_url='/home/')
def pre_invoice2(request, id):

    context = {}    
    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    return render(request, "pre_invoice2.html", context)

@login_required(login_url='/home/')
def calculate_invoice_total(request, id, invoiceID):

    wo = workOrder.objects.filter(id=id).first()

    itemResume = []

    authBilling = authorizedBilling.objects.filter(woID = wo, invoice = invoiceID)

    woInv = woInvoice.objects.filter(woID = wo, invoiceNumber = invoiceID).first()

    for data in authBilling:
        if data.quantity > 0:
            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})
    
    total = 0 
    linea = 0

    try:
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0
            
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount         
    except Exception as e:
        print(e)


    # obtengo las internal PO
    internal = internalPO.objects.filter(woID = wo, nonBillable = False, invoice = invoiceID)
    totaPO = 0
    
    vendorList = vendorSubcontrator(request)
    
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            if data.isAmountRounded:
                amount = int(round(float(str(data.total)))) 
            else:
                amount = Decimal(str(data.total))
        else:
            amount = 0

        total = total + amount
        totaPO += amount
        
                
    if totaPO > 0:
        totaPO = totaPO * Decimal(str(0.10))
        
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO)))
        #else:
        total = total + totaPO


    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice = invoiceID).exclude(Status=4)

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))
       
    total += Decimal(totalHoursRate) 

    woInv.total = total
    woInv.save()
    
    return total   

@login_required(login_url='/home/')
def calculate_estimate_total(request, id, estimateID):

    wo = workOrder.objects.filter(id=id).first()

    itemResume = []

    authBilling = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)

    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()

    for data in authBilling:
        if data.quantity > 0:
            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':data.total,'Encontrado':False})
    
    total = 0 
    linea = 0

    try:
        itemResumeS = sorted(itemResume, key=lambda d: d['item']) 
        for data in itemResumeS:
            linea = linea + 1
            amount = 0
            
            amount = Decimal(str(data['quantity'])) * Decimal(str(data['price']))
            total = total + amount         
    except Exception as e:
        print(e)


    # obtengo las internal PO
    internal = internalPO.objects.filter(woID = wo, nonBillable = False, estimate = estimateID)
    totaPO = 0
    
    vendorList = vendorSubcontrator(request)
    
    for data in internal:
        linea = linea + 1
        if data.total != None and data.total != "":
            if data.isAmountRounded:
                amount = int(round(float(str(data.total)))) 
            else:
                amount = Decimal(str(data.total))
        else:
            amount = 0

        total = total + amount
        totaPO += amount
        
                
    if totaPO > 0:
        totaPO = totaPO * Decimal(str(0.10))
        
        #if data.isAmountRounded:
            #total = total + int(round(float(totaPO)))
        #else:
        total = total + totaPO


    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID).exclude(Status=4)

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))
       
    total += Decimal(totalHoursRate) 

    woEst.total = total
    woEst.save()
    
    return total   


@login_required(login_url='/home/')
def upload_item(request):
    countInserted = 0
    countRejected = 0
    countUpdated = 0
    if request.method == 'POST':
        dataset = Dataset()
        new_item = request.FILES['myfile']

        if not new_item.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request,'upload_item.html', {'countInserted':countInserted, 'countRejected':countRejected  })

        imported_data = dataset.load(new_item.read(),format='xlsx')
      

        for data in imported_data:             
            try:         
                value = item(
                    itemID = data[0],
                    name = data[1],
                    description =  data[2],
                    is_active = True ,
                    created_date = datetime.now()                   
                )
                value.save()

                countInserted = countInserted + 1
            except Exception as e:
                countRejected = countRejected + 1                
                       
    return render(request,'upload_item.html', {'countInserted':countInserted, 'countRejected':countRejected })

@login_required(login_url='/home/')
def upload_item_price(request):
    countInserted = 0
    countRejected = 0
    countUpdated = 0
    if request.method == 'POST':
        dataset = Dataset()
        new_item = request.FILES['myfile']

        if not new_item.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request,'upload_itemDetail.html', {'countInserted':"-1", 'countRejected':"-1"  })

        imported_data = dataset.load(new_item.read(),format='xlsx')
      

        for data in imported_data:             
            try:         
                itemp = item.objects.filter(itemID = data[0]).first()
                loca = Locations.objects.filter(name = data[1]).first()

                if itemp and loca:

                    """value = itemPrice(
                        item = itemp,
                        location = loca,
                        pay_perc =  data[2],
                        price = data[3],
                        emp_payout = data[4],
                        rate  = data[5]                
                    )
                    value.save()"""

                    value = itemPrice.objects.filter(item = itemp, location = loca).first()
                    if value:
                        value.pay_perc =  data[2]
                        value.price = data[3]       
                        value.emp_payout = data[4]
                        value.rate = data[5]
                        value.save()

                    countInserted = countInserted + 1
            except Exception as e:
                print(e)
                countRejected = countRejected + 1                
                       
    return render(request,'upload_itemDetail.html', {'countInserted':countInserted, 'countRejected':countRejected })

@login_required(login_url='/home/')
def upload_employee(request):
    countInserted = 0
    countRejected = 0
    countUpdated = 0
    error_detail = []
    if request.method == 'POST':
        dataset = Dataset()
        new_item = request.FILES['myfile']

        if not new_item.name.endswith('xlsx'):
            messages.info(request, 'wrong format')
            return render(request,'upload_employee.html', {'countInserted':countInserted, 'countRejected':countRejected  })

        imported_data = dataset.load(new_item.read(),format='xlsx')
      
        sup = None
        loc= None
        
        for data in imported_data:             
            try:         

                if data[6] != None and data[6]!= '':
                    sup = Employee.objects.filter(employeeID = int(data[6])).first()
                
                if data[7] != None and data[7]!= '':
                    loc = Locations.objects.filter(LocationID = int(data[7])).first()

                if sup!= None and loc != None:
                    value = Employee(
                        employeeID = data[0],
                        first_name = data[1],
                        last_name = data[2],
                        hourly_rate = data[3],
                        email = data[4],
                        is_active = True,
                        supervisor_name = sup,
                        Location = loc
                    )
                    value.save()
                elif sup!=None:
                    value = Employee(
                        employeeID = data[0],
                        first_name = data[1],
                        last_name = data[2],
                        hourly_rate = data[3],
                        email = data[4],
                        is_active = True,
                        supervisor_name = sup                        
                    )
                    value.save()
                elif loc!=None:
                    value = Employee(
                        employeeID = data[0],
                        first_name = data[1],
                        last_name = data[2],
                        hourly_rate = data[3],
                        email = data[4],
                        is_active = True,
                        Location = loc                        
                    )
                    value.save()
                else :
                    value = Employee(
                        employeeID = data[0],
                        first_name = data[1],
                        last_name = data[2],
                        hourly_rate = data[3],
                        email = data[4],
                        is_active = True                     
                    )
                    value.save()

                countInserted = countInserted + 1
            except Exception as e:
                error_detail.append(str(e))
                countRejected = countRejected + 1                
                       
    return render(request,'upload_employee.html', {'countInserted':countInserted, 'countRejected':countRejected, 'error_detail': error_detail})

@login_required(login_url='/home/')
def period_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    context["period"] = period.objects.filter(periodID__gte = 1).order_by('-id')
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    

    opType = "Access Option"
    opDetail = "Period List"
    logInAuditLog(request, opType, opDetail)


    return render(request, "period_list.html", context)

@login_required(login_url='/home/')
def location_period_list(request, id):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(id = id).first()

    perActive = period.objects.filter(status__in=(1,2)).first()
    context["per"] = perActive

    
    
    
    if request.user.is_staff:
        loca = Locations.objects.filter(is_active=True).order_by("LocationID")
    else:
        if emp:
            if emp.is_superAdmin:
                loca = Locations.objects.filter(is_active=True).order_by("LocationID")
            elif emp.Location != None:
                
                locaList = employeeLocation.objects.filter(employeeID = emp)                
                locationList = []
                locationList.append(emp.Location.LocationID)
                
                for i in locaList:
                    locationList.append(i.LocationID.LocationID)
                
                loca = Locations.objects.filter(LocationID__in =locationList, is_active=True).order_by("LocationID")
            else:
                loca = Locations.objects.filter(LocationID = -1)

    

    rtTotal = 0
    otTotal = 0
    dtTotal = 0
    bonusTotal = 0
    on_callTotal = 0
    prodTotal = 0
    gran_total = 0
    payrollTotal = 0
    ownvehicleTotal = 0
    invoiceTotal = 0
    percTotal = 0
    locationSummary = []

    for locItem in loca:
        daily = Daily.objects.filter(Location = locItem, Period = per)     
        regular_time = 0
        over_time = 0
        double_time = 0
        total_time = 0
        rt = 0
        ot = 0
        dt = 0
        bonus = 0
        on_call = 0
        prod = 0
        gran_total = 0
        payroll = 0
        ownvehicle = 0
        invoice = 0
        payroll2= 0
        perc = 0
        for dailyItem in daily:            
            production = DailyItem.objects.filter(DailyID=dailyItem).count()

            dailyemp = DailyEmployee.objects.filter(DailyID=dailyItem)

            for i in dailyemp:
                if production <= 0:
                    regular_time += validate_decimals(i.regular_hours)
                    over_time += validate_decimals(i.ot_hour)
                    double_time += validate_decimals(i.double_time)
                    total_time += validate_decimals(i.total_hours)
                    #if validate_decimals(i.EmployeeID.hourly_rate) != None:
                    rt += validate_decimals(i.rt_pay)
                    ot += validate_decimals(i.ot_pay)
                    dt += validate_decimals(i.dt_pay)

                if validate_decimals(i.bonus) != None:
                    bonus += validate_decimals(i.bonus)
                    
                if validate_decimals(i.on_call) != None:
                    on_call += validate_decimals(i.on_call)

                if validate_decimals(i.payout) != None:
                    payroll += validate_decimals(i.payout)

            
            dailyprod =  DailyItem.objects.filter(DailyID=dailyItem)
            total = 0
            
            ov = 0
            for j in dailyprod:                
                total += validate_decimals(j.total)
                if validate_decimals(j.price) != None:
                    invoice += (validate_decimals(j.quantity) * float(validate_decimals(j.price)) )
                if validate_decimals(j.emp_payout) != None:    
                    payroll2 += (validate_decimals(j.quantity) * float(validate_decimals(j.emp_payout)) )

            dailyempleado = DailyEmployee.objects.filter(DailyID=dailyItem)
            ptpEmp = 0
            for h in dailyempleado:
                ptpEmp += validate_decimals(h.per_to_pay)

                 #Nuevo Calculo Own Vehicle
                if h.is_own_vehicle:
                    ov = validate_decimals(h.own_vehicle_pay)    
                    ownvehicle += validate_decimals(ov)

            total = validate_decimals((total * ptpEmp) / 100)

            #if validate_decimals(dailyItem.own_vehicle) != None:
            #    ov = validate_decimals(((validate_decimals(total) * validate_decimals(dailyItem.own_vehicle)) / 100))
            #   ownvehicle += validate_decimals(ov)


           


            prod += validate_decimals(total)

        if validate_decimals(invoice) > 0:                    
                perc = validate_decimals((validate_decimals(payroll) * 100) / validate_decimals(invoice))

        rtTotal += rt
        otTotal += ot 
        dtTotal += dt
        bonusTotal += bonus
        on_callTotal += on_call
        prodTotal += prod        
        payrollTotal += payroll
        ownvehicleTotal += ownvehicle
        invoiceTotal += invoice
        


        locationSummary.append({ 'LocationID': locItem.LocationID, 'name': locItem.name, 
                                'regular_time':regular_time, 'over_time':over_time, 
                                'double_time':double_time, 'total_time':total_time,
                                'rt': rt, 'ot': ot, 'dt': dt, 'bonus':bonus, 'on_call': on_call,
                                'production': prod, 'own_vehicle': ownvehicle, 'payroll': payroll, 'invoice':invoice, 'percentage': perc})

    if validate_decimals(invoiceTotal) > 0:                    
        percTotal = validate_decimals((validate_decimals(payrollTotal) * 100) / validate_decimals(invoiceTotal))

    totals = {'rt': rtTotal, 'ot': otTotal, 'dt': dtTotal, 'bonus':bonusTotal, 'on_call': on_callTotal,
                                'production': prodTotal, 'own_vehicle': ownvehicleTotal, 'payroll': payrollTotal, 'invoice':invoiceTotal, 'percentage': percTotal}
    
    context["locationSummary"] = locationSummary
    context["totals"] = totals
    context["period"] = per   
    context["emp"] = emp

    try:
        empList = Employee.objects.all()
        empRecap = []
        for item in empList:
            dailyEmp = DailyEmployee.objects.filter(EmployeeID = item, DailyID__Period = id).count()

            if dailyEmp > 0:
                empR = employeeRecap.objects.filter(EmployeeID = item, Period = per).first()
                if empR:
                    file = empR.recap
                else:
                    file = None

                empRecap.append({'employeeID': item.employeeID, 'name': item, 'file': file, 'mailingDate': empR.mailingDate })

        
        
        context["empRecap"] = empRecap
        
        return render(request, "location_period_list.html", context)
    except Exception as e:
        None
    
    return render(request, "location_period_list.html", context)
    
@login_required(login_url='/home/')
def create_period(request, perID):
    periodRange = 13 #Period Rage 14 days
    payRange = 7 #Pay Range, number of days to pay  

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}   
    context["emp"] = emp

    #get the last period created
    lastPeriod = period.objects.filter(id=perID).first()

    if lastPeriod:
        #try:

        fromD = lastPeriod.toDate + timedelta(days=1)
        toD = fromD + timedelta(days=periodRange)
        payD = toD + timedelta(days=payRange)
        newYear = int(payD.year)
        perId = 0
        weekR = 'W' + str(fromD.isocalendar()[1]) + '-' + str(toD.isocalendar()[1])

        if newYear > lastPeriod.periodYear:
            perId = 1
        else:
            perId = lastPeriod.periodID + 1

        newPeriod = period(
            periodID = perId,
            periodYear = newYear,
            fromDate = fromD,
            toDate = toD,
            payDate = payD,
            weekRange = weekR,
            status = 1
        )

        newPeriod.save()

        #Search for Mobile Dailys without period and assign to the new period
        pM = period.objects.filter(periodID = -1).first()
        mobiles = MobileModel.DailyMob.objects.filter(Period = pM)

        for m in mobiles:
            if m.day >= newPeriod.fromDate and m.day <= newPeriod.toDate:
                m.Period = newPeriod
                m.save()

        #except Exception as e:
        #    print('********** Error: ', e, '**********')

    return True

@login_required(login_url='/home/')
def orders_payroll(request, dailyID, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    daily = Daily.objects.filter(id = dailyID).first()    
    loca = list(Locations.objects.all().exclude(LocationID = daily.Location.LocationID))
    
    WOdailyList = list(Daily.objects.filter(Period = daily.Period, day = daily.day, Location__LocationID = LocID).exclude(woID = None).values_list('woID__id',flat=True))


    wo = workOrder.objects.filter(Status__in = [1,2,7,8]).exclude(Location__in = loca).exclude(id__in = WOdailyList )
    context = {}    
    context["orders"] = wo
    context["emp"] = emp    
    context["daily"] = dailyID
    context["selectedLocation"] = LocID

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    #context["WOdailyList"] = WOdailyList

    return render(request, "orders_payroll.html", context)

@login_required(login_url='/home/')
def update_order_daily(request, woID, dailyID, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()

    context = {}    
    context["emp"] = emp    

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    crew = Daily.objects.filter(id = dailyID).first()
    wo = workOrder.objects.filter(id = woID).first()
    
    anterior = None

    if crew and wo:

        if crew.woID != None:
            anterior = workOrder.objects.filter(id = crew.woID.id).first()

            if anterior:

                log = woStatusLog( 
                            woID = anterior,
                            currentStatus = anterior.Status,
                            nextStatus = 1,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
                log.save()

                anterior.Status = 1
                anterior.Location = None
                anterior.UploadDate = None
                anterior.UserName = None
                anterior.WCSup = None
                anterior.UploadDate = datetime.now()
                anterior.save()


        crew.woID = wo
        crew.save()

        if wo.Status != "2":
            log = woStatusLog( 
                                woID = wo,
                                currentStatus = wo.Status,
                                nextStatus = 2,
                                createdBy = request.user.username,
                                created_date = datetime.now()
                                )
            log.save()

        wo.Status = 2
        wo.Location = crew.Location
        wo.UploadDate = datetime.now()
        wo.UserName = request.user.username
        if crew.supervisor != None:
            sup = Employee.objects.filter(employeeID = crew.supervisor ).first()
            if sup:                
                wo.WCSup = sup

        wo.save()

        per = crew.Period.id
        
        #Adding Audit
        if crew.woID != None:            
            operationDetail = "Change on Selected WO - last WO: " + str(anterior) + ", New WO: " + str(wo)
        else:
            operationDetail = "Adding a Selected WO: " + str(wo)


        daily_audit(crew.id, operationDetail, "Insert/Update", request.user.username)

        return HttpResponseRedirect('/payroll/' + str(per) + '/' + crew.day.strftime("%d")  + '/'+ str(crew.crew) +'/' + str(LocID))
    else:
        return HttpResponseRedirect('/payroll/0/0/0/'+str(LocID))

@login_required(login_url='/home/')
def create_daily(request, pID, dID, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    
    context = {}    
    context["emp"] = emp    
    per = period.objects.filter(id = pID).first()

    perActual = period.objects.filter(status__in=(1,2)).first()
    context["per"] = perActual

    if int(LocID) > 0:
        loc = Locations.objects.filter(LocationID = LocID).first()
    else:
        loc = Locations.objects.filter(LocationID = emp.Location.LocationID).first()

    if per:
        #Selecting the day date
        startDate = per.fromDate
        selectedDate = per.fromDate
        numDays = 14
        for x in range(0,numDays):            
            fullDate = startDate + timedelta(days = x)            
            day = fullDate.strftime("%d")
            if int(dID) == int(day):
                 selectedDate = fullDate

        crewNumber = Daily.objects.filter( Period = per, day = selectedDate, Location = loc).last()
        if crewNumber:
            crewNo = crewNumber.crew
        else:
            crewNo = 0

        crew  = Daily(
            Period = per,
            Location = loc,
            day = selectedDate,
            crew = int(crewNo) + 1,
            created_date = datetime.now()
        )

        crew.save()
        per = crew.Period.id
        
        #Adding Audit
        
        operationDetail = "Period: " + str(per) + ", Crew: " + str(crew.crew)
        
        daily_audit(crew.id, operationDetail, "Insert", request.user.username)

        return HttpResponseRedirect('/payroll/' + str(per) + '/' + crew.day.strftime("%d")  + '/'+ str(crew.crew) +'/'+LocID)
    else:
        return HttpResponseRedirect('/payroll/0/0/0/0')
    

def daily_audit(dailyID, opDetail, opType, createBy):
    
    
    dID = Daily.objects.filter( id = dailyID).first()
    
    audit = DailyAudit(
        DailyID = dID,
        operationDetail = opDetail,
        operationType = opType,
        created_date = datetime.now(),
        createdBy =  createBy
    )
    
    audit.save()
    
    return True



def logInAuditLog(request, opType, opDetail):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    if emp:
        Location = emp.Location
    else:
        Location = None

  
    if emp:
        audit = logInAudit(
            Location = Location,
            Period = per,
            EmployeeID = emp,
            operationType = opType,
            operationDetail = opDetail,
            is_staff = request.user.is_staff ,
            is_supervisor = emp.is_supervisor,
            is_admin = emp.is_admin,
            is_superAdmin = emp.is_superAdmin ,
            accounts_payable = emp.accounts_payable,
            created_date = datetime.now(),
            createdBy =  request.user.username
        )
        
        audit.save()
    else:
        audit = logInAudit(
            Location = Location,
            Period = per,
            EmployeeID = emp,
            operationType = opType,
            operationDetail = opDetail,
            is_staff = request.user.is_staff ,
            created_date = datetime.now(),
            createdBy =  request.user.username
        )
        
        audit.save()

    return True

@login_required(login_url='/home/')
def update_daily(request, daily):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    
    context = {}    
    context["emp"] = emp    

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    crew = Daily.objects.filter(id = daily).first()

    if crew:
        sup = request.POST.get('supervisor') 

        crew.supervisor = sup
        crew.save()

        per = crew.Period.id          

        return HttpResponseRedirect('/payroll/' + str(per) + '/' + crew.day.strftime("%d")  + '/'+ str(crew.crew) +'/0')
    else:
        return HttpResponseRedirect('/payroll/0/0/0/0')

@require_http_methods(["GET"])
def get_daily_status(request, daily_id):
    try:
        daily = Daily.objects.get(id=daily_id)
        return JsonResponse({
            'daily_rtb': daily.daily_rtb,
            'daily_wp': daily.daily_wp,
            'daily_cd': daily.daily_cd,
            'daily_nfs': daily.daily_nfs,
            'daily_fd': daily.daily_fd,
            'daily_rtb_pep': daily.daily_rtb_pep
        })
    except Daily.DoesNotExist:
        return JsonResponse({'error': 'Daily not found'}, status=404)

@require_http_methods(["PUT"])
def update_daily_status(request, daily_id):
    try:
        daily = Daily.objects.get(id=daily_id)
        data = json.loads(request.body)
        
        daily.daily_rtb = data.get('daily_rtb', daily.daily_rtb)
        daily.daily_wp = data.get('daily_wp', daily.daily_wp)
        daily.daily_cd = data.get('daily_cd', daily.daily_cd)
        daily.daily_nfs = data.get('daily_nfs', daily.daily_nfs)
        daily.daily_fd = data.get('daily_fd', daily.daily_fd)
        daily.daily_rtb_pep = data.get('daily_rtb_pep', daily.daily_rtb_pep)
        
        daily.save()

        #Updating Work Order Status if needed
        if daily.woID:
            wo = workOrder.objects.filter(id = daily.woID.id).first()
            if wo:
                if daily.daily_rtb:
                    wo.Status = "7"  # RTB                    
                elif daily.daily_rtb_pep:
                    wo.Status = "8"  # RTB_PEP
                
                wo.save()

        return JsonResponse({'success': True, 'message': 'Daily status updated'})
    except Daily.DoesNotExist:
        return JsonResponse({'error': 'Daily not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def update_ptp_Emp(dailyID, split):
    emp_ptp = 0
    crew = Daily.objects.filter(id = dailyID).first()
    if crew:
        itemCount = 0
        itemSum = 0
        
        if bool(split):
            empCount = DailyEmployee.objects.filter(DailyID = crew).count()
           
            if empCount > 0:
                empPtp =  validate_decimals(100 / empCount)
                empList = DailyEmployee.objects.filter(DailyID = crew)

                for empl in empList:
                    empD = DailyEmployee.objects.filter(id = empl.id).first()
                    empD.per_to_pay = empPtp
                    empD.save()
      

        itemCount = DailyItem.objects.filter(DailyID = crew).count()
        if itemCount > 0:            
            itemList = DailyItem.objects.filter(DailyID = crew)

            for iteml in itemList:
                itemSum += iteml.total 

        # Deactivate Own Vehicle per Crew
        """if crew.own_vehicle != None:
            ovp = (itemSum * crew.own_vehicle) / 100
            itemSum += ovp      """               
                                      
        empList = DailyEmployee.objects.filter(DailyID = crew)
        
        for empl in empList:
            rt_pay = 0
            ot_pay = 0
            dt_pay = 0
            empRate = 0
            production = 0
            ovEmp = 0
            
            empD = DailyEmployee.objects.filter(id = empl.id).first()    
            if empD.per_to_pay != None:                                         
                emp_ptp += empD.per_to_pay      

            if itemCount > 0:
                pay_out = validate_decimals(((itemSum * empD.per_to_pay) / 100))
                production = validate_decimals(((itemSum * empD.per_to_pay) / 100))

                #Calculate Own Vehicle Pay = %5 from total Production
                if empl.is_own_vehicle:
                    ovEmp = (itemSum * 5) / 100              
                    pay_out += ovEmp      

            else: 
                if empD.EmployeeID.hourly_rate != None: 
                    empRate = validate_decimals(empD.EmployeeID.hourly_rate)

                rt_pay = (empD.regular_hours * empRate)
                ot_pay = (empD.ot_hour * (empRate * 1.5))
                dt_pay = (empD.double_time * (empRate * 2))
                pay_out = (empD.regular_hours * empRate) + (empD.ot_hour * (empRate * 1.5)) + (empD.double_time * (empRate * 2))

            if empD.on_call != None:
                pay_out += empD.on_call

            if empD.bonus != None:
                pay_out += empD.bonus
            
            empD.rt_pay = rt_pay
            empD.ot_pay = ot_pay
            empD.dt_pay = dt_pay
            empD.emp_rate = empRate
            empD.own_vehicle_pay = ovEmp
            empD.payout = pay_out
            empD.production = production
            empD.save()
        
        crew.total_pay = round(emp_ptp)
        crew.save()
    return emp_ptp

@login_required(login_url='/home/')
def payroll(request, perID, dID, crewID, LocID):
    twTitle = 'TIME WORKED'
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status=1).first()
   
    context = {}    
    if int(perID) > 0:
        per = period.objects.filter(id = perID).first()
    else:
        per = period.objects.filter(status = 1).first()

    context["period"] = per
    context["emp"] = emp

    perActual = period.objects.filter(status__in = (1,2)).first()
    context["per"] = perActual


    opType = "Access Option"
    opDetail = "Payroll"
    logInAuditLog(request, opType, opDetail)



    if int(LocID) > 0:
        loca = Locations.objects.filter(LocationID = LocID).first()
    else:
        if emp:
            if emp.Location is None or not emp.Location:        
                return render(request,'landing.html',{'message':'This user does not have a location assigned', 'alertType':'danger', 'emp':emp})
            elif not per:
                return render(request,'landing.html',{'message':'no active period found', 'alertType':'danger', 'emp':emp})
        else:
            return render(request,'landing.html',{'message':'This user does not have a location assigned', 'alertType':'danger', 'emp':emp})
        
        loca = Locations.objects.filter(LocationID = emp.Location.LocationID).first()

    
    context["location"] = loca

    #getting the list of days per week
    startDate = per.fromDate
    numDays = 7
    week1 = []
    for x in range(0,numDays):
        selectedDay = False
        fullDate = startDate + timedelta(days = x)
        shortDate = fullDate.strftime("%a") + ' ' + fullDate.strftime("%d")
        longDate = fullDate.strftime("%A") + ' ' + fullDate.strftime("%d")
        day = fullDate.strftime("%d")
        if dID == day:
            selectedDay = True
            selectedDate = fullDate
            twTitle += ' - ' + fullDate.strftime("%A").upper() + ', ' + fullDate.strftime("%B %d, %Y").upper()
        
        #obtengo la cantidad de Items asociados
        dItems = Daily.objects.filter(Period = per, Location = loca, day = fullDate)
        totalItems = 0

        for d in dItems:
            dItemDetail = DailyItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

        week1.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay })

    startDate += timedelta(days = numDays)
    week2 = []
    for x in range(0,numDays):
        selectedDay = False
        fullDate = startDate + timedelta(days = x)
        shortDate = fullDate.strftime("%a") + ' ' + fullDate.strftime("%d")
        longDate = fullDate.strftime("%A") + ' ' + fullDate.strftime("%d")
        day = fullDate.strftime("%d")

        if dID == day:
            selectedDay = True
            selectedDate = fullDate
            twTitle += ' - ' + fullDate.strftime("%A").upper() + ', ' + fullDate.strftime("%B %d, %Y").upper()

        #obtengo la cantidad de Items asociados
        dItems = Daily.objects.filter(Period = per, Location = loca, day = fullDate)
        totalItems = 0

        for d in dItems:
            dItemDetail = DailyItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

        week2.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay })
    
    
    if request.user.is_staff or emp.is_superAdmin:
        superV = Employee.objects.filter(is_supervisor=True)
    else:
        superV = Employee.objects.filter(is_supervisor=True)

    if dID != "0":
        # get the list of dailys for the period, Day selected and Location
        crews = Daily.objects.filter(Period = perID, day=selectedDate, Location = loca).order_by('crew')
        context["crew"] = crews

    if crewID != "0":
        dailyID = Daily.objects.filter(Period = perID, day=selectedDate, crew = crewID, Location = loca ).first()
        dailyEmp = DailyEmployee.objects.filter(DailyID = dailyID).order_by('created_date')
        context["dailyEmp"] = dailyEmp

        #if the Payroll comes from Mobile, get the Mobile Info

        if dailyID.mobile_id:
            mobileInfo = MobileModel.DailyMob.objects.filter(id = dailyID.mobile_id).first()
            context["mobileInfo"] = mobileInfo
        else:
            context["mobileInfo"] = None

        dailyItem = DailyItem.objects.filter(DailyID = dailyID).order_by('created_date')
        dailyTotal = 0
        ovT = 0
        for di in dailyItem:
            dailyTotal += di.total 


        if dailyID.own_vehicle != None:
            ovT = (dailyTotal * dailyID.own_vehicle) / 100
        
        granTotal = dailyTotal + ovT


        #Adding the documents Maps
        dailyDocs = DailyDocs.objects.filter(DailyID = dailyID, docType=1).order_by('created_date')

        #Adding the documents Pictures
        dailyDocsPic = DailyDocs.objects.filter(DailyID = dailyID, docType=2).order_by('created_date')

        #Adding the documents Material Backup
        dailyDocsMB = DailyDocs.objects.filter(DailyID = dailyID, docType=3).order_by('created_date')
        

  
        context["dailyDocs"] = dailyDocs
        context["dailyDocsPic"] = dailyDocsPic
        context["dailyDocsMB"] = dailyDocsMB

        context["dailyItem"] = dailyItem        
        context["TotalItem"] = dailyTotal
        context["ovTotal"] = ovT
        context["GranTotalItem"] = granTotal



    if request.method == 'POST':
        dailyID = request.POST.get('daily')
        sup = request.POST.get('supervisor') 
        split = request.POST.get('split')
        ptp = request.POST.get('ptp')
        ov = request.POST.get('ov')
        crew = Daily.objects.filter(id = dailyID).first()
        if crew:            
            crew.supervisor = sup                      
            crew.split_paymet = bool(split)   

            if ov != '':
                crew.own_vehicle = ov
            else:
                crew.own_vehicle = None    

            emp_ptp = update_ptp_Emp(dailyID, bool(split))

            crew.total_pay = emp_ptp     
            crew.save()
            per = crew.Period.id  

            emp_ptp = update_ptp_Emp(dailyID, bool(split))       
            
            if int(str(sup))>0 and crew.woID != None:
                super = Employee.objects.filter(employeeID = sup ).first()
                if super:   
                    wo = workOrder.objects.filter( id = crew.woID.id).first()
                    if wo:             
                        wo.WCSup = super
                        wo.save()       
                        
                        
                        #Adding Audit
                        operationDetail = "Change on Selected Supervisor- New Supervisor: " + str(super) + ", Own Vehicle: " + str(ov) + ", Split: " + str(bool(split))
                        
                        daily_audit(crew.id, operationDetail, "Insert/Update", request.user.username)
     
            
        
        return HttpResponseRedirect('/payroll/' + str(crew.Period.id) + '/' + crew.day.strftime("%d") + '/' + str(crew.crew) +'/' + str(LocID))        



                   
    context["week1"] = week1
    context["week2"] = week2
    context["selectedDate"] = twTitle
    context["superV"] = superV
    context["selectedCrew"] = int(crewID)
    context["selectedDay"] = int(dID)
    context["selectedLocation"] = LocID
    
    return render(request, "payroll.html", context)


def calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime):
    
    if startTime != None and endTime != None:
        if startTime > endTime:
            total = 0
        else:
            #convert to decimal
            startTime = startTime/100
            st_h = int(startTime) 
            st_m = validate_decimals(startTime % 1)* 100
            st_total = validate_decimals(st_h + validate_decimals(st_m / 60))
            
            endTime = endTime / 100
            et_h = int(endTime) 
            et_m = validate_decimals(endTime % 1)* 100
            et_total = validate_decimals(et_h + validate_decimals(et_m / 60))
            
            total = et_total - st_total
    else:
        total = 0 
    
    if lunch_startTime != None and lunch_endTime != None:
        lunch_startTime = lunch_startTime / 100
        lunch_endTime = lunch_endTime / 100
        
        if lunch_startTime > lunch_endTime:
            total_lunch = 0
        elif lunch_startTime > endTime or lunch_endTime > endTime:
            total_lunch = 0
        else:
            #convert to decimal
            lst_h = int(lunch_startTime) 
            lst_m = validate_decimals(lunch_startTime % 1) * 100
            lst_total = validate_decimals(lst_h + validate_decimals(lst_m / 60))
            
            let_h = int(lunch_endTime) 
            let_m = validate_decimals(lunch_endTime % 1)* 100
            let_total = validate_decimals(let_h + validate_decimals(let_m / 60))
            
            total_lunch = let_total - lst_total
    else:
        total_lunch = 0
    
    endTotal = total - total_lunch
    
    if endTotal <= 8:          
        regular_hours =  validate_decimals(endTotal)
        ot_hours = 0
        double_time = 0
    elif endTotal > 8 and endTotal <= 12:
        regular_hours =  8
        ot_hours = (float(endTotal) - 8)   
        double_time = 0
    elif endTotal > 12:
        regular_hours =  8
        ot_hours = 4
        double_time = (float(endTotal) - 12)   
    else:
        regular_hours =  0
        ot_hours = 0
        double_time = 0
        

    total_hours = regular_hours + ot_hours + double_time

    return total_hours, regular_hours, ot_hours, double_time


    """
    def calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime):
    
    if startTime != None and endTime != None:
        if startTime > endTime:
            total = 0
        else:
            total = int(str(endTime)) - int(str(startTime))      
    else:
        total = 0            
    
    if lunch_startTime != None and lunch_endTime != None:
        if lunch_startTime > lunch_endTime:
            total_lunch = 0
        elif lunch_startTime > endTime or lunch_endTime > endTime:
            total_lunch = 0
        else:
            total_lunch = int(str(lunch_endTime)) - int(str(lunch_startTime))

            #if total_lunch < 100 and total %1 > 0:
            if total_lunch < 100 and (total + total_lunch + 40) % 1  > 0: 
                total_lunch = total_lunch + 40

    else:
        total_lunch = 0


    endTotal = total - total_lunch

    if endTotal > 100:
        endTotal = endTotal / 100
    elif endTotal < 0:
        endTotal = 0

    

    if endTotal <= 8:           
        r_h = int(endTotal) 
        r_m = validate_decimals(endTotal % 1)* 100
        regular_hours =  validate_decimals(r_h + (r_m / 60))
        ot_hours = 0
        double_time = 0
    elif endTotal > 8 and endTotal <= 12:
        regular_hours =  8
        ot_temp = (float(endTotal) - 8)   
        ot_h = int(ot_temp) 
        ot_m = validate_decimals(ot_temp % 1)* 100
        ot_hours = validate_decimals(ot_h + (ot_m / 60))   
        double_time = 0
    elif endTotal > 12:
        regular_hours =  8
        ot_hours = 4
        db_temp = (float(endTotal) - 12)   
        db_h = int(db_temp) 
        db_m = validate_decimals(db_temp % 1) *100
        double_time = validate_decimals(db_h + (db_m / 60))       
    else:
        regular_hours =  0
        ot_hours = 0
        double_time = 0  
        
        

    total_hours = regular_hours + ot_hours + double_time

    return total_hours, regular_hours, ot_hours, double_time"""
        
@login_required(login_url='/home/')    
def create_daily_emp(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    dailyID = Daily.objects.filter(id = id).first()

    dailyE = DailyEmployee.objects.filter(DailyID = dailyID)
    empList = []

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    for i in dailyE:
       empList.append(i.EmployeeID.employeeID) 

    EmpLocation = Employee.objects.filter(is_active = True, is_supervisor = False).exclude(employeeID__in = empList)


    form = DailyEmpForm(request.POST or None, initial={'DailyID': dailyID}, qs = EmpLocation)
    if form.is_valid():                
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time

        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)
        form.instance.created_date = datetime.now()

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp
        form.save()  

        #Adding Audit
        operationDetail = "Adding a Employee: " + str(selectedEmp) + ", % to pay: " + str(form.instance.per_to_pay) + ", on Call: " + str(form.instance.on_call) + ", Bonus: " + str(form.instance.bonus) + ", Start Time: " + str(startTime) + ", Lunch Start Time: " + str(lunch_startTime) + ", Lunch End Time: " + str(lunch_endTime) + ", End Time: " + str(endTime)
        
        daily_audit(id, operationDetail, "Insert", request.user.username)

        update_ptp_Emp(id, dailyID.split_paymet)             
        return HttpResponseRedirect('/payroll/' + str(dailyID.Period.id) + '/' + dailyID.day.strftime("%d") + '/' + str(dailyID.crew) +'/' + str(LocID))        
         
    context['form']= form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    return render(request, "create_daily_emp.html", context)

@login_required(login_url='/home/')
def update_daily_emp(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}    
    obj = get_object_or_404(DailyEmployee, id = id)

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per    

    EmpLocation = Employee.objects.all()
    empSelected = Employee.objects.filter(employeeID = obj.EmployeeID.employeeID ).first()
 
    form = DailyEmpForm(request.POST or None, instance = obj, qs = EmpLocation)
 
    if form.is_valid():      
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time

        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp

        form.save()
        
         #Adding Audit
        operationDetail = "Updating a Employee: " + str(selectedEmp) + ", % to pay: " + str(obj.per_to_pay) + ", on Call: " + str(obj.on_call) + ", Bonus: " + str(obj.bonus) + ", Start Time: " + str(startTime) + ", Lunch Start Time: " + str(lunch_startTime) + ", Lunch End Time: " + str(lunch_endTime) + ", End Time: " + str(endTime)
        
        daily_audit(obj.DailyID.id, operationDetail, "Update", request.user.username)

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        context["emp"] = emp       
        return HttpResponseRedirect('/payroll/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) + '/' + str(LocID)) 

    dailyID = Daily.objects.filter(id = obj.DailyID.id).first()

    context["form"] = form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    context["empSelected"] = empSelected
    
    return render(request, "update_daily_emp.html", context)

@login_required(login_url='/home/')
def delete_daily_emp(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    obj = get_object_or_404(DailyEmployee, id = id)
 
    context["form"] = obj
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    if request.method == 'POST':
        
        
         #Adding Audit
        operationDetail = "Deleting a Employee: " + str(obj.EmployeeID) + ", % to pay: " + str(obj.per_to_pay) + ", on Call: " + str(obj.on_call) + ", Bonus: " + str(obj.bonus) + ", Start Time: " + str(obj.start_time) + ", Lunch Start Time: " + str(obj.start_lunch_time) + ", Lunch End Time: " + str(obj.end_lunch_time) + ", End Time: " + str(obj.end_time)
        
        daily_audit(obj.DailyID.id, operationDetail, "Delete", request.user.username)

        
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 
        
        
       
        return HttpResponseRedirect('/payroll/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 

   
    return render(request, "delete_daily_emp.html", context)

@login_required(login_url='/home/')
def create_daily_item(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    dailyID = Daily.objects.filter(id = id).first()

    dailyI = DailyItem.objects.filter(DailyID = dailyID)
    itemList = []

    for i in dailyI:
       itemList.append(i.itemID.item.itemID) 

    #itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID).exclude(item__itemID__in = itemList)


    #Validate if the WO was created after the Prices Update
    priceUpdate = "2025-03-03"
    priceCreated = dailyID.woID.created_date

    if priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date():
        itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= True).exclude(item__itemID__in = itemList)
    else:
        itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= False).exclude(item__itemID__in = itemList)

    context["is_new"] = priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date()
    context["created"] = datetime.strftime(priceCreated.date(), "%Y-%m-%d")


    form = DailyItemForm(request.POST or None, initial={'DailyID': dailyID}, qs = itemLocation)
    if form.is_valid():    
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        price = form.instance.itemID.price   
        Emppayout = form.instance.itemID.emp_payout 
        
        form.instance.emp_payout = float(Emppayout)
        if form.instance.itemID.price != None and form.instance.itemID.price != "":
            price = form.instance.itemID.price   
        else:
            price = 0
            
        form.instance.price = float(price)
        form.instance.total = form.instance.quantity * float(Emppayout)
        form.instance.created_date = datetime.now()

        form.save()      
        
        #Adding Audit
        
        operationDetail = "Adding Item: " + str(form.instance.itemID) + ", Quantity: " + str(form.instance.quantity) + ", Total: " + str(form.instance.total)
        
        daily_audit(form.instance.DailyID.id, operationDetail, "Insert", request.user.username)
        

        update_ptp_Emp(id, dailyID.split_paymet)

        return HttpResponseRedirect('/payroll/' + str(dailyID.Period.id) + '/' + dailyID.day.strftime("%d") + '/' + str(dailyID.crew) +'/' + str(LocID))        
         
    context['form']= form
    context["emp"] = emp
    context["DailyID"] = dailyID
    context["itemList"] = itemLocation
    return render(request, "create_daily_item.html", context)

@login_required(login_url='/home/')
def update_daily_item(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyItem, id = id)

    itemLocation = itemPrice.objects.filter(location__LocationID = obj.DailyID.Location.LocationID)
    
    itemSelected = itemPrice.objects.filter(id = obj.itemID.id ).first()

    form = DailyItemForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if form.is_valid():
        #PJIG Aqui se modifico antes estaba price = form.instance.itemID.emp_payout
        price = form.instance.itemID.price
        form.instance.price = float(price)
        form.instance.total = form.instance.quantity * float(form.instance.itemID.emp_payout)
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        form.save()
        context["emp"] = emp    
        
         #Adding Audit
        
        operationDetail = "Updating Item: " + str(form.instance.itemID) + ", Quantity: " + str(form.instance.quantity) + ", Total: " + str(form.instance.total)
        
        daily_audit(form.instance.DailyID.id, operationDetail, "Update", request.user.username)

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        return HttpResponseRedirect('/payroll/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/'+str(LocID)) 

    context["form"] = form
    context["emp"] = emp
    context["itemSelected"] = itemSelected

    return render(request, "update_daily_item.html", context)

@login_required(login_url='/home/')
def delete_daily_item(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyItem, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        
         #Adding Audit
        
        operationDetail = "Deleting Item: " + str(obj.itemID) + ", Quantity: " + str(obj.quantity) + ", Total: " + str(obj.total)
        
        daily_audit(obj.DailyID.id, operationDetail, "Delete", request.user.username)
        
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        return HttpResponseRedirect('/payroll/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 

   
    return render(request, "delete_daily_item.html", context)


#*********************** documents upload ***********************

class BulkUploadView(View):
    def post(self, request, id, LocID, docType, *args, **kwargs):
        form = DailyDocsForm(request.POST, request.FILES)

        if form.is_valid():
            daily_id = form.cleaned_data['DailyID']
            doc_type = form.cleaned_data['docType']            
            files = self.request.FILES.getlist('files')
            
            created_docs = []
            for file in files:
                doc = DailyDocs(
                    DailyID=daily_id,
                    docType=docType,
                    docName=os.path.splitext(file.name)[0],
                    document=file,
                    createdBy=self.request.user.username,
                    Status = 1,
                    created_date=datetime.now()
                )
                doc.save()
                created_docs.append({                    
                    'id': doc.id,
                    'name': doc.docName,
                    'url': doc.document.url,
                    'docType': docType,
                })
            
            return JsonResponse({'success': True, 'documents': created_docs})   
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    def get(self, request, id, LocID, docType, *args, **kwargs):
        emp = Employee.objects.filter(user__username__exact = request.user.username).first()
        context ={}

        per = period.objects.filter(status__in=(1,2)).first()
        context["per"] = per

        dailyID = Daily.objects.filter(id = id).first()

        # Add this if you need a GET handler for the form page
        form = DailyDocsForm(initial={
            'DailyID': dailyID , # Auto-set DailyID from URL parameter if needed
            'docType': docType
        })

        return render(request, 'create_daily_doc.html', {'form': form, 'dailyID': dailyID, 'emp': emp, 'docType': docType,'selectedLocation': LocID})

@login_required(login_url='/home/')
def delete_daily_docs(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyDocs, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if obj:
        
        obj.delete()

    return HttpResponseRedirect('/payroll/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 

@login_required(login_url='/home/')
def upload_daily(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    context ={}  
    context["emp"] = emp
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    if request.method == 'POST':
        new_daily = request.FILES['myfile']
        
        d = Daily.objects.filter(id = id).first()

        if d:
            filename = d.day.strftime("%m%d%Y") + "-C" + str(d.crew) + "-" + d.Location.name + "-" + d.Period.weekRange + ".pdf"           
            new_daily.name = filename
            d.pdfDaily = new_daily            
            d.save()           
        else:
            filename = "daily.pdf"

        return HttpResponseRedirect('/payroll/' + str(d.Period.id) + '/' + d.day.strftime("%d") + '/' + str(d.crew) +'/' + str(LocID))   

    return render(request, "upload_daily.html", context)

@login_required
@require_POST
def record_daily_pdf_download(request, daily_id):
    """
    Registra en la BD que el PDF asociado a Daily (item.pdfDaily) fue descargado:
    """
    try:
        daily = Daily.objects.filter(id=daily_id).first()
    except Daily.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


    try:
        daily.download_date = datetime.now()
        daily.downloaded_by = request.user.username
        daily.save()
    except Daily.DoesNotExist:
        return JsonResponse({'error': 'Error updating data'}, status=405)


    return JsonResponse({'status': 'ok'})


def recap(request, perID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    

    error= ""
    
    empList = Employee.objects.all()   
    per = period.objects.filter(status__in=(1,2)).first()

    for item in empList:

        try:
            dailyEmp = DailyEmployee.objects.filter(EmployeeID = item, DailyID__Period = perID).count()

            if dailyEmp > 0:
                file = make_recap_pdf(item.employeeID,perID)

                empRecap = employeeRecap.objects.filter(EmployeeID = item, Period = per).first()
                
                if empRecap:

                    empRecap.recap = file
                    empRecap.save()

                else:

                    remplo = employeeRecap( Period = per,
                                        EmployeeID = item,
                                        recap = file )
                    remplo.save()
        except Exception as e:
            return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})
   
    
    return HttpResponseRedirect('/location_period_list/' + perID)     


def make_recap_pdf(empID, perID):
    context= {}  

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    template_path = 'recap_template.html'

    template= get_template(template_path)
    
    fileName = "recap-1.pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + fileName
    
    lines = []
    lines2 = []
    itemHtml = ''
    itemHtml2 = ''
    
    per = period.objects.filter(id = perID).first()
    context["period"] = per

    emp = Employee.objects.filter(employeeID = empID).first()
    context["emp"] = emp

    dailyemp = DailyEmployee.objects.filter(EmployeeID = emp, DailyID__Period = per).order_by('DailyID__day')

    contador = 0
    rtTotal = 0
    otTotal = 0
    dtTotal = 0
    ocTotal = 0
    bonTotal = 0
    prodTotal = 0
    ovTotal = 0
    payTotal = 0
    line2 = False 

    for item in dailyemp:
        contador += 1
        rt = 0
        ot = 0
        dt = 0
        on_call = 0
        bonus = 0
        

        prod = DailyItem.objects.filter(DailyID = item.DailyID).count()

        if prod <= 0:           
            #if item.EmployeeID.hourly_rate != None:
            rt = validate_decimals(item.rt_pay)
            ot = validate_decimals(item.ot_pay)
            dt = validate_decimals(item.dt_pay)
                
        payroll = item.payout
        on_call = item.on_call
        bonus = item.bonus

        itemd = DailyItem.objects.filter(DailyID = item.DailyID)

        total = 0
        for i in itemd:
            total += i.total

        production = (total * item.per_to_pay) / 100
        
        #if item.DailyID.own_vehicle != None:
        #    own_vehicle = (((total * item.DailyID.own_vehicle) / 100) * item.per_to_pay) / 100
        #else:
        #    own_vehicle = 0

        # Se cambia formula para el calculo del OV
        if item.is_own_vehicle:
            own_vehicle = item.own_vehicle_pay
        else:
            own_vehicle = 0


        rtTotal += rt
        otTotal += ot
        dtTotal += dt
        if on_call != None:
            ocTotal += on_call

        if bonus != None:
            bonTotal += bonus

        prodTotal += production
        ovTotal += own_vehicle
        payTotal += payroll

        if contador <= 45:
            itemHtml = itemHtml + '<tr style=" height: 20px;"> '          
            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #444; border-right:1px solid #999; padding-top: 3px;" width="12%" align="center"> '
            
            if item.DailyID.Location == None:
                itemHtml = itemHtml + '&nbsp;'
            else:
                itemHtml = itemHtml + item.DailyID.Location.name
                            
            itemHtml = itemHtml + '</td>'
            itemHtml = itemHtml + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            itemHtml = itemHtml + item.DailyID.day.strftime('%Y-%m-%d')
            itemHtml = itemHtml + ' </td> '
            
            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:7px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="20%" align="center">'
            itemHtml = itemHtml + item.DailyID.woID.JobAddress
            itemHtml = itemHtml + ' </td>'
            
            itemHtml = itemHtml + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if rt!= 0:
                itemHtml = itemHtml + '${0:,.2f}'.format((float(rt)))
            itemHtml = itemHtml + '</td>'
                            
            itemHtml = itemHtml + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if ot != 0:                    
                itemHtml = itemHtml + '${0:,.2f}'.format((float(ot)))
            itemHtml = itemHtml + ' </td> '
            
            itemHtml = itemHtml + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if dt != 0:                    
                itemHtml = itemHtml +'${0:,.2f}'.format((float(dt)))
            itemHtml = itemHtml + '</td>'
               
                                
                            
            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if production != 0:
                itemHtml = itemHtml + '${0:,.2f}'.format((float(production)))
            itemHtml = itemHtml + '</td>'


            itemHtml = itemHtml + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if own_vehicle != 0:
                itemHtml = itemHtml +  '${0:,.2f}'.format((float(own_vehicle)))           
            itemHtml = itemHtml + '</td>'
            

            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if on_call != 0 and on_call != None:
                itemHtml = itemHtml + '${0:,.2f}'.format((float(on_call)))
            itemHtml = itemHtml + '</td>'
            
                    
            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if bonus != 0 and bonus != None:
                itemHtml = itemHtml + '${0:,.2f}'.format((float(bonus)))
            itemHtml = itemHtml + '</td>'
            

            itemHtml = itemHtml + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #444; padding-top: 3px;" width="8%" align="center">'
            if payroll != 0 and payroll != None:
                itemHtml = itemHtml + '${0:,.2f}'.format((float(payroll)))
            itemHtml = itemHtml + '</td>'
            
                         
            itemHtml = itemHtml + '</tr>'
        else:
            line2 = True
            itemHtml2 = itemHtml2 + ' <tr style=" height: 20px;"> '          
            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #444; border-right:1px solid #999; padding-top: 3px;" width="12%" align="center"> '
            if item.DailyID.Location == None:
                itemHtml2 = itemHtml2 + '&nbsp;'
            else:
                itemHtml2 = itemHtml2 + item.DailyID.Location.name
                            
            itemHtml2 = itemHtml2 + '</td>'
            itemHtml2 = itemHtml2 + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            itemHtml2 = itemHtml2 + item.DailyID.day.strftime('%Y-%m-%d')
            itemHtml2 = itemHtml2 + ' </td> '
            
            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:7px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="20%" align="center">'
            itemHtml2 = itemHtml2 + item.DailyID.woID.JobAddress
            itemHtml2 = itemHtml2 + ' </td>'
            
            itemHtml2 = itemHtml2 + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if rt!= 0:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(rt)))
            itemHtml2 = itemHtml2 + '</td>'
                            
            itemHtml2 = itemHtml2 + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if ot != 0:                    
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(ot))) 
            itemHtml2 = itemHtml2 + ' </td> '
            
            itemHtml2 = itemHtml2 + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if dt != 0:                    
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(dt)))
            itemHtml2 = itemHtml2 + '</td>'
               
                                
                            
            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if production != 0:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(production)))
            itemHtml2 = itemHtml2 + '</td>'


            itemHtml2 = itemHtml2 + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
            if own_vehicle != 0:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(own_vehicle))) 
            itemHtml2 = itemHtml2 + '</td>'
            

            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if on_call != 0 and on_call != None:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(on_call)))
            itemHtml2 = itemHtml2 + '</td>'
            
                    
            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
            if bonus != 0 and bonus != None:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(bonus)))
            itemHtml2 = itemHtml2 + '</td>'
            

            itemHtml2 = itemHtml2 + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #444; padding-top: 3px;" width="8%" align="center">'
            if payroll != 0 and payroll != None:
                itemHtml2 = itemHtml2 + '${0:,.2f}'.format((float(payroll)))
            itemHtml2 = itemHtml2 + '</td>'
            
                         
            itemHtml2 = itemHtml2 + '</tr>'



    itemLine = ''
    
    itemLine = itemLine + '<tr style=" height: 20px;"> '          
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #444; border-right:1px solid #999; padding-top: 3px;" width="12%" align="center"> '
    itemLine = itemLine + '&nbsp;'
    itemLine = itemLine + '</td>'
    itemLine = itemLine + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'
    itemLine = itemLine + ' </td> '   
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:7px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="20%" align="center">'
    itemLine = itemLine + ' </td>'   
    itemLine = itemLine + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'
    itemLine = itemLine + '</td>'                 
    itemLine = itemLine + ' <td style=" font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'   
    itemLine = itemLine + ' </td> '  
    itemLine = itemLine + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'  
    itemLine = itemLine + '</td>'                
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">' 
    itemLine = itemLine + '</td>'
    itemLine = itemLine + '<td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="8%" align="center">'   
    itemLine = itemLine + '</td>'
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'   
    itemLine = itemLine + '</td>'        
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #999; padding-top: 3px;" width="7%" align="center">'    
    itemLine = itemLine + '</td>'    
    itemLine = itemLine + ' <td style="font-family:Verdana, Geneva, sans-serif; font-weight:200; font-size:8px; border-top:1px solid #999; border-bottom:1px solid #999; border-left:1px solid #999; border-right:1px solid #444; padding-top: 3px;" width="8%" align="center">'
    itemLine = itemLine + '</td>'                      
    itemLine = itemLine + '</tr>'
    
    itemLineFinal2 = ''
    itemLineFinal = ''
    if contador <= 45:
        itemLineFinal = itemLine * (45-contador)
    else:
         line2 = True
         itemLineFinal2 = itemLine * (50 - (contador-45))
    
    """if contador <= 45:
        for x in range(0,45-contador):
            lines.append({'line':x, 'Location': None, 'date': None, 'address': '',
                       'rt': 0, 'ot': 0, 'dt': 0, 'production': 0, 'own_vehicle': 0 , 'on_call': None,  'bonus': None,'payroll': 0})
    else:
        for x in range(45,95-contador):
            line2 = True
            lines2.append({'line':x, 'Location': None, 'date': None, 'address': '',
                        'rt': 0, 'ot': 0, 'dt': 0, 'production': 0, 'own_vehicle': 0 , 'on_call': None,  'bonus': None, 'payroll': 0})"""

    context["lines"] = lines
    context["lines2"] = lines2
    context["line2"] = line2
    context["rtTotal"] = rtTotal
    context["otTotal"] = otTotal
    context["dtTotal"] = dtTotal
    context["ocTotal"] = ocTotal
    context["bonTotal"] = bonTotal
    context["prodTotal"] = prodTotal
    context["ovTotal"] = ovTotal
    context["payTotal"] = payTotal
    context["itemHtml"] = itemHtml
    context["itemHtml2"] = itemHtml2
    context["itemLine"] = itemLineFinal
    context["itemLine2"] = itemLineFinal2


    
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)


    output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=output)
    file_name = str(emp.employeeID) + " " + emp.last_name + " " + emp.first_name + " " + per.weekRange
    myPdf = ContentFile(output.getvalue(),file_name + '.pdf')

    return myPdf


def generate_recap(empID, perID):
    context= {}  

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    template_path = 'recap_template.html'

    template= get_template(template_path)
    
    fileName = "recap-1.pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + fileName
    
    lines = []
    lines2 = []

    per = period.objects.filter(id = perID).first()
    context["period"] = per

    emp = Employee.objects.filter(employeeID = empID).first()
    context["emp"] = emp

    dailyemp = DailyEmployee.objects.filter(EmployeeID = emp, DailyID__Period = per)

    contador = 0
    rtTotal = 0
    otTotal = 0
    dtTotal = 0
    ocTotal = 0
    bonTotal = 0
    prodTotal = 0
    ovTotal = 0
    payTotal = 0
    line2 = False 

    for item in dailyemp:
        contador += 1
        rt = 0
        ot = 0
        dt = 0
        on_call = 0
        bonus = 0
        

        prod = DailyItem.objects.filter(DailyID = item.DailyID).count()

        if prod <= 0:           
            if item.EmployeeID.hourly_rate != None:
                rt = (item.regular_hours * float(item.EmployeeID.hourly_rate))
                ot = ((item.ot_hour * (float(item.EmployeeID.hourly_rate)*1.5)))
                dt = ((item.double_time * (float(item.EmployeeID.hourly_rate)*2)))

        payroll = item.payout
        on_call = item.on_call
        bonus = item.bonus

        itemd = DailyItem.objects.filter(DailyID = item.DailyID)

        total = 0
        for i in itemd:
            total += i.total

        production = (total * item.per_to_pay) / 100
        if item.DailyID.own_vehicle != None:
            own_vehicle = (((total * item.DailyID.own_vehicle) / 100) * item.per_to_pay) / 100
        else:
            own_vehicle = 0

        rtTotal += rt
        otTotal += ot
        dtTotal += dt
        if on_call != None:
            ocTotal += on_call

        if bonus != None:
            bonTotal += bonus

        prodTotal += production
        ovTotal += own_vehicle
        payTotal += payroll

        if contador <= 45:
            lines.append({'line':contador, 'Location': item.DailyID.Location.name,
                       'date': item.DailyID.day, 'address': item.DailyID.woID.JobAddress,
                       'rt': rt, 'ot': ot, 'dt': dt, 'production': production , 'own_vehicle': own_vehicle, 'on_call': on_call, 'bonus': bonus, 'payroll': payroll })
        else:
            line2 = True
            lines2.append({'line':contador, 'Location': item.DailyID.Location.name,
                       'date': item.DailyID.day, 'address': item.DailyID.woID.JobAddress,
                       'rt': rt, 'ot': ot, 'dt': dt, 'production': production , 'own_vehicle': own_vehicle, 'on_call': on_call, 'bonus': bonus, 'payroll': payroll })


    """if contador <= 45:
        for x in range(0,45-contador):
            lines.append({'line':x, 'Location': None, 'date': None, 'address': '',
                       'rt': 0, 'ot': 0, 'dt': 0, 'production': 0, 'own_vehicle': 0 , 'on_call': None,  'bonus': None,'payroll': 0})
    else:
        for x in range(45,95-contador):
            line2 = True
            lines2.append({'line':x, 'Location': None, 'date': None, 'address': '',
                        'rt': 0, 'ot': 0, 'dt': 0, 'production': 0, 'own_vehicle': 0 , 'on_call': None,  'bonus': None, 'payroll': 0})"""

    context["lines"] = lines
    context["lines2"] = lines2
    context["line2"] = line2
    context["rtTotal"] = rtTotal
    context["otTotal"] = otTotal
    context["dtTotal"] = dtTotal
    context["ocTotal"] = ocTotal
    context["bonTotal"] = bonTotal
    context["prodTotal"] = prodTotal
    context["ovTotal"] = ovTotal
    context["payTotal"] = payTotal


    
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)


    output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=output)
    file_name = str(emp.employeeID) + " " + emp.last_name + " " + emp.first_name + " " + per.weekRange
    myPdf = ContentFile(output.getvalue(),file_name + '.pdf')

    return myPdf

@login_required(login_url='/home/')
def send_recap(request, perID):
    empSelected =request.POST.get('Employees')
   
    try:
        if empSelected != 0:
            empList = empSelected.split(",")
            per = period.objects.filter(id = perID).first()
            if per:
                empRecap = employeeRecap.objects.filter(Period = per, EmployeeID__employeeID__in = empList)

                for item in empRecap:
                    subject = 'Recap Weeks ' + per.weekRange
                    message = 'Hello ' + item.EmployeeID.last_name + ' ' + item.EmployeeID.first_name + ','
                    message += '\n \n Attached you can find the recap of the weeks ' + per.weekRange
                    message += '\n please review it and let me know if you have any question or problem.'
                    message += '\n \n best regards,'
                    emailTo = item.EmployeeID.email
                    if emailTo != None:
                        email =  EmailMessage(subject,message, 'hrdepartment@wiringconnection.com' ,[emailTo])
                        email.attach_file(item.recap.path)                    
                        email.send()

                        item.mailingDate = datetime.now()
                        item.save()
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})
   

    return HttpResponseRedirect('/location_period_list/' + perID) 

def send_email_recap(request, subject, message, destination):
    email_sender= os.environ.get('DEFAULT_FROM_EMAIL')
    email_pass= settings.EMAIL_HOST_PASSWORD
    
    SMTPserver = os.environ.get('EMAIL_HOST')
    sender =     os.environ.get('EMAIL_HOST_USER')    

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'html'

    msg = MIMEText(message, text_subtype)
    msg['Subject']= subject
    msg['From']   = sender 
    msg['To']   = destination

    conn = SMTP(SMTPserver)
    conn.set_debuglevel(False)
    conn.login(email_sender, email_pass)
    try:
        conn.sendmail(sender, [destination], msg.as_string())
    finally:
        conn.quit()

    

@login_required(login_url='/home/')
def send_recap_emp(request, perID, empID):   
    per = period.objects.filter(id = perID).first()
    emp = Employee.objects.filter(employeeID = empID).first()
    try:
        if per and emp:
            empRecap = employeeRecap.objects.filter(Period = per, EmployeeID = emp)

            for item in empRecap:
                subject = 'Recap Weeks ' + per.weekRange
                message = 'Hello ' + item.EmployeeID.last_name + ' ' + item.EmployeeID.first_name + ','
                message += '\n \n Attached you can find the recap of the weeks ' + per.weekRange
                message += '\n please review it and let me know if you have any question or problem.'
                message += '\n \n best regards,'

                emailTo = item.EmployeeID.email              
                
                if emailTo != None:
                    email = EmailMessage(subject,message, 'hrdepartment@wiringconnection.com' ,[emailTo])
                    email.attach_file(item.recap.path)                
                    email.send()

                    #send_email_recap(request, subject, message, emailTo)

                    item.mailingDate = datetime.now()
                    item.save()
                
                
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e) + "////" + settings.EMAIL_HOST_PASSWORD + "+++", 'alertType':'danger','emp':emp, 'per': per})
   

    return HttpResponseRedirect('/location_period_list/' + perID) 

@login_required(login_url='/home/')
def get_list_orders_bySupervisor(request,estatus, loc,pid,addR,invNumber,invAmount,invAmountF):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    locationObject = Locations.objects.filter(LocationID=loc).first() 
    #
    if emp.is_manager:

        locaList = employeeLocation.objects.filter(employeeID = emp)
                
        locationList = []
        locationList.append(emp.Location.LocationID)
        
        for i in locaList:
            locationList.append(i.LocationID.LocationID)

        if emp.Location!= None:
            if estatus == "0" and loc == "0":     
                if pid != None and pid != "-1":
                    orders = workOrder.objects.filter(prismID__exact = pid, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif addR != None and addR !="-1":
                    orders = workOrder.objects.filter(JobAddress__contains = addR, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif invNumber !="-1" and invNumber != None:
                    
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)
                    orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                elif  invAmount !="-1" and invAmount != None and invAmountF !="-1" and invAmountF != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False)  
                elif  invAmount !="-1" and invAmount != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False)    
                else:     
                    orders = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )            
            else:
                if estatus != "0" and loc != "0":
                    orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )                 
                else:
                    if estatus != "0":
                        orders = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )
                    else:    
                        orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )
        else:
            orders = None

        return orders  
    elif emp.is_supervisor:
        if estatus == "0" and loc == "0":     
            if pid != None and pid != "-1":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif addR != None and addR !="-1":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif invNumber !="-1" and invNumber != None:
                
                #Getting the OrderList by Invoice Number
                
                woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                woInvLits = []
                
                for i in woInv:
                    woInvLits.append(i.woID.id)
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
            elif  invAmount !="-1" and invAmount != None and invAmountF !="-1" and invAmountF != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)  
            elif  invAmount !="-1" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)    
            else:     
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID).exclude(linkedOrder__isnull = False, uploaded = False )            
        else:
            if estatus != "0" and loc != "0":
                orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )                 
            else:
                if estatus != "0":
                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
                else:    
                    orders = workOrder.objects.filter(WCSup__employeeID__exact=emp.employeeID, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )
        
        return orders           
    else:
        orders = workOrder.objects.filter(WCSup__employeeID__exact=0, Location__isnull=False).exclude(linkedOrder__isnull = False, uploaded = False )
        return orders

@login_required(login_url='/home/')
def get_list_orders(request,estatus, loc, pid,addR,invNumber,invAmount,invAmountF):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()

    context= {} 

    if loc == None or loc =="":
        loc = "0"

    locationObject = Locations.objects.filter(LocationID=loc).first()    

    if emp:
        if emp.is_superAdmin:                
            if estatus == "0" and loc == "0":                   
                if pid != None and pid != "-1":
                    orders = workOrder.objects.filter(prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)    
                elif addR != None and addR !="-1":
                    orders = workOrder.objects.filter(JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
                elif invNumber !="-1" and invNumber != None:                    
                    #Getting the OrderList by Invoice Number                    
                    woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)
                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)                    
                elif  invAmount !="-1" and invAmount != None and invAmountF !="-1" and invAmountF != None:      
                    #Getting the OrderList by Invoice Number                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)                     
                elif  invAmount !="-1" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                else:  
                    orders = workOrder.objects.filter(id = -1)   
            else:
                if estatus != "0" and loc != "0":
                    orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )     
                else:
                    if estatus != "0":
                        orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False ) 
                    else:
                        orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False ) 
            
            #context["day_diff"]=date_difference(orders)
            ordenes=orders
            return ordenes                                    
        
        if emp.is_admin:              
         
            context["perfil"]="Admin"  
            
            locaList = employeeLocation.objects.filter(employeeID = emp)
                
            locationList = []
            locationList.append(emp.Location.LocationID)
            
            for i in locaList:
                locationList.append(i.LocationID.LocationID)
                    
            if emp.Location!= None:
                if estatus == "0" and loc == "0":                                         
                    if pid != None and pid != "-1":
                        orders = workOrder.objects.filter(prismID__exact = pid, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)    
                    elif addR != None and addR !="-1":
                        orders = workOrder.objects.filter(JobAddress__contains = addR, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False)   
                    elif invNumber !="-1" and invNumber != None:                
                        #Getting the OrderList by Invoice Number                        
                        woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                        woInvLits = []                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)
                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                        
                    elif  invAmount !="-1" and invAmount != None and invAmountF !="" and invAmountF != None:      
                        #Getting the OrderList by Invoice Number                        
                        woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False)                         
                    elif  invAmount !="-1" and invAmount != None:   
                        #Getting the OrderList by Invoice Number
                        
                        woInv = woInvoice.objects.filter(total = float(invAmount))
                        woInvLits = []
                        
                        for i in woInv:
                            woInvLits.append(i.woID.id)

                        orders = workOrder.objects.filter(id__in = woInvLits, Location__LocationID__in = locationList ).exclude(linkedOrder__isnull = False, uploaded = False) 
                    else:  
                        orders = workOrder.objects.filter(id = -1)   

                else:
                    if estatus != "0" and loc != "0":                          
                        orders = workOrder.objects.filter(Status = estatus, Location = loc).exclude(linkedOrder__isnull = False, uploaded = False )     
                    else:
                        if estatus != "0":                                                          
                            #If estatus is 1 get all the locations

                            LocationExclude = Locations.objects.all().exclude(LocationID__in = locationList )

                            if estatus == "1":
                                orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False , Location__in = LocationExclude ) 
                            else:
                                orders = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 

                        else:                             
                            orders = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False )                             
                            
            else:
                orders = workOrder.objects.filter(id = -1) 
            
            ordenes=orders
            return ordenes

            """if orders != None:
                context["day_diff"]=date_difference(orders)
            else:
                context["day_diff"] = None"""



    if request.user.is_staff:        
        if estatus == "0" and loc == "0":    
            
            if pid != None and pid != "-1":
                orders = workOrder.objects.filter(prismID__exact = pid).exclude(linkedOrder__isnull = False, uploaded = False)    
            elif addR != None and addR !="-1":
                orders = workOrder.objects.filter(JobAddress__contains = addR).exclude(linkedOrder__isnull = False, uploaded = False)   
            elif invNumber !="-1" and invNumber != None:
                
                #Getting the OrderList by Invoice Number
                
                woInv = woInvoice.objects.filter(invoiceNumber = invNumber)
                woInvLits = []
                
                for i in woInv:
                    woInvLits.append(i.woID.id)
                orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False) 
                
            elif  invAmount !="-1" and invAmount != None and invAmountF !="-1" and invAmountF != None:      
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__gte = float(invAmount), total__lte = float(invAmountF))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)  
            elif  invAmount !="-1" and invAmount != None:   
                    #Getting the OrderList by Invoice Number
                    
                    woInv = woInvoice.objects.filter(total__contains = float(invAmount))
                    woInvLits = []
                    
                    for i in woInv:
                        woInvLits.append(i.woID.id)

                    orders = workOrder.objects.filter(id__in = woInvLits ).exclude(linkedOrder__isnull = False, uploaded = False)     
                
            else:  
                #orders = workOrder.objects.filter(id = -1)   
                last_date = date(2025, 3, 3)
                orders = workOrder.objects.filter(created_date__gte = last_date).exclude(linkedOrder__isnull = False, uploaded = False)
        
        else:
            if estatus != "0" and loc != "0":
                orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  
            else:
                if estatus != "0":
                    orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )  
                else:
                    orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  
      

        #context["day_diff"]=date_difference(orders)
        ordenes=orders
        return ordenes
        

    
    if estatus == "0" and loc == "0":   
        orders = workOrder.objects.filter(WCSup__isnull=True).exclude(linkedOrder__isnull = False, uploaded = False )
    else:
        if estatus != "0" and loc != "0":
            orders = workOrder.objects.filter(WCSup__isnull=True, Location = locationObject, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
        else:
            if estatus != "0":
                orders = workOrder.objects.filter(WCSup__isnull=True, Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )
            else:
                orders = workOrder.objects.filter(WCSup__isnull=True, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )

    return orders

@login_required(login_url='/home/')
def get_order_list(request,estatus, loc,pid,addR,invNumber,invAmount,invAmountF,superV):
    

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Summary', cell_overwrite_ok = True) 

    # Sheet header, first row
    row_num = 7

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color light_blue;')

    font_style =  xlwt.XFStyle()       
    

    font_style_number = xlwt.XFStyle()
    font_style_number.num_format_str = '$ #,##0.00'          

       


    columns = ['prismID', 'work order ID', 'PO', 'PO Amount','Internal PO', 'Payroll', 'Subcontractor', 'Invoiced Amount', 'Pending Billing','Billing Amount', 'Total Expenses', 'Balance','% Balance','Status','Location','Supervisor','upload Date','Issued By','Job Name','Job Address', 'Comments']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
    

    if superV == "False":
        #Validate difference bwteen bySupervisor and the other Function --- 08/05/2024
        ordenes = get_list_orders(request, estatus, loc,pid,addR,invNumber,invAmount,invAmountF)          
    else:
        ordenes = get_list_orders_bySupervisor(request, estatus, loc,pid,addR,invNumber,invAmount,invAmountF)  

    for item in ordenes:
        row_num += 1
        ws.write(row_num, 0, item.prismID, font_style) # at 0 row 0 column 
        ws.write(row_num, 1, item.workOrderId, font_style) # at 0 row 0 column 
        ws.write(row_num, 2, item.PO, font_style_number) # at 0 row 0 column 
        ws.write(row_num, 3, item.POAmount, font_style_number) # at 0 row 0 column 

        dailys = Daily.objects.filter(woID = item)
        dailyDetail = []

        #Calculate Payroll
        empTotal = 0
        for itemd in dailys:
            dailyEmp = DailyEmployee.objects.filter(DailyID = itemd)

            for empI in dailyEmp:
                empTotal += validate_decimals(empI.payout)                

        #woo = workOrder.objects.filter(id = item.id)
        
        #Daily Item Production
        dailyItem = DailyItem.objects.filter(DailyID__woID = item)
        dailyItemTotal = 0
        for di in dailyItem:
            dailyItemTotal += validate_decimals(di.price) * validate_decimals(di.quantity)

        #External Production
        extProduction = externalProduction.objects.filter(woID = item)
        epTotal = 0 
        for ep in extProduction:
            epTotal += validate_decimals(ep.total_invoice)

        #Internal PO
        internalpo = internalPO.objects.filter(woID=item, nonBillable=False)
        poTotal = 0
        for po in internalpo:
            if po.total:
                if po.isAmountRounded:
                    poTotal += int(round(float(str(po.total))))
                else:
                    poTotal += Decimal(str(po.total))
		
        poTotal = validate_decimals(poTotal)

        balance = validate_decimals(item.POAmount) - validate_decimals(empTotal) - validate_decimals(poTotal) -  validate_decimals(epTotal)
        totalExp = validate_decimals(empTotal) + validate_decimals(poTotal) + validate_decimals(epTotal)
        if item.POAmount != None and validate_decimals(item.POAmount) > 0:
            balance_per = ((validate_decimals(totalExp)*100)/validate_decimals(item.POAmount))  
        else:
            balance_per = 0

        #ws.write(row_num, 4, f"$ {empTotal:.2f}", font_style)
        ws.write(row_num, 5, empTotal, font_style_number) #Payroll
        ws.write(row_num, 4, poTotal,  font_style_number) # Internal PO
        
        # Subcontractor = External Production Calculate
        subcontractor = 0
        subC = externalProduction.objects.filter(woID = item)
        for s in subC:
            subcontractor += validate_decimals(s.total_invoice)
        ws.write(row_num, 6, subcontractor,  font_style_number)
        
        ws.write(row_num, 10, totalExp,  font_style_number)
        
        #New Columns for Billing Amount, Pending Billing and Invoiced Amount
        # Calculte Invoiced Amount
        invoicedAmount = 0
        woInv = woInvoice.objects.filter(woID = item)
        for i in woInv:
            invoicedAmount += validate_decimals(i.total)
            
        #Calculate Billing Amount = Daily Producton Item + Internal PO + External Production
        billing_amount = 0    
        
        
        woCalculate = workOrder.objects.filter(id = item.id).first()
        production_invoiced, produnction_pending_billing = calculate_billing_amount(request, woCalculate)
        
        ##### Calculos
        prod_facturada = 0
        prod_facturada = get_invoiced_production_total_for_wo(woCalculate.id)
        prod_no_facturada = 0
        prod_no_facturada = get_uninvoiced_production_total_for_wo(woCalculate.id)
        
        
        # production_invoiced + produnction_pending_billing + (internalPO * 10%)
        billing_amount = validate_decimals(prod_no_facturada) + validate_decimals(prod_facturada)  
        
        # validate if it is necessary add this formula tor the cases that the order have no production but have internal PO and External Production, in that case the billing amount will be the sum of the internal PO with 10% and the external production, but if the order have production the billing amount will be the sum of the production invoiced, production pending billing and the internal PO with 10% and the external production, this formula is to avoid that some orders that have no production but have internal PO and External Production have a billing amount of 0 when they should have a billing amount different from 0 because of the internal PO and External Production.
        #billing_amount = validate_decimals(dailyItemTotal) + validate_decimals(poTotal) + validate_decimals(epTotal)
        
        
        #Calculate Pending Billing
        
        #pending_billing = validate_decimals(billing_amount) - validate_decimals(invoicedAmount)
    
        #Getting the Internal POs that not included in estimates and Invoices and are billables
        internalPOs = internalPO.objects.filter(woID=item, nonBillable=False, invoice__isnull = True, estimate__isnull = True)
        pending_POs = 0
        for i in internalPOs:
            pending_POs += validate_decimals(i.total) * validate_decimals('1.1') # assuming that the billing amount of the internal PO is the total with a 10% increase, this formula is to avoid that some internal POs that are not included in estimates and Invoices and are billables have a pending billing amount of 0 when they should have a pending billing amount different from 0 because of the internal PO
        
        pending_billing = 0
        pending_billing = validate_decimals(prod_no_facturada)
        
        invoicedAmount = validate_decimals(prod_facturada)
        
        
        ws.write(row_num, 9, billing_amount,  font_style_number)
        ws.write(row_num, 8, pending_billing,  font_style_number) #Pending Billing
        ws.write(row_num, 7, invoicedAmount,  font_style_number) # Invoiced Amount
        ws.write(row_num, 11, balance,  font_style_number)
        ws.write(row_num, 12, f"{balance_per:.2f}%",  font_style)        
        
        try:
            status_label = next((label for key, label in status_choice if str(key) == str(item.Status)), "")
        except Exception:
            status_label = ""
        
        ws.write(row_num, 13, status_label, font_style)

        
        if item.Location != None:
            ws.write(row_num, 14, item.Location.name, font_style) # at 0 row 0 column 
        else:
             ws.write(row_num, 14, '', font_style) 
        
        if item.WCSup != None:
            ws.write(row_num, 15, item.WCSup.first_name + ' ' + item.WCSup.last_name, font_style) # at 0 row 0 column 
        else:
            ws.write(row_num, 15, '', font_style) # at 0 row 0 column 

        try:            
            upload_date = parser.parse(item.UploadDate) if item.UploadDate else ''
            string_upload_date = datetime.strftime(upload_date, "%m/%d/%Y") if upload_date else ''
        except Exception:
            string_upload_date = item.UploadDate
        
        #aqui
        
        ws.write(row_num, 16, string_upload_date, font_style)  
        ws.write(row_num, 17, item.IssuedBy, font_style) 
        ws.write(row_num, 18, item.JobName, font_style) 
        ws.write(row_num, 19, item.JobAddress, font_style)      
        ws.write(row_num, 20, item.Comments, font_style)       

        
    
    ws.col(1).width = 3500
    ws.col(2).width = 3500
    ws.col(3).width = 3500
    ws.col(4).width = 3500
    ws.col(5).width = 4500
    ws.col(6).width = 4500
    ws.col(7).width = 5500
    ws.col(8).width = 5500
    ws.col(9).width = 5500
    ws.col(10).width = 3500
    ws.col(11).width = 3500
    ws.col(12).width = 5500
    ws.col(13).width = 5500
    ws.col(14).width = 5000
    ws.col(15).width = 4000
    ws.col(16).width = 9000
    ws.col(17).width = 11000
    ws.col(18).width = 15000
    ws.col(19).width = 20000
    ws.col(20).width = 20000

    filename = 'orders.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response
    

@login_required(login_url='/home/')
def get_summary(request, perID):
   
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()

    if request.user.is_staff:
        loca = Locations.objects.filter(is_active=True).order_by("LocationID")
    else:
        if emp:
            if emp.is_superAdmin:
                loca = Locations.objects.filter(is_active=True).order_by("LocationID")
            elif emp.Location != None:
                loca = Locations.objects.filter(LocationID = emp.Location.LocationID, is_active=True)
            else:
                loca = Locations.objects.filter(LocationID = -1)

    locList = []
    for empLoc in loca:
        locList.append(empLoc.LocationID)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Summary', cell_overwrite_ok = True) 

    # Sheet header, first row
    row_num = 7

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color light_blue;')

    font_style =  xlwt.XFStyle()                    


    columns = ['Location', 'Date', 'Eid', 'Name', 'RT','OT','DT','TT','RT$','OT$','Bonus', 'Production','own vehicle', 'on call', 'payroll','Supervisor','PID','Address']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 

    
    try:

        per = period.objects.filter(id = perID).first()
        dailyList = Daily.objects.filter(Period = per, Location__LocationID__in = locList).order_by('Location')

        for item in dailyList:        
        
            demp = DailyEmployee.objects.filter(DailyID=item).order_by()    
            empLines = 0    
            

            for i in demp:
                itemProd = 0
                rtPrice = 0
                otPrice = 0
                dtPrice = 0     
                ttp = 0
                ov = 0
                bonus = 0
                on_call = 0
                InvoiceGeneral = 0
                
            
                if validate_decimals(i.payout) > 0:                
                    row_num += 1
                    

                    ws.write(row_num,0,item.Location.name, font_style)
                    ws.write(row_num,1,item.day.strftime("%m/%d/%Y"), font_style)
                    ws.write(row_num,2,i.EmployeeID.employeeID, font_style)
                    ws.write(row_num,3,i.EmployeeID.last_name + ' ' +i.EmployeeID.first_name, font_style)

                    itemProd = DailyItem.objects.filter(DailyID = i.DailyID).count()
                    
                    if itemProd <= 0:                    
                
                        ws.write(row_num,4,validate_print_decimals(i.regular_hours), font_style)
                        ws.write(row_num,5,validate_print_decimals(i.ot_hour), font_style)
                        ws.write(row_num,6,validate_print_decimals(i.double_time), font_style)
                        ws.write(row_num,7,validate_print_decimals(i.total_hours), font_style)

                        if validate_decimals(i.EmployeeID.hourly_rate) != None:
                            rtPrice = (validate_decimals(i.regular_hours) * float(validate_decimals(i.EmployeeID.hourly_rate)))
                            otPrice = ((validate_decimals(i.ot_hour) * (float(validate_decimals(i.EmployeeID.hourly_rate))*1.5)))
                            dtPrice = ((validate_decimals(i.double_time) * (float(validate_decimals(i.EmployeeID.hourly_rate))*2)))

                            ws.write(row_num,8,validate_print_decimals(rtPrice), font_style)
                            ws.write(row_num,9,validate_print_decimals(otPrice + dtPrice), font_style)
                        else:
                            ws.write(row_num,8,'', font_style)
                            ws.write(row_num,9,'', font_style)
                    else:
                        ws.write(row_num,4,'', font_style)
                        ws.write(row_num,5,'', font_style)
                        ws.write(row_num,6,'', font_style)
                        ws.write(row_num,7,'', font_style)
                        ws.write(row_num,8,'', font_style)
                        ws.write(row_num,9,'', font_style)

                    ws.write(row_num,10,validate_print_decimals(i.bonus), font_style)
                    if itemProd > 0:  
                        di = DailyItem.objects.filter(DailyID = i.DailyID)          
                        t = 0
                        for j in di:
                            t += validate_decimals(j.total)

                        #if validate_decimals(item.own_vehicle) != None:
                        #    ov = validate_decimals((((t * validate_decimals(item.own_vehicle)) / 100) * validate_decimals(i.per_to_pay)) /100)
                        #else:
                        #    ov = 0

                        
                        #Nuevo Calculo Own Vehicle
                        if i.is_own_vehicle:
                            ov = validate_decimals(i.own_vehicle_pay)    
                        else:
                            ov = 0
                        

                        ttp = (t * validate_decimals(i.per_to_pay)) /100
                        ws.write(row_num,round(11,2),validate_print_decimals(ttp), font_style)
                        ws.write(row_num,12,validate_print_decimals(ov), font_style)
                    else:
                        ws.write(row_num,11,'', font_style)
                        ws.write(row_num,12,'', font_style)

                    if validate_decimals(i.bonus) != None:
                        bonus = validate_decimals(i.bonus)
                    
                    if validate_decimals(i.on_call) != None:
                        on_call = validate_decimals(i.on_call)


                    payTotal = validate_decimals(i.payout) #validate_decimals(rtPrice + otPrice + dtPrice + bonus + ttp + ov + on_call)
                    ws.write(row_num,13,validate_print_decimals(i.on_call), font_style)
                    ws.write(row_num,14,validate_print_decimals(payTotal), font_style)
                    if item.woID.WCSup != None:
                        ws.write(row_num,15,item.woID.WCSup.last_name + ' ' + item.woID.WCSup.first_name, font_style)
                    ws.write(row_num,16,item.woID.prismID, font_style)
                    ws.write(row_num,17,item.woID.JobAddress, font_style)

                    empLines += 1
                    
                    # se agregan las columnas de items
                    if empLines == 1:
                        items = DailyItem.objects.filter(DailyID = i.DailyID)
                        col_item =  0
                        itemNumber = 0

                        for z in items:                            
                            col_item += 1
                            itemNumber += 1
                            try:
                                ws.write(7,17 + col_item,'Item'+str(itemNumber), font_title)   
                                ws.write(7,18 + col_item,'Qty'+str(itemNumber), font_title)                                                         
                            except Exception as e:
                                None                            
                            
                            ws.write(row_num,17 + col_item,z.itemID.item.itemID, font_style)
                        
                            col_item += 1                                          
                            
                            ws.write(row_num,17 + col_item,z.quantity, font_style)                            
                           

    
        
        sumItem = 0            
        for x in dailyList:
            items = DailyItem.objects.filter(DailyID = x).count()                           

            if items > sumItem:
                sumItem = items            
       
        ws.write(7,18 + sumItem*2,'Item Totals', font_title)   
        ws.write(7,19 + sumItem*2,'Invoice', font_title)                   
        

        row_num=7
        
        for x in dailyList:
            demp = DailyEmployee.objects.filter(DailyID=x).order_by()    
            empLines = 0    

            for y in demp:
                empLines += 1
            
                if validate_decimals(y.payout) > 0:                
                    row_num += 1
                    if empLines == 1:
                        items = DailyItem.objects.filter(DailyID = x)
                        sumQty = 0
                        sumInvoice = 0
                        for z in items:
                            if validate_decimals(z.price) != None:
                                lineInv = validate_decimals(z.quantity) * validate_decimals(z.price)
                            else:
                                lineInv = 0
                            sumInvoice += validate_decimals(lineInv)
                            sumQty += validate_decimals(z.quantity)

                        if sumQty > 0:
                            InvoiceGeneral += validate_decimals(sumInvoice)
                            ws.write(row_num,18 + sumItem*2,validate_decimals(sumQty), font_style)   
                            ws.write(row_num,19 + sumItem*2,validate_decimals(sumInvoice), font_style)     
        

        ws.col(0).width = 3000
        ws.col(2).width = 1500
        ws.col(3).width = 5000
        ws.col(4).width = 1000
        ws.col(5).width = 1000
        ws.col(6).width = 1000
        ws.col(7).width = 1000
        ws.col(8).width = 1000
        ws.col(9).width = 1000
        ws.col(10).width = 1700                                      
        ws.col(11).width = 3500
        ws.col(12).width = 3000
        ws.col(13).width = 1700
        ws.col(14).width = 2200
        ws.col(15).width = 5000
        ws.col(17).width = 11500
        
    except Exception as e:
        ws.write(0,0,str(e), font_style)    

    
    try:
        # WORKSHEET UPLOAD

        ws2 = wb.add_sheet('UPLOAD', cell_overwrite_ok = True) 

        # Sheet header, first row
        row_num = 7
       

        columns = ['Loc Id', 'Assigned Department', 'Eid', 'Name', 'RT','OT','DT','TT','RT$','OT$','Bonus', 'Production','own vehicle', 'on call', 'payroll']

        for col_num in range(len(columns)):
            ws2.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
          


        empList = Employee.objects.all()   
        per = period.objects.filter(id = perID).first()
        invoice = 0
        payTotalTotal = 0
        for item in empList:
            dailyEmp = DailyEmployee.objects.filter(EmployeeID = item, DailyID__Period = perID, DailyID__Location__LocationID__in = locList).count()

            if dailyEmp > 0:           
                emp = Employee.objects.filter(employeeID = item.employeeID).first()            

                dailyemp = DailyEmployee.objects.filter(EmployeeID = emp, DailyID__Period = per)

                contador = 0
                rtTotal = 0
                otTotal = 0
                dtTotal = 0
                rt_Total = 0
                ot_Total = 0
                dt_Total = 0
                tt_Total = 0
                ocTotal = 0
                bonTotal = 0
                prodTotal = 0
                ovTotal = 0
                payTotal = 0
                
                line2 = False 

                for itemEmp in dailyemp:                
                    contador += 1
                    rt = 0
                    ot = 0
                    dt = 0
                    on_call = 0
                    bonus = 0                    
                    

                    prod = DailyItem.objects.filter(DailyID = itemEmp.DailyID).count()

                    if prod <= 0:           
                        if validate_decimals(itemEmp.EmployeeID.hourly_rate) != None:
                            rt = (validate_decimals(itemEmp.regular_hours) * float(validate_decimals(itemEmp.EmployeeID.hourly_rate)))
                            ot = ((validate_decimals(itemEmp.ot_hour) * (float(validate_decimals(itemEmp.EmployeeID.hourly_rate))*1.5)))
                            dt = ((validate_decimals(itemEmp.double_time) * (float(validate_decimals(itemEmp.EmployeeID.hourly_rate))*2)))
                        rt_Total += validate_decimals(itemEmp.regular_hours)
                        ot_Total += validate_decimals(itemEmp.ot_hour)
                        dt_Total += validate_decimals(itemEmp.double_time)
                        tt_Total += validate_decimals(itemEmp.total_hours)

                    payroll = validate_decimals(itemEmp.payout)
                    on_call = validate_decimals(itemEmp.on_call)
                    bonus = validate_decimals(itemEmp.bonus)

                    itemd = DailyItem.objects.filter(DailyID = itemEmp.DailyID)

                    total = 0
                    for i in itemd:
                        if validate_decimals(i.itemID.price) != None:
                            invoice += validate_decimals(((validate_decimals(i.quantity) * float(validate_decimals(i.itemID.price))) * validate_decimals(itemEmp.per_to_pay)) / 100)                   
                            
                        total += validate_decimals(i.total)

                    production = validate_decimals((validate_decimals(total) * validate_decimals(itemEmp.per_to_pay)) / 100)


                    #if validate_decimals(itemEmp.DailyID.own_vehicle) != None:
                    #    own_vehicle = validate_decimals((((validate_decimals(total) * validate_decimals(itemEmp.DailyID.own_vehicle)) / 100) * validate_decimals(itemEmp.per_to_pay)) / 100)
                    #else:
                    #    own_vehicle = 0

                    own_vehicle = validate_decimals(itemEmp.own_vehicle_pay)

                    
                   
                    rtTotal += rt
                    otTotal += ot
                    dtTotal += dt               

                    if validate_decimals(on_call) != None:
                        ocTotal += validate_decimals(on_call)

                    if validate_decimals(bonus) != None:
                        bonTotal += validate_decimals(bonus)

                    prodTotal += validate_decimals(production)
                    ovTotal += validate_decimals(own_vehicle)
                    payTotal += validate_decimals(payroll)
                
                payTotalTotal += validate_decimals(payTotal)

                row_num += 1
                if emp.Location != None:
                    ws2.write(row_num, 0, emp.Location.LocationID, font_style)
                    ws2.write(row_num, 1, emp.Location.name, font_style)
                
                ws2.write(row_num, 2, emp.employeeID, font_style)
                ws2.write(row_num, 3, emp.last_name + ' ' + emp.first_name, font_style)
                ws2.write(row_num, 4, validate_print_decimals(rt_Total), font_style)
                ws2.write(row_num, 5, validate_print_decimals(ot_Total), font_style)
                ws2.write(row_num, 6, validate_print_decimals(dt_Total), font_style)
                ws2.write(row_num, 7, validate_print_decimals(tt_Total), font_style)
                ws2.write(row_num, 8, validate_print_decimals(rtTotal), font_style)
                ws2.write(row_num, 9, validate_print_decimals(otTotal + dtTotal), font_style)
                ws2.write(row_num, 10,validate_print_decimals(bonTotal), font_style)
                ws2.write(row_num, 11,validate_print_decimals(prodTotal), font_style)
                ws2.write(row_num, 12,validate_print_decimals(ovTotal), font_style)
                ws2.write(row_num, 13,validate_print_decimals(ocTotal), font_style)
                ws2.write(row_num, 14,validate_print_decimals(payTotal), font_style)


                ws2.write(2, 13,'Invoice', font_style)
                ws2.write(2, 14,validate_decimals(InvoiceGeneral), font_style)
                ws2.write(3, 13,'% pay', font_style)   
                if validate_decimals(payTotalTotal) > 0 and validate_decimals(InvoiceGeneral) > 0:
                    ws2.write(3, 14,validate_decimals((validate_decimals(payTotalTotal)*100) / validate_decimals(InvoiceGeneral)), font_style)
                else:
                    ws2.write(3, 14,0, font_style)


    except Exception as e:       
        ws2.write(0,0,str(e), font_style) 
    
    
    try:
        # WORKSHEET BALANCE

        ws3 = wb.add_sheet('Balance', cell_overwrite_ok = True) 

        # Sheet header, first row
        row_num = 12

        font_title2 = xlwt.easyxf('font: bold on, color black;\
                                align: horiz center')
        
        ws3.write_merge(3, 3, 0, 14, 'Payroll Production Balance', font_title2)

        font_title3 = xlwt.easyxf('font: bold on, color black;\
                        borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;\
                        align: horiz left')

        ws3.write_merge(5, 5, 3, 4, 'Invoice', font_title3)
        ws3.write_merge(6, 6, 3, 4, 'Payroll', font_title3)
        ws3.write_merge(7, 7, 3, 4, 'Balance', font_title3)
        ws3.write_merge(8, 8, 3, 4, '% Paid', font_title3)

        ws3.write_merge(5, 5, 8, 9, 'Weeks', font_title3)
        ws3.write_merge(6, 6, 8, 9, 'From', font_title3)
        ws3.write_merge(7, 7, 8, 9, 'To', font_title3)
        ws3.write_merge(8, 8, 8, 9, 'Pay date', font_title3)
       

        ws3.write_merge(5, 5, 10, 11, per.weekRange, font_title3)
        ws3.write_merge(6, 6, 10, 11, per.fromDate.strftime("%m/%d/%Y"), font_title3)
        ws3.write_merge(7, 7, 10, 11, per.toDate.strftime("%m/%d/%Y"), font_title3)
        ws3.write_merge(8, 8, 10, 11, per.payDate.strftime("%m/%d/%Y"), font_title3)   

       
        ws3.write_merge(5, 5, 5, 6, '$' + '{0:,.2f}'.format(validate_decimals(InvoiceGeneral)), font_title3)
        ws3.write_merge(6, 6, 5, 6, '$' + '{0:,.2f}'.format(validate_decimals(payTotalTotal)), font_title3)
        ws3.write_merge(7, 7, 5, 6, '$' + '{0:,.2f}'.format(validate_decimals(InvoiceGeneral) - validate_decimals(payTotalTotal)), font_title3)
        
       
        if validate_decimals(payTotalTotal) > 0 and validate_decimals(invoice) > 0:
            ws3.write_merge(8, 8, 5, 6, str(round((validate_decimals(payTotalTotal)*100) / validate_decimals(InvoiceGeneral),2)) + '%', font_title3)  
        else:    
            ws3.write_merge(8, 8, 5, 6, '0%', font_title3)            

        

        columns = ['Loc Id', 'Location', 'Regular Time','Over Time','Double Time','Total Time','RT$','OT$','Bonus', 'Production','own vehicle', 'on call', 'payroll', 'Invoice', '% Pay']

        for col_num in range(len(columns)):
            ws3.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column        


        loca = Locations.objects.filter(LocationID__in = locList).order_by("LocationID")    

        for locItem in loca:
            row_num += 1
            daily = Daily.objects.filter(Location = locItem, Period = per)     
            regular_time = 0
            over_time = 0
            double_time = 0
            total_time = 0
            rt = 0
            ot = 0
            dt = 0
            bonus = 0
            on_call = 0
            prod = 0
            gran_total = 0
            payroll = 0
            ownvehicle = 0
            invoice = 0
            payroll2= 0
            perc = 0
            for dailyItem in daily:            
                production = DailyItem.objects.filter(DailyID=dailyItem).count()

                dailyemp = DailyEmployee.objects.filter(DailyID=dailyItem)

                for i in dailyemp:
                    if production <= 0:
                        regular_time += validate_decimals(i.regular_hours)
                        over_time += validate_decimals(i.ot_hour)
                        double_time += validate_decimals(i.double_time)
                        total_time += validate_decimals(i.total_hours)
                        if validate_decimals(i.EmployeeID.hourly_rate) != None:
                            rt += (validate_decimals(i.regular_hours) * float(validate_decimals(i.EmployeeID.hourly_rate)))
                            ot += ((validate_decimals(i.ot_hour) * (float(validate_decimals(i.EmployeeID.hourly_rate))*1.5)))
                            dt += ((validate_decimals(i.double_time) * (float(validate_decimals(i.EmployeeID.hourly_rate))*2)))

                    if validate_decimals(i.bonus) != None:
                        bonus += validate_decimals(i.bonus)
                        
                    if validate_decimals(i.on_call) != None:
                        on_call += validate_decimals(i.on_call)

                    if validate_decimals(i.payout) != None:
                        payroll += validate_decimals(i.payout)

                    if validate_decimals(i.is_own_vehicle) != None:
                        ov = i.own_vehicle_pay
                        ownvehicle += validate_decimals(ov)

                
                dailyprod =  DailyItem.objects.filter(DailyID=dailyItem)
                total = 0
                
                ov = 0
                for j in dailyprod:                
                    total += validate_decimals(j.total)
                    if validate_decimals(j.itemID.price) != None:
                        invoice += (validate_decimals(j.quantity) * float(validate_decimals(j.itemID.price)) )
                    if validate_decimals(j.itemID.emp_payout) != None:    
                        payroll2 += (validate_decimals(j.quantity) * float(validate_decimals(j.itemID.emp_payout)) )

                dailyempleado = DailyEmployee.objects.filter(DailyID=dailyItem)
                ptpEmp = 0
                for h in dailyempleado:
                    ptpEmp += validate_decimals(h.per_to_pay)

                total = validate_decimals((total * ptpEmp) / 100)

                #if validate_decimals(dailyItem.own_vehicle) != None:
                #    ov = validate_decimals(((validate_decimals(total) * validate_decimals(dailyItem.own_vehicle)) / 100))
                #    ownvehicle += validate_decimals(ov)

                prod += validate_decimals(total)

            if validate_decimals(invoice) > 0:                    
                perc = validate_decimals((validate_decimals(payroll) * 100) / validate_decimals(invoice))

            

            ws3.write(row_num, 0, locItem.LocationID, font_style) 
            ws3.write(row_num, 1, locItem.name, font_style) 
            ws3.write(row_num, 2, validate_print_decimals(regular_time), font_style)
            ws3.write(row_num, 3, validate_print_decimals(over_time), font_style)
            ws3.write(row_num, 4, validate_print_decimals(double_time), font_style)        
            ws3.write(row_num, 5, validate_print_decimals(total_time), font_style)
            ws3.write(row_num, 6, validate_print_decimals(rt), font_style)
            ws3.write(row_num, 7, validate_print_decimals(ot + dt), font_style)        
            ws3.write(row_num, 8, validate_print_decimals(bonus), font_style)
            ws3.write(row_num, 9, validate_print_decimals(prod), font_style)
            ws3.write(row_num, 10, validate_print_decimals(ownvehicle), font_style)
            ws3.write(row_num, 11, validate_print_decimals(on_call), font_style)
            ws3.write(row_num, 12, validate_print_decimals(payroll), font_style)
            ws3.write(row_num, 13, validate_print_decimals(invoice), font_style)
            ws3.write(row_num, 14, validate_print_decimals(perc), font_style) 
    except Exception as e:
        ws3.write(0,0,str(e), font_style)              

    
    filename = 'Payroll Summary ' + str(per.weekRange) + '.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response

@login_required(login_url='/home/')
def update_sup_daily(request, id, woid):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    dailyID = Daily.objects.filter(id = id).first()

    order = workOrder.objects.filter(id = woid).first()

    form = dailySupForm(request.POST or None, initial={'woID': order})
    if form.is_valid():                
        form.save()  
        
        return HttpResponseRedirect('/payroll/' + str(dailyID.Period.id) + '/' + dailyID.day.strftime("%d") + '/' + str(dailyID.crew) +'/0')        
         
    context['form']= form
    context["emp"] = emp
    context["order"] = order
    context["daily"] = dailyID
    return render(request, "update_sup_daily.html", context)

@login_required(login_url='/home/')
def delete_daily(request, id, LocID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    obj = get_object_or_404(Daily, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        actual_wo = obj.woID
        comments = request.POST.get('comments')
        
        #Adding Audit
        
        #Getting all the Payroll operations before to delete
       
        dAudit = DailyAudit.objects.filter(DailyID = obj.id)
        opDetail = comments
        for i in dAudit:
            opDetail += "Crew: " + str(obj.crew) + ", Date: " + str(i.created_date) + ", User: " + i.createdBy + ", Operation: " + i.operationType + ", Detail: " + i.operationDetail + "\n" 
        
        
        pAudit = payrollAudit(
                                Location = obj.Location,
                                Period = obj.Period,
                                day = obj.day,
                                operationDetail = opDetail,
                                operationType = "Delete",
                                created_date = datetime.now(),
                                createdBy =  request.user.username
                            )
        
        pAudit.save()           
        
        #Update Mobile Daily to status Deleted
        if  obj.mobile_id is not None:
            mcrew = MobileModel.DailyMob.objects.filter(id = obj.mobile_id).first()

            if mcrew:
                mcrew.Status = 6
                mcrew.deleted_date = datetime.now()
                mcrew.deleted_by = request.user.username
                mcrew.comments = comments
                mcrew.save()

        obj.delete()

        if actual_wo != None:
            lastD = Daily.objects.filter(woID = actual_wo).last()
            wo = workOrder.objects.filter(id = actual_wo.id).first()
            
            if lastD:                 
                wo.UploadDate = lastD.created_date

                if lastD.supervisor != None:
                    sup = Employee.objects.filter(employeeID = lastD.supervisor ).first()
                    if sup:                
                        wo.WCSup = sup

                wo.save()
            else:
                log = woStatusLog( 
                            woID = wo,
                            currentStatus = wo.Status,
                            nextStatus = 1,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
                log.save()

                wo.Status = 1
                wo.Location = None
                wo.UploadDate = None
                wo.UserName = None
                wo.WCSup = None
                wo.UploadDate = datetime.now()
                wo.save()

        
        return HttpResponseRedirect('/payroll/' + str(obj.Period.id) + '/' + obj.day.strftime("%d") + '/0/' + str(LocID)) 

   
    return render(request, "delete_daily.html", context)


@login_required(login_url='/home/')
def status_log(request, id,isSupervisor):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = id).first()

    wo_log = woStatusLog.objects.filter(woID = wo).order_by('created_date')
    context["log"] = wo_log
    context["id"] = wo.id
    context["isSupervisor"]=isSupervisor
    
    return render(request, "order_status_log.html", context)

@login_required(login_url='/home/')
def payroll_audit(request, id):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = Daily.objects.filter(id = id).first()

    wo_log = DailyAudit.objects.filter(DailyID = wo).order_by('created_date')
    context["log"] = wo_log
    context["id"] = wo.id
    
    return render(request, "payroll_audit.html", context)

@login_required(login_url='/home/')
def login_audit(request):
  
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    operationTypes = logInAudit.objects.values_list('operationType', flat=True).distinct().order_by('operationType')
    context["operationTypes"] = operationTypes

    createdByList = logInAudit.objects.values_list('createdBy', flat=True).distinct().order_by('createdBy')
    context["createdByList"] = createdByList

    wo_log = logInAudit.objects.none()
    applied = False

    if request.method == "POST":
        applied = True
        filters = {}
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        operationType = request.POST.get('operationType')
        createdBy = request.POST.get('createdBy')
        is_staff = request.POST.get('is_staff')
        is_supervisor = request.POST.get('is_supervisor')
        is_admin = request.POST.get('is_admin')
        is_superAdmin = request.POST.get('is_superAdmin')

        if date_from:
            filters['created_date__gte'] = parser.parse(date_from)
        if date_to:
            filters['created_date__lt'] = parser.parse(date_to) + timedelta(days=1)
        if operationType:
            filters['operationType'] = operationType
        if createdBy:
            filters['createdBy'] = createdBy
        if is_staff:
            filters['is_staff'] = True
        if is_supervisor:
            filters['is_supervisor'] = True
        if is_admin:
            filters['is_admin'] = True
        if is_superAdmin:
            filters['is_superAdmin'] = True

        if not filters:
            context["filter_error"] = "Select at least one filter to search."
            applied = False
        else:
            wo_log = logInAudit.objects.filter(**filters).order_by('-created_date')

        context["date_from"] = date_from
        context["date_to"] = date_to
        context["selectOperationType"] = operationType
        context["selectCreatedBy"] = createdBy
        context["select_is_staff"] = is_staff
        context["select_is_supervisor"] = is_supervisor
        context["select_is_admin"] = is_admin
        context["select_is_superAdmin"] = is_superAdmin

    context["log"] = wo_log
    context["applied"] = applied

    return render(request, "login_audit.html", context)

@login_required(login_url='/home/')
def payroll_audit_delete(request, perID, LocID, dID):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    #wo = Daily.objects.filter(id = id).first()


    selPeriod = period.objects.filter(id = perID).first()
    selLoc = Locations.objects.filter(LocationID = LocID).first()

    wo_log = payrollAudit.objects.filter(Period = selPeriod, Location = selLoc).order_by('created_date')
    context["log"] = wo_log
    #context["id"] = wo.id
    
    return render(request, "payroll_audit.html", context)


@login_required(login_url='/home/')
def supervisor_appoval(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(period, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        obj.status = 2
        obj.approvedBy = request.user.username
        obj.approved_date = datetime.now()
        obj.save()        

        return HttpResponseRedirect('/location_period_list/' + str(id)) 

   
    return render(request, "sup_approval.html", context)

@login_required(login_url='/home/')
def close_payroll(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status=2).first()
    context["per"] = per

    obj = get_object_or_404(period, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        obj.status = 3
        obj.closedBy = request.user.username
        obj.closed_date = datetime.now()
        obj.save()    
        
        
        #Validate if the next period exist, if not create it                
        next_period = period.objects.filter(id__gt = id, status__in = (1,2)).count()
        
        if next_period == 0:
            create_period(request, id)
        
        return HttpResponseRedirect('/period_list/') 

   
    return render(request, "close_payroll.html", context)


@login_required
def open_period(request,id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status=2).first()
    context["per"] = per
    
    actual_period = get_object_or_404(period, id = id)
    
    #Changing the period Status to Open
    actual_period.status = 1
    actual_period.save()
    
    return HttpResponseRedirect('/location_period_list/' + str(id))
    
    
    

@login_required(login_url='/home/')
def payroll_detail(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in = (1,2)).first()
    context["per"] = per

    obj = get_object_or_404(workOrder, id = id)

    dailys = Daily.objects.filter(woID = obj)
    dailyDetail = []
    
    #Payroll Detail
    empTotal = 0
    for item in dailys:
        dailyEmp = DailyEmployee.objects.filter(DailyID = item)

        for empI in dailyEmp:
            empTotal += validate_decimals(empI.payout)
            dailyDetail.append({'empID': empI.EmployeeID.employeeID, 'empName':empI.EmployeeID, 'payout': empI.payout, 'day':empI.DailyID.day, 'period': empI.DailyID.Period.weekRange, 'pdf': item.pdfDaily } )

    #External Production
    extProduction = externalProduction.objects.filter(woID = obj)
    epTotal = 0 
    for ep in extProduction:
        epTotal += validate_decimals(ep.total_invoice)

    #Production Transfer to 
    prodTransferTo = authorizedBilling.objects.filter(transferFrom = obj)
    pttTotal = 0
    for ptt in prodTransferTo:
        pr = validate_decimals(ptt.transferQty)  * validate_decimals(ptt.itemID.price)
        pttTotal += pr

    #Production Transfer From
    prodTransferFrom = authorizedBilling.objects.filter(woID = obj, transferFrom__isnull = False)
    ptfTotal = 0
    for ptf in prodTransferFrom:
        pr = validate_decimals(ptf.transferQty)  * validate_decimals(ptf.itemID.price)
        ptfTotal += pr


    #Internal PO Detail
    internalpo = internalPO.objects.filter(woID=obj)
    poTotal = 0
    for po in internalpo:
        poTotal += validate_decimals(po.total)

    balance = validate_decimals(obj.POAmount) - validate_decimals(empTotal) - validate_decimals(poTotal)- validate_decimals(epTotal)
    totalExp = validate_decimals(empTotal) + validate_decimals(poTotal) + validate_decimals(epTotal)
    if validate_decimals(obj.POAmount) > 0:
        balance_per = ((validate_decimals(totalExp)*100)/validate_decimals(obj.POAmount))
    else:    
        balance_per = 0

    context["payroll"] = dailyDetail
    context["payrollTotal"] = empTotal
    context["poTotal"] = poTotal
    context["epTotal"] = epTotal
    context["totalExp"] = totalExp
    context["balance"] = balance
    context["balance_per"] = balance_per
    context["order"] = obj
    context["po"] = internalpo
    context["extProduction"] = extProduction
    context["emp"] = emp


    context["prodTransferTo"] = prodTransferTo
    context["pttTotal"] = pttTotal

    context["prodTransferFrom"] = prodTransferFrom
    context["ptfTotal"] = ptfTotal

    vendorList = vendorSubcontrator(request) 
    context["vendorList"] = vendorList
 
    return render(request, "payroll_detail.html", context)

@login_required(login_url='/home/')
def get_emp_list(request):
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Employees', cell_overwrite_ok = True) 

        # Sheet header, first row
        row_num = 7

        font_title = xlwt.XFStyle()
        font_title.font.bold = True
        font_title = xlwt.easyxf('font: bold on, color black;\
                        borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;\
                        pattern: pattern solid, fore_color light_blue;')

        font_style =  xlwt.XFStyle()              

        


        columns = ['EID', 'First Name', 'Last Name', 'middle_initial', 'supervisor_name','termination_date','hire_created','hourly_rate','email','Location','user','Is Active', 'Is Supervisor', 'Is Admin']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
        

        empl = Employee.objects.all().order_by('employeeID')   
        for item in empl:
            row_num += 1
            ws.write(row_num, 0, item.employeeID, font_style) # at 0 row 0 column 
            ws.write(row_num, 1, item.first_name, font_style) # at 0 row 0 column 
            ws.write(row_num, 2, item.last_name, font_style) # at 0 row 0 column 
            ws.write(row_num, 3, item.middle_initial, font_style) # at 0 row 0 column 
            
            if  item.supervisor_name != None:
                ws.write(row_num, 4, item.supervisor_name.first_name + ' ' + item.supervisor_name.last_name, font_style) # at 0 row 0 column 
            
            ws.write(row_num, 5, item.termination_date, font_style) # at 0 row 0 column 
            ws.write(row_num, 6, item.hire_created, font_style) # at 0 row 0 column 
            ws.write(row_num, 7, item.hourly_rate, font_style) # at 0 row 0 column 
            ws.write(row_num, 8, item.email, font_style) # at 0 row 0 column 
            if item.Location != None:
                ws.write(row_num, 9, item.Location.name, font_style) # at 0 row 0 column 
            
            if item.user != None:
                ws.write(row_num, 10, item.user.username, font_style) # at 0 row 0 column 

            if item.is_active:
                ws.write(row_num, 11, True, font_style) # at 0 row 0 column 
            else:
                ws.write(row_num, 11, False, font_style) # at 0 row 0 column 
            
            if item.is_supervisor:
                ws.write(row_num, 12, True, font_style) # at 0 row 0 column 
            else:
                ws.write(row_num, 12, False, font_style) # at 0 row 0 column 

            if item.is_admin:
                ws.write(row_num, 13, True, font_style) # at 0 row 0 column 
            else:
                ws.write(row_num, 13, False, font_style) # at 0 row 0 column 
            
            
    except Exception as e:
        ws.write(0,0,str(e), font_style)    

    ws.col(5).width = 3500
    ws.col(6).width = 5000
    ws.col(7).width = 4000
    ws.col(8).width = 9000
    ws.col(9).width = 9000
    ws.col(10).width = 9000

    filename = 'employees.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response

@login_required(login_url='/home/')
def get_item_list(request):

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Items', cell_overwrite_ok = True) 

    # Sheet header, first row
    row_num = 7

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color light_blue;')

    font_style =  xlwt.XFStyle()              

       


    columns = ['itemID', 'Name', 'Description', 'Location', 'pay_perc','price','emp_payout','rate']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
    

    iteml = item.objects.all()   
    for i in iteml:
        

        itemP = itemPrice.objects.filter(item=i)

        for ip in itemP:
            row_num += 1
            ws.write(row_num, 0, i.itemID, font_style) # at 0 row 0 column 
            ws.write(row_num, 1, i.name, font_style) # at 0 row 0 column 
            ws.write(row_num, 2, i.description, font_style)
            ws.write(row_num, 3, ip.location.name, font_style)
            ws.write(row_num, 4, ip.pay_perc, font_style)
            ws.write(row_num, 5, ip.price, font_style)
            ws.write(row_num, 6, ip.emp_payout, font_style)
            ws.write(row_num, 7, ip.rate, font_style)
                        

    ws.col(0).width = 3500
    ws.col(1).width = 7000
    ws.col(2).width = 7000
    ws.col(3).width = 5000
    ws.col(4).width = 4000
    ws.col(5).width = 4000
    ws.col(6).width = 4000
    ws.col(7).width = 4000

    filename = 'Items.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response


def validate_decimals(value):
    try:
        return round(float(str(value)), 2)
    except:
       return 0


def validate_print_decimals(value): 
    try:
        if round(float(value), 2) > 0:                
            return round(float(value), 2)
        else:
            return ''
    except:
       return ''      

@login_required(login_url='/home/')
def vendor_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    context["vendor"] = vendor.objects.all()
    context["emp"]= emp


    opType = "Access Option"
    opDetail = "Vendor List"
    logInAuditLog(request, opType, opDetail)



    return render(request, "vendor_list.html", context)

@login_required(login_url='/home/')
def create_vendor(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    form = vendorForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/vendor_list/")
         
    context['form']= form
    context["emp"]=emp
    return render(request, "create_vendor.html", context)

@login_required(login_url='/home/')
def create_vendor_modal(request, woID, tipoOP, poID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["selectedWO"]=woID
    context["tipoOP"]=tipoOP
    context["poID"]=poID
 
    form = vendorForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()  


        if tipoOP == "0":             
            return HttpResponseRedirect("/create_po/" + str(woID) + '/0')
        else:
            return HttpResponseRedirect("/update_po/" + str(poID) + '/' + str(woID) + '/V' + str(form.instance.id))
         
    context['form']= form
    context["emp"]=emp

    
    return render(request, "create_vendor_modal.html", context)
    

@login_required(login_url='/home/')
def update_vendor(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(vendor, id = id)
 
    form = vendorForm(request.POST or None, instance = obj)
 
    if form.is_valid():
        form.save()
        return HttpResponseRedirect("/vendor_list/")

    context["form"] = form
    context["emp"] = emp
    return render(request, "create_vendor.html", context)

@login_required(login_url='/home/')
def subcontractor_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    context["subcontractor"] = subcontractor.objects.all()
    context["emp"]= emp



    opType = "Access Option"
    opDetail = "Subcontractor List"
    logInAuditLog(request, opType, opDetail)


    return render(request, "subcontractor_list.html", context)

@login_required(login_url='/home/')
def create_subcontractor(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    form = subcontractorForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/subcontractor_list/")
         
    context['form']= form
    context["emp"]=emp
    return render(request, "create_subcontractor.html", context)

@login_required(login_url='/home/')
def create_subcontractor_modal(request, woID, tipoOP, poID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["selectedWO"]=woID
    context["tipoOP"]=tipoOP
    context["poID"]=poID

    form = subcontractorForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()             

        if tipoOP == "0":             
            return HttpResponseRedirect("/create_po/" + str(woID) + '/0')
        else:
            return HttpResponseRedirect("/update_po/" + str(poID) + '/' + str(woID) + '/S' + str(form.instance.id))
         
    context['form']= form
    context["emp"]=emp
    return render(request, "create_subcontractor_modal.html", context)

@login_required(login_url='/home/')
def update_subcontractor(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(subcontractor, id = id)
 
    form = subcontractorForm(request.POST or None, instance = obj)
    
    can_delete = False
    #Validate if the subcontractor is associeted with an External production
    ep_sub = externalProduction.objects.filter(subcontractor = obj).count()
    #Validete if the subcontractor is associated with an Internal PO:
    ipo_sub = internalPO.objects.filter(vendor= 'S'+ str(obj.id)).count()
    
    if ep_sub == 0 and ipo_sub == 0:
        context["can_delete"] = True
 
    if form.is_valid():
        form.save()
        return HttpResponseRedirect("/subcontractor_list/")

    context["form"] = form
    context["emp"] = emp
    context["subcontractor_id"] = id
    
    return render(request, "create_subcontractor.html", context)

@login_required(login_url='/home/')
def delete_subcontractor(request, id):   

    obj = get_object_or_404(subcontractor, id = id)
 
    if obj:
        obj.delete()        
        
    return HttpResponseRedirect("/subcontractor_list/")

@login_required(login_url='/home/')
def external_prod_list(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context = {}    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    context["externalProd"] = externalProduction.objects.filter(woID = wo)
    context["emp"] = emp
    return render(request, "external_prod_list.html", context)

@login_required(login_url='/home/')
def create_external_prod(request, woID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    
    woid = workOrder.objects.filter(id = woID).first()

    form = extProdForm(request.POST or None, initial={'woID': woid})
    context['id'] = None

    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()  
        context["id"] = form.instance.id  

        context["items"] = externalProdItem.objects.filter(externalProdID = form.instance)

        return HttpResponseRedirect("/get_external_prod/" + str(form.instance.id))

    context["order"] = woid     
    context['form']= form
    context["emp"]=emp
    return render(request, "create_external_prod.html", context)

@login_required(login_url='/home/')
def get_external_prod(request, id):
    
    context ={}
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()   
    per = period.objects.filter(status__in=(1,2)).first()
    is_open = True

    obj = get_object_or_404(externalProduction , id = id )

    if obj.subcontractor.pay70Percent == True:
        context["payPercent"] = "70%"
    else:
        context["payPercent"] = obj.subcontractor.payPercent + "%"

    extProdItem = externalProdItem.objects.filter(externalProdID = obj)
    totalextProdItem = 0

    for i in extProdItem:
        if i.Status != 1:
            is_open = False

        totalextProdItem += i.total
    
    context["totalextProdItem"] = totalextProdItem
    context["id"] = id
    context["items"] = extProdItem
    context["is_open"] = is_open

    context["per"] = per
    context["form"] = obj
    context["emp"] = emp
    context["order"] = obj.woID
    return render(request, "get_external_prod.html", context)

@login_required(login_url='/home/')
def update_external_prod(request, id):

    context ={}
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    obj = get_object_or_404(externalProduction , id = id )

    if obj.woID.Status == '5' and not emp.is_superAdmin:
        messages.error(request, "Solo SuperAdmin puede modificar produccion externa en ordenes facturadas")
        return HttpResponseRedirect("/get_external_prod/" + str(id))

    form = extProdForm(request.POST or None, instance = obj)

    if form.is_valid():
        try:
            newFile = request.FILES['myfile']
            form.instance.invoice = newFile
        except Exception as e:
            None
        form.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({"status": "ok"})

        return HttpResponseRedirect("/get_external_prod/" + str(id))
    elif request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        messages.error(request, "Error al guardar: " + str(form.errors))

    context["per"] = per
    context["form"] = form
    context["emp"] = emp
    return render(request, "update_external_prod.html", context)

@login_required(login_url='/home/')
def remove_external_prod(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    
    per = period.objects.filter(status__in=(1,2)).first()
    
    obj = get_object_or_404(externalProduction , id = id )
 

    if obj:

        ext_prod_item = externalProdItem.objects.filter(externalProdID = obj)

        for i in ext_prod_item:

            authItem = authorizedBilling.objects.filter(woID = i.externalProdID.woID, itemID = i.itemID, Status = 1).first()

            if authItem:
                if authItem.quantity == i.quantity:
                    authItem.delete()
                else:
                    authItem.quantity -=  i.quantity
                    authItem.save()

            i.delete()

        obj.delete()

        return HttpResponseRedirect("/external_prod_list/" + str(obj.woID.id))

    context["per"] = per
    context["emp"] = emp
    return render(request, "get_external_prod.html", context)



@login_required(login_url='/home/')
def upload_external_prod(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    context ={}  
    context["emp"] = emp
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    if request.method == 'POST':
        new_invoice = request.FILES['myfile']
        
        d = externalProduction.objects.filter(id = id).first()

        if d:            
            d.invoice = new_invoice            
            d.save()   

    return HttpResponseRedirect("/get_external_prod/" + str(id))

def propagate_ext_prod_changes_to_billing(request, ext_prod_item):
    wo = ext_prod_item.externalProdID.woID
    new_item = ext_prod_item.itemID
    new_qty = ext_prod_item.quantity
    new_total = ext_prod_item.total

    auth = None

    if ext_prod_item.autorizedID:
        auth = authorizedBilling.objects.filter(id=ext_prod_item.autorizedID.id).first()

    if not auth and ext_prod_item.invoice:
        auth = authorizedBilling.objects.filter(
            woID=wo, itemID=new_item, invoice=ext_prod_item.invoice
        ).first()

    if not auth and ext_prod_item.estimate:
        auth = authorizedBilling.objects.filter(
            woID=wo, itemID=new_item, estimate=ext_prod_item.estimate
        ).first()

    if not auth:
        auth = authorizedBilling.objects.filter(
            woID=wo, itemID=new_item, Status__in=(2, 3)
        ).first()

    if auth:
        auth.itemID = new_item
        auth.quantity = new_qty
        auth.total = new_total
        auth.updated_date = datetime.now()
        auth.updatedBy = request.user.username
        auth.save()

        ext_prod_item.autorizedID = auth
        ext_prod_item.save()

    estimates = woEstimate.objects.filter(woID=wo, Status__in=(1, 2))
    for est in estimates:
        calculate_estimate_total(request, wo.id, est.estimateNumber)

    invoices = woInvoice.objects.filter(woID=wo, Status__in=(1, 2))
    for inv in invoices:
        calculate_invoice_total(request, wo.id, inv.invoiceNumber)

@login_required(login_url='/home/')
def create_ext_prod_item(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    dailyID = externalProduction.objects.filter(id = id).first()

    if dailyID.woID.Status == '5' and not emp.is_superAdmin:
        messages.error(request, "Solo SuperAdmin puede agregar items de produccion externa en ordenes facturadas")
        return HttpResponseRedirect("/get_external_prod/" + str(dailyID.id))

    dailyI = externalProdItem.objects.filter(externalProdID = dailyID)
    itemList = []

    for i in dailyI:
       itemList.append(i.itemID.item.itemID) 

    if dailyID.woID.Location != None:
        #itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.woID.Location.LocationID).exclude(item__itemID__in = itemList)

        #Validate if the WO was created after the Prices Update
        priceUpdate = "2025-03-03"
        priceCreated = dailyID.woID.created_date

        if priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date():
            itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.woID.Location.LocationID, item__is_new= True).exclude(item__itemID__in = itemList)
        else:
            itemLocation = itemPrice.objects.filter(location__LocationID = dailyID.woID.Location.LocationID, item__is_new= False).exclude(item__itemID__in = itemList)

        context["is_new"] = priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date()
        context["created"] = datetime.strftime(priceCreated.date(), "%Y-%m-%d")
        
    else:
        itemLocation = None


    form = extProdItemForm(request.POST or None, initial={'externalProdID': dailyID}, qs = itemLocation)
    if form.is_valid():    
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        price = form.instance.itemID.price    
        form.instance.total = form.instance.quantity * float(price)
        form.instance.created_date = datetime.now()

        form.save()      

        return HttpResponseRedirect("/get_external_prod/" + str(form.instance.externalProdID.id))       
         
    context['form']= form
    context["emp"] = emp
    context["itemList"] = itemLocation
    context["externalProdID"] = dailyID
    return render(request, "create_ext_prod_item.html", context)

@login_required(login_url='/home/')
def update_ext_prod_item(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(externalProdItem, id = id)

    if obj.externalProdID.woID.Status == '5' and not emp.is_superAdmin:
        messages.error(request, "Solo SuperAdmin puede modificar produccion externa en ordenes facturadas")
        return HttpResponseRedirect("/get_external_prod/" + str(obj.externalProdID.id))

    itemLocation = itemPrice.objects.filter(location__LocationID = obj.externalProdID.woID.Location.LocationID)
    
    itemSelected = itemPrice.objects.filter(id = obj.itemID.id ).first()

    form = extProdItemForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if form.is_valid():
        price = form.instance.itemID.price    
        form.instance.total = form.instance.quantity * float(price)
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        form.save()
        context["emp"] = emp

        propagate_ext_prod_changes_to_billing(request, form.instance)

        return HttpResponseRedirect("/get_external_prod/" + str(form.instance.externalProdID.id)) 

    context["form"] = form
    context["emp"] = emp
    context["itemSelected"] = itemSelected

    return render(request, "update_ext_prod_item.html", context)

@login_required(login_url='/home/')
def delete_ext_prod_item(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(externalProdItem, id = id)

    if obj.externalProdID.woID.Status == '5' and not emp.is_superAdmin:
        messages.error(request, "Solo SuperAdmin puede eliminar items de produccion externa en ordenes facturadas")
        return HttpResponseRedirect("/get_external_prod/" + str(obj.externalProdID.id))
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        wo = obj.externalProdID.woID

        authItem = authorizedBilling.objects.filter(woID = wo, itemID = obj.itemID, Status = 1).first()

        if authItem:
            if authItem.quantity == obj.quantity:
                authItem.delete()
            else:
                authItem.quantity -=  obj.quantity
                authItem.save()

        authItemInvoiced = authorizedBilling.objects.filter(woID = wo, itemID = obj.itemID, Status__in=(2, 3)).first()

        if authItemInvoiced:
            if authItemInvoiced.quantity == obj.quantity:
                authItemInvoiced.delete()
            else:
                authItemInvoiced.quantity -= obj.quantity
                authItemInvoiced.save()

        obj.delete()

        estimates = woEstimate.objects.filter(woID=wo, Status__in=(1, 2))
        for est in estimates:
            calculate_estimate_total(request, wo.id, est.estimateNumber)

        invoices = woInvoice.objects.filter(woID=wo, Status__in=(1, 2))
        for inv in invoices:
            calculate_invoice_total(request, wo.id, inv.invoiceNumber)

        return HttpResponseRedirect("/get_external_prod/" + str(obj.externalProdID.id)) 

   
    return render(request, "delete_ext_prod_item.html", context)


    

@login_required(login_url='/home/')
def authorized_billing_list(request, id):
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    

    payItems = DailyItem.objects.filter(DailyID__woID = wo)
    itemResume = []


    opType = "Access Option"
    opDetail = "Billing List"
    logInAuditLog(request, opType, opDetail)


    try:
        for data in payItems:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    # Group External Production by Item
    try:
        extProduction = externalProdItem.objects.filter(externalProdID__woID = wo)

        for data in extProduction:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    itemFinal = []

    countAuthItem = authorizedBilling.objects.filter(woID = wo).count()

    #Insert Production in Authorized Items
    if countAuthItem == 0:
        for itemR in itemResume:

            #Getting the Item Price

            iPrice = itemPrice.objects.filter(item__itemID=itemR['item'], location__LocationID = wo.Location.LocationID).first()

            authI = authorizedBilling(
                        woID = wo,
                        itemID = iPrice,
                        quantity = itemR['quantity'],
                        total = itemR['amount'],
                        createdBy = request.user.username,
                        created_date = datetime.now()
                    )

            authI.save()       
            
    authorizedItem = authorizedBilling.objects.filter(woID = wo)

    for itemA in authorizedItem:
        itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

        if itemResult != None:          
            itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
        else:
            itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})



    context["itemResume"] = sorted(itemFinal, key=lambda d: d['item']) 
  
    return render(request, "authorized_billing_list.html", context)

@login_required(login_url='/home/')
def create_authorized_prod_item(request, id, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = id).first()

    if int(invoiceID) == 0 and int(estimateID) == 0:
        authorizedItems = authorizedBilling.objects.filter(woID = wo, estimate__isnull = True, invoice__isnull = True )
    elif int(estimateID) > 0:
        authorizedItems = authorizedBilling.objects.filter(woID = wo, estimate = int(estimateID))
    elif int(invoiceID) > 0:
        authorizedItems = authorizedBilling.objects.filter(woID = wo, invoice = int(invoiceID) )
        
    itemList = []

    for i in authorizedItems:
       itemList.append(i.itemID.item.itemID) 

    if wo.Location != None:
        #itemLocation = itemPrice.objects.filter(location__LocationID = wo.Location.LocationID).exclude(item__itemID__in = itemList)

        #Validate if the WO was created after the Prices Update
        priceUpdate = "2025-03-03"
        priceCreated = wo.created_date

        if priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date():
            itemLocation = itemPrice.objects.filter(location__LocationID = wo.Location.LocationID, item__is_new= True).exclude(item__itemID__in = itemList)
        else:
            itemLocation = itemPrice.objects.filter(location__LocationID = wo.Location.LocationID, item__is_new= False).exclude(item__itemID__in = itemList)

        context["is_new"] = priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date()
        context["created"] = datetime.strftime(priceCreated.date(), "%Y-%m-%d")
    else:
        itemLocation = None


    form = authorizedBillingForm(request.POST or None, initial={'woID': wo}, qs = itemLocation)
    if form.is_valid():    
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem
        
        if int(invoiceID) != 0:                       
            invoiceO = woInvoice.objects.filter(woID = wo, invoiceNumber = int(invoiceID)).first()  
            invoiceO.Status = 3
            invoiceO.save()
            
            form.instance.invoice = int(invoiceID)
            form.instance.estimate = invoiceO.estimateNumber
            form.instance.Status = 3
        
        if int(estimateID) != 0:                       
            estimateO = woEstimate.objects.filter(woID = wo, estimateNumber = int(estimateID)).first()  
            #estimateO.Status = 3
            estimateO.save()
            
            
            woInv = woInvoice.objects.filter(woID = wo, estimateNumber = int(estimateID)).first()
            
            if woInv:
                form.instance.invoice = woInv.invoiceNumber

                
            form.instance.estimate = int(estimateID)
            form.instance.Status = 2
        
        price = form.instance.itemID.price    
        form.instance.total = form.instance.quantity * float(price)
        form.instance.created_date = datetime.now()
        form.instance.updated_date = datetime.now()
        form.instance.updatedBy = request.user.username
        form.save()      

        if int(invoiceID) == 0 and int(estimateID) == 0:
            return HttpResponseRedirect("/billing_list/" + str(wo.id) + "/False")    
        elif int(estimateID) > 0: 
            if woInv:
                calculate_invoice_total(request, wo.id, woInv.invoiceNumber )

            return HttpResponseRedirect("/update_estimate/" + str(wo.id) + "/"  + estimateID )
            
        elif int(invoiceID) > 0:
            calculate_invoice_total(request, wo.id, int(invoiceID) )
            return HttpResponseRedirect("/update_invoice/" + str(wo.id) + "/"  + invoiceID  )   
         
    context['form']= form
    context["emp"] = emp
    context["itemList"] = itemLocation
    return render(request, "create_authorized_prod_item.html", context)

@login_required(login_url='/home/')
def update_authorized_prod_item(request, id, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    estimateO = None
    invoiceO = None

    obj = get_object_or_404(authorizedBilling, id = id)

    itemLocation = itemPrice.objects.filter(location__LocationID = obj.woID.Location.LocationID)
    
    itemSelected = itemPrice.objects.filter(id = obj.itemID.id ).first()

    form = authorizedBillingForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if form.is_valid():
        price = form.instance.itemID.price    
        form.instance.total = form.instance.quantity * float(price)
        
        itemid = request.POST.get('itemID')
        
        selectedItem = itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem
        form.instance.updated_date = datetime.now()
        form.instance.updatedBy = request.user.username
        form.save()
        context["emp"] = emp    

        if int(invoiceID) == 0 and int(estimateID) == 0:
            return HttpResponseRedirect("/billing_list/" + str(form.instance.woID.id) + "/False") 
        elif int(invoiceID) > 0:            
            
            invoiceO = woInvoice.objects.filter(woID = obj.woID, invoiceNumber = int(invoiceID)).first()            
            invoiceO.Status = 3
            invoiceO.save() 

   
            calculate_invoice_total(request, obj.woID.id, int(invoiceID))
    
            estimateO = woEstimate.objects.filter(woID = obj.woID, estimateNumber = invoiceO.estimateNumber ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
            
            return HttpResponseRedirect("/update_invoice/" + str(obj.woID.id) + "/"  + invoiceID)
            
        elif int(estimateID) > 0:            
            
            invoiceO = woInvoice.objects.filter(woID = obj.woID, estimateNumber = int(estimateID)).first()            
            if invoiceO:
                invoiceO.Status = 3
                invoiceO.save() 

                calculate_invoice_total(request, obj.woID.id, invoiceO.invoiceNumber )

                
            estimateO = woEstimate.objects.filter(woID = obj.woID, estimateNumber = int(estimateID) ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
        
            return HttpResponseRedirect("/update_estimate/" + str(obj.woID.id) + "/"  + estimateID)  

    context["form"] = form
    context["emp"] = emp
    context["itemSelected"] = itemSelected

    return render(request, "update_authorized_prod_item.html", context)

@login_required(login_url='/home/')
def delete_authorized_prod_item(request, id, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(authorizedBilling, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        aComment = request.POST.get('comment')
        obj.comment = aComment
        obj.total = 0
        obj.quantity = 0
        obj.updated_date = datetime.now()
        obj.updatedBy = request.user.username
        obj.save()


        if int(invoiceID) == 0 and int(estimateID) == 0:
            return HttpResponseRedirect("/billing_list/" + str(obj.woID.id)+ "/False") 
        elif int(invoiceID) > 0:           
            
            invoiceO = woInvoice.objects.filter(woID = obj.woID, invoiceNumber = int(invoiceID)).first()  
            invoiceO.Status = 3
            invoiceO.save() 

  
            calculate_invoice_total(request, obj.woID.id, int(invoiceID) )


            estimateO = woEstimate.objects.filter(woID = obj.woID, estimateNumber = invoiceO.estimateNumber ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
            
            return HttpResponseRedirect("/update_invoice/" + str(obj.woID.id) + "/"  + invoiceID)
            
        elif int(estimateID) > 0:            
            
            invoiceO = woInvoice.objects.filter(woID = obj.woID, estimateNumber = int(estimateID)).first()            
            if invoiceO:
                invoiceO.Status = 3
                invoiceO.save() 

                calculate_invoice_total(request, obj.woID.id, invoiceO.invoiceNumber )
                
            estimateO = woEstimate.objects.filter(woID = obj.woID, estimateNumber = int(estimateID) ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
        
            return HttpResponseRedirect("/update_estimate/" + str(obj.woID.id) + "/"  + estimateID)  

   
    return render(request, "delete_authorized_prod_item.html", context)

@login_required(login_url='/home/')
def delete_hours(request, orderID, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per  
    context["emp"] = emp

    wo = workOrder.objects.filter(id = orderID).first()
 
    if request.method == 'POST':
        if int(invoiceID) == 0 and int(estimateID) == 0:
            return HttpResponseRedirect("/billing_list/" + str(orderID) + "/False") 
        elif int(invoiceID) > 0:           
            
            
            #Billable Hours

            bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice = invoiceID)

            for b in  bill:
                bObject = DailyEmployee.objects.filter(id = b.id).first()
                bObject.Status = 4
                bObject.save()

            invoiceO = woInvoice.objects.filter(woID = wo, invoiceNumber = int(invoiceID)).first()  
            invoiceO.Status = 3
            invoiceO.save() 

            calculate_invoice_total(request, orderID, int(invoiceID))


            estimateO = woEstimate.objects.filter(woID = wo, estimateNumber = invoiceO.estimateNumber ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
            
            return HttpResponseRedirect("/update_invoice/" + str(orderID) + "/"  + invoiceID)
            
        elif int(estimateID) > 0:            
            
            #Billable Hours

            bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID)

            for b in  bill:
                bObject = DailyEmployee.objects.filter(id = b.id).first()
                bObject.Status = 4
                bObject.save()

            invoiceO = woInvoice.objects.filter(woID = wo, estimateNumber = int(estimateID)).first()            
            if invoiceO:
                invoiceO.Status = 3
                invoiceO.save() 

                calculate_invoice_total(request, orderID, invoiceO.invoiceNumber )
                
            estimateO = woEstimate.objects.filter(woID = wo, estimateNumber = int(estimateID) ).first()  
            if estimateO:
                #estimateO.Status = 3
                estimateO.save() 
        
            return HttpResponseRedirect("/update_estimate/" + str(orderID) + "/"  + estimateID)  

   
    return render(request, "delete_hours.html", context)

@login_required(login_url='/home/')
def comment_authorized_prod_item(request, id):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(authorizedBilling, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        aComment = request.POST.get('comment')
        obj.comment = aComment
        obj.total = 0
        obj.quantity = 0
        obj.save()


        return HttpResponseRedirect("/billing_list/" + str(obj.woID.id) + "/False") 

   
    return render(request, "comment_authorized_prod_item.html", context)

@login_required(login_url='/home/')
def production_transfer(request, id, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(authorizedBilling, id = id)

    #Getting the list of WO used with the current Items
    woList = []

    authorizedItems = authorizedBilling.objects.filter(itemID = obj.itemID, transferFrom = obj.woID)

    for i in authorizedItems:
       woList.append(i.woID.id) 

    wo = workOrder.objects.filter(Status = 2).exclude(id__in = woList)
    context["orderList"] = wo    
    
    itemLocation = itemPrice.objects.all()

    form = TrauthorizedBillingForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if request.method == 'POST':     
        destWoID = request.POST.get('destinationID')
        destQty = request.POST.get('destinationQty')
        
        #Getting destination wo
        destWO = workOrder.objects.filter(id = int(destWoID)).first()

        if destWO and int(destQty) > 0:

            newQty = obj.quantity - int(destQty)
            obj.transferTo =  destWO
            obj.transferQty = int(destQty)
            obj.transfer_date = datetime.now()
            obj.transferBy = request.user.username
            obj.quantity = newQty
            #updating the price
            price = obj.itemID.price    
            obj.total = newQty * float(price)
            obj.updated_date = datetime.now()
            obj.updatedBy = request.user.username
            obj.save()

            
            invoiceO = woInvoice.objects.filter(woID = obj.woID.id, estimateNumber = int(estimateID)).first()
            if invoiceO:
                calculate_invoice_total(request,obj.woID.id,invoiceO.invoiceNumber)
            
            #if Item Transfer Exists in destination
            # destABItem = authorizedBilling.objects.filter(woID = destWO, itemID = obj.itemID, transferFrom = obj.woID ).first()
       
            destAB = authorizedBilling (
                        woID = destWO,
                        itemID = obj.itemID,
                        quantity = int(destQty),
                        total = int(destQty) * float(price),                     
                        Status = 1,                        
                        transferFrom = obj.woID,                        
                        transferQty = int(destQty),
                        transfer_date = datetime.now(),
                        transferBy = request.user.username,
                        created_date = datetime.now(),
                        createdBy = request.user.username                        
                    )
            destAB.save()
        
        

        context["emp"] = emp    
        
        return HttpResponseRedirect("/update_estimate/" + str(obj.woID.id) + "/"  + estimateID)
    
       
    context["form"] = form
    context["emp"] = emp

    return render(request, "production_transfer.html", context)

@login_required(login_url='/home/')
def internal_po_transfer(request, id, invoiceID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(internalPO, id = id)

    #Getting the list of WO used with the current Items
    woList = []

    #authorizedItems = internalPO.objects.filter(itemID = obj.itemID, transferFrom = obj.woID)

    #for i in authorizedItems:
    #   woList.append(i.woID.id) 

    wo = workOrder.objects.filter(Status = 2).exclude(id__in = woList)
    context["orderList"] = wo    
    
    itemLocation = itemPrice.objects.all()

    form = InternalPOForm(request.POST or None, instance = obj)
 
    if request.method == 'POST':     
        destWoID = request.POST.get('destinationID')        
        
        #Getting destination wo
        destWO = workOrder.objects.filter(id = int(destWoID)).first()
        originWO = workOrder.objects.filter(id = obj.woID.id).first()

        if destWO:
            obj.woID =  destWO           
            obj.transfer_date = datetime.now()
            obj.transferBy = request.user.username
            obj.transferFromPO = originWO
            obj.estimate = None
            obj.invoice = None
            obj.Status = 1
            obj.save()

            
            invoiceO = woInvoice.objects.filter(woID = originWO.id, estimateNumber = int(estimateID)).first()
            if invoiceO:
                calculate_invoice_total(request,originWO.id,invoiceO.invoiceNumber)
        
        

        context["emp"] = emp    
        
        return HttpResponseRedirect("/update_estimate/" + str(originWO.id) + "/"  + estimateID)
    
       
    context["form"] = form
    context["emp"] = emp

    return render(request, "internal_po_transfer.html", context)

@login_required(login_url='/home/')
def billing_list(request, id, isRestoring):
    errorMessage = ""
    try:
        context = {} 
        emp = Employee.objects.filter(user__username__exact = request.user.username).first()
        context["emp"] = emp

        per = period.objects.filter(status__in=(1,2)).first()
        context["per"] = per

        wo = workOrder.objects.filter(id=id).first()
        context["order"] = wo

        context['status_ready'] = str(wo.Status) in ['2', '7', '8']
        

        payItems = DailyItem.objects.filter(DailyID__woID = wo, Status=1)
        itemResume = []


        #list estimate numbers
        estimateList = woEstimate.objects.filter(woID = wo)
        estimateFList = []
        for eList in estimateList:
            invoiceO = woInvoice.objects.filter(woID = wo, estimateNumber = eList.estimateNumber).first()
            if invoiceO:
                invoiceNum = invoiceO.invoiceNumber
            else:
                invoiceNum = 0

            adjustment = woAdjustment.objects.filter(woID = wo, estimateNumber = eList.estimateNumber).first()
            adj = False

            if adjustment:
                adj = True
            
            estimateFList.append({'woID': eList.woID, 'estimateNumber': eList.estimateNumber, 'invoiceNumber':invoiceNum, 'Status':eList.Status, 'is_partial':eList.is_partial, 'created_date': eList.created_date, 'createdBy': eList.createdBy, 'adjustment': adj})

        context["estimateList"] = estimateFList

        #list estimate numbers
        estimateList = woInvoice.objects.filter(woID = wo)
        context["invoiceList"] = estimateList

        try:
            for data in payItems:                

                itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
                amount = 0
                
                #Calculate amount with DailyItem.price
                #amount = Decimal(str(validate_decimals(data.quantity))) * Decimal(str(validate_decimals(data.itemID.price)))  
                amount = Decimal(str(validate_decimals(data.quantity))) * Decimal(str(validate_decimals(data.price)))  

                if amount == 0:
                    amount = Decimal(str(validate_decimals(data.quantity))) * Decimal(str(validate_decimals(data.itemID.price))) 


                if amount == 0:
                    #Calculate amount with DailyItem.price
                    #errorMessage = "There is a Problem with " + data.itemID.item.itemID + ' - ' + data.itemID.item.name + ' Price: '+ str(validate_decimals(data.itemID.price)) + ' Amount ' + str(validate_decimals(amount))
                    errorMessage = "There is a Problem with " + data.itemID.item.itemID + ' - ' + data.itemID.item.name + ' Price: '+ str(validate_decimals(data.price)) + ' Amount ' + str(validate_decimals(amount))

                if itemResult != None:                                      
                    itemResume[itemResult]['quantity'] += data.quantity
                    itemResume[itemResult]['amount'] += amount
                    if data.isAuthorized == False:
                        itemResume[itemResult]['updateQuantity'] += data.quantity
                        itemResume[itemResult]['updateAmount'] += amount
                else:            
                    if data.isAuthorized == False:
                        #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False, 'updateAmount':amount, 'updateQuantity':data.quantity})
                        #Adding Price from Amount/Qty                        
                        itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.price, 'amount':amount,'Encontrado':False, 'updateAmount':amount, 'updateQuantity':data.quantity})
                    else:
                        #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False, 'updateAmount':0, 'updateQuantity':0})
                        
                        #if data.price == 0 then use the Item Catalog Price
                        if data.price == 0 or data.price == None:
                            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False, 'updateAmount':0, 'updateQuantity':0})
                        else:                        
                            #Adding Price from Amount/Qty
                            itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.price, 'amount':amount,'Encontrado':False, 'updateAmount':0, 'updateQuantity':0})

                if data.isAuthorized == False:
                    currentItem = DailyItem.objects.filter(id = data.id).first()
                    currentItem.isAuthorized = True               
                    currentItem.authorized_date = datetime.now()
                    currentItem.save()
        
        except Exception as e:
            errorMessage += str(e) + ' primero \n\n'
            print(str(e)) 

        # Group External Production by Item
        try:
            extProduction = externalProdItem.objects.filter(externalProdID__woID = wo, Status=1)

            for data in extProduction:

                itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
                amount = 0
                amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
                if itemResult != None:                  
                    itemResume[itemResult]['quantity'] += data.quantity
                    itemResume[itemResult]['amount'] += amount

                    if data.isAuthorized == False:
                        itemResume[itemResult]['updateQuantity'] += data.quantity
                        itemResume[itemResult]['updateAmount'] += amount
                else:          
                    if data.isAuthorized == False:
                        itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False, 'updateAmount':amount, 'updateQuantity':data.quantity})
                        
                    else:                      
                        itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False, 'updateAmount':0, 'updateQuantity':0})

                if data.isAuthorized == False:
                    currentItem = externalProdItem.objects.filter(id = data.id).first()
                    currentItem.isAuthorized = True               
                    currentItem.authorized_date = datetime.now()
                    currentItem.save() 
            
        except Exception as e:
            errorMessage += str(e) + ' segundo \n\n'
            print(str(e)) 

        itemFinal = []    


        #Insert Production in Authorized Items
        for itemR in itemResume:

            #Validating if Item exists in Authorized Item
            countItem = authorizedBilling.objects.filter(woID = wo, Status = 1, itemID__item__itemID = itemR['item']).count()

            if countItem == 0:
                #Getting the Item Price
                iPrice = itemPrice.objects.filter(item__itemID=itemR['item'], location__LocationID = wo.Location.LocationID).first()

                if iPrice:

                    authI = authorizedBilling(
                                woID = wo,
                                itemID = iPrice,
                                quantity = itemR['quantity'],
                                total = itemR['amount'],
                                createdBy = request.user.username,
                                created_date = datetime.now(),
                                transferQty = 0
                            )

                    authI.save()     

                else:
                    errorMessage += 'Item ' + str(itemR['item']) + ' does not have a price definition for ' + wo.Location.name + '. ' +  os.linesep 
            else:
                existingAB = authorizedBilling.objects.filter(woID = wo, Status = 1, itemID__item__itemID = itemR['item']).first()
                if isRestoring == "True":
                    existingAB.quantity = itemR['quantity']
                    existingAB.total = float(itemR['amount'])
                    existingAB.save()
                else:                  
                    existingAB.quantity += itemR['updateQuantity']
                    existingAB.total += float(itemR['updateAmount'])
                    existingAB.save()


        authorizedItem = authorizedBilling.objects.filter(woID = wo, Status = 1)
        qtyP = 0
        totalP = 0
        qtyA = 0
        totalA = 0

        for itemA in authorizedItem:
            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

            if itemResult != None and itemA.transferFrom == None:    
                if itemA.quantity > 0:
                    priceA = itemA.total / itemA.quantity
                else:
                    priceA = 0
                        
                #itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'transferFrom': itemA.transferFrom, 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
                itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'transferFrom': itemA.transferFrom, 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA': itemResume[itemResult]['price'], 'amountA':itemA.total, 'idA': itemA.id})
                qtyP += validate_decimals(itemResume[itemResult]['quantity'])
                totalP += validate_decimals(itemResume[itemResult]['amount'])
                qtyA += validate_decimals(itemA.quantity)
                totalA += validate_decimals(itemA.total)
            else:

                if itemA.quantity > 0:
                    priceA = itemA.total / itemA.quantity
                else:
                    priceA = 0

                #itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'transferFrom': itemA.transferFrom ,'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
                itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'transferFrom': itemA.transferFrom ,'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':priceA, 'amountA':itemA.total, 'idA': itemA.id})
                qtyA += validate_decimals(itemA.quantity)
                totalA += validate_decimals(itemA.total)

        #Getting Partial Estimates
        openEstimate = woEstimate.objects.filter(woID = wo, Status = 1).count()


        #Getting Internal POs
        internal = internalPO.objects.filter(woID = wo, nonBillable = False)

        vendorList = vendorSubcontrator(request) 
        context["vendorList"] = vendorList

        context["internalPO"] = internal
        context["openEstimate"] = openEstimate > 0
        context["itemCount"] = len(itemFinal)
        context["itemResume"] = sorted(itemFinal, key=lambda d: d['item']) 
        context["totals"] = {'qtyP':qtyP, 'totalP':totalP,'qtyA':qtyA,'totalA':totalA  }
        
        
        ##### Calculos
        prod_facturada = 0
        prod_facturada = get_invoiced_production_total_for_wo(wo.id)
        prod_no_facturada = 0
        prod_no_facturada = get_uninvoiced_production_total_for_wo(wo.id)
        
        po_total = 0
        for i in internal:
            if i.total:
                if i.isAmountRounded:
                    po_total += int(round(float(str(i.total))))
                else:
                    po_total += Decimal(str(i.total))
		
        po_total = validate_decimals(po_total)
        
        #po Facturado
        po_facturado = 0
        
        internal_facturado = internalPO.objects.filter(woID = wo, nonBillable = False, invoice__isnull = False )
        
        for i in internal_facturado:
            if i.total:
                if i.isAmountRounded:
                    po_facturado += int(round(float(str(i.total))))
                else:
                    po_facturado += Decimal(str(i.total))
		
        po_facturado = validate_decimals(po_facturado)
        
        #po No Facturado
        po_no_facturado = 0
        
        internal_no_facturado = internalPO.objects.filter(woID = wo, nonBillable = False, invoice__isnull = True )
        
        for i in internal_no_facturado:
            if i.total:
                if i.isAmountRounded:
                    po_no_facturado += int(round(float(str(i.total))))
                else:
                    po_no_facturado += Decimal(str(i.total))
		
        po_no_facturado = validate_decimals(po_no_facturado)
        
        #Calculate Payroll
        dailys = Daily.objects.filter(woID = wo)
        
        empTotal = 0
        for itemd in dailys:
            dailyEmp = DailyEmployee.objects.filter(DailyID = itemd)

            for empI in dailyEmp:
                empTotal += validate_decimals(empI.payout)

	    # Subcontractor = External Production Calculate
        subcontractor = 0
        subC = externalProduction.objects.filter(woID = wo)
        for s in subC:
            subcontractor += validate_decimals(s.total_invoice)
        
        context["prod_facturada"] = validate_decimals(prod_facturada)
        context["prod_no_facturada"] = validate_decimals(prod_no_facturada)
        context["po_total"] = po_total 
        context["subcontractor"] = subcontractor 
        context["payroll"] = empTotal         
        context["billing_amount"] = validate_decimals(prod_facturada) +  validate_decimals(prod_no_facturada)

    except Exception as e:
        errorMessage += str(e) + 'ultimo \n'
        print(str(e)) 
     
    context["errorMessage"] = errorMessage
         
    return render(request, "billing_list.html", context)

@login_required(login_url='/home/')
def restore_original_production(request, id):

    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    context["woID"] = id


    if request.method == 'POST':   
        return HttpResponseRedirect("/billing_list/" + str(id) + "/True")

    return render(request, "restore_original_production.html", context)

@login_required(login_url='/home/')
def update_invoice(request, id, invoiceID):
    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    context["orderID"] = id
    

    payItems = DailyItem.objects.filter(DailyID__woID = wo, invoice = invoiceID)
    itemResume = []

    try:
        for data in payItems:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    # Group External Production by Item
    try:
        extProduction = externalProdItem.objects.filter(externalProdID__woID = wo, invoice = invoiceID)

        for data in extProduction:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    itemFinal = []    
            
    authorizedItem = authorizedBilling.objects.filter(woID = wo, invoice = invoiceID)
    qtyP = 0
    totalP = 0
    qtyA = 0
    totalA = 0

    for itemA in authorizedItem:
        itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

        if itemResult != None:          
            itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyP += validate_decimals(itemResume[itemResult]['quantity'])
            totalP += validate_decimals(itemResume[itemResult]['amount'])
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)
        else:
            itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)

    #Getting Partial Estimates
    openEstimate = woEstimate.objects.filter(woID = wo, Status = 1).count()

    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice = invoiceID).exclude(Status=4)

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))
       

    billableHours = [{'Description': 'Billable Hours', 'TotalHours': totalHours, 'totalHoursRate':totalHoursRate}]
    context["billableHours"]=billableHours

    
    context["openEstimate"] = openEstimate > 0
    context["itemCount"] = len(itemFinal)
    context["itemResume"] = sorted(itemFinal, key=lambda d: d['item']) 
    context["totals"] = {'qtyP':qtyP, 'totalP':totalP,'qtyA':qtyA,'totalA':totalA  }
    context["invoiceID"] = invoiceID
    
    
    return render(request, "update_invoice.html", context)

@login_required(login_url='/home/')
def update_estimate(request, id, estimateID):    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    context["orderID"] = id

    payItems = DailyItem.objects.filter(DailyID__woID = wo, estimate = estimateID)
    itemResume = []

    try:
        for data in payItems:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            
            #amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            amount = Decimal(str(data.quantity)) * Decimal(str(data.price))  

            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                #caculate price with autorizeBilling price
                #itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    # Group External Production by Item
    try:
        extProduction = externalProdItem.objects.filter(externalProdID__woID = wo, estimate = estimateID)

        for data in extProduction:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
           
        
    except Exception as e:
        print(str(e)) 

    itemFinal = []    
            
    authorizedItem = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)
    qtyP = 0
    totalP = 0
    qtyA = 0
    totalA = 0

    for itemA in authorizedItem:
        itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

        if itemResult != None:          
            itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyP += validate_decimals(itemResume[itemResult]['quantity'])
            totalP += validate_decimals(itemResume[itemResult]['amount'])
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)
        else:
            itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)

    #Getting Partial Estimates
    openEstimate = woEstimate.objects.filter(woID = wo, Status = 1).count()


    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate = estimateID).exclude(Status=4)

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))

    billableHours = [{'Description': 'Billable Hours', 'TotalHours': totalHours, 'totalHoursRate':totalHoursRate}]
    context["billableHours"]=billableHours


    #Adding Billable Hours Not Included

    billNI = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, Status = 1)

    totalHoursNI = 0
    totalHoursRateNI =  0

    for bn in billNI:
        totalHoursNI +=  validate_decimals(bn.total_hours) 
        #Calculating Regular Hours
        totalHoursRateNI += (validate_decimals(bn.regular_hours) * validate_decimals(bn.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRateNI += (validate_decimals(bn.ot_hour) * (validate_decimals(bn.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRateNI += (validate_decimals(bn.double_time) * (validate_decimals(bn.EmployeeID.hourly_rate)* 2))
       


    billableHoursNI = [{'Description': 'Billable Hours', 'TotalHours': totalHoursNI, 'totalHoursRate':totalHoursRateNI}]
    context["billableHoursNI"]=billableHoursNI
    
    #Getting Internal PO's to be added to Estimate and Invoice
    
    Internal = internalPO.objects.filter(woID = wo, Status=1)
    poTotal = 0
    for po in Internal:
        poTotal += validate_decimals(po.total)

    
    #Getting Internal PO's Included in Estimate
    
    InternalEst = internalPO.objects.filter(woID = wo, estimate = estimateID)
    poTotalEst = 0
    for po2 in InternalEst:
        poTotalEst += validate_decimals(po2.total)

    
    #Getting ActualEstimate Address
    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()
    context["woEstimate"] = woEst

    vendorList = vendorSubcontrator(request) 
    context["vendorList"] = vendorList

    
    context["openEstimate"] = openEstimate > 0
    context["itemCount"] = len(itemFinal)
    context["itemResume"] = sorted(itemFinal, key=lambda d: d['item']) 
    context["totals"] = {'qtyP':qtyP, 'totalP':totalP,'qtyA':qtyA,'totalA':totalA  }
    context["estimateID"] = estimateID
    context["internalPO"] = Internal
    context["internalPOEst"] = InternalEst

    context["poTotal"] = poTotal
    context["poTotalEst"] = poTotalEst
    
    
    return render(request, "update_estimate.html", context)

@login_required(login_url='/home/')
def delete_invoice(request, id, invoiceID):    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    invoice = woInvoice.objects.filter(woID_id=id, invoiceNumber=invoiceID).first()

    if invoice:
        
        estimate = woEstimate.objects.filter(woID = invoice.woID, estimateNumber = invoice.estimateNumber).first()
        
        if estimate:
            estimate.Status = 1
            estimate.save()
                
        invoice.delete()

    return HttpResponseRedirect("/billing_list/" + str(id)+ "/False") 

@login_required(login_url='/home/')
def convert_final_estimate(request, id, estimateID):    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    estimate = woEstimate.objects.filter(estimateNumber = estimateID).first()

    if estimate:
        estimate.is_partial = False
    
        estimate.save()

    return HttpResponseRedirect("/billing_list/" + str(id)+ "/False") 

@login_required(login_url='/home/')
def convert_partial_estimate(request, id, estimateID):    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    estimate = woEstimate.objects.filter(estimateNumber = estimateID).first()

    if estimate:
        estimate.is_partial = True
    
        estimate.save()

    return HttpResponseRedirect("/billing_list/" + str(id)+ "/False") 
    
    
    

@login_required(login_url='/home/')
def add_internalPO_to_estimate(request, poID, woID, estimateID):
    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = woID).first()
    context["order"] = wo
    
    woInv = woInvoice.objects.filter(woID = wo, estimateNumber = estimateID).first() 
    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first() 
    
    if woInv:
        context["invoiceNumber"] = woInv.invoiceNumber
    else:
        context["invoiceNumber"] = 0
        
    if woEst: 
        context["estimateNumber"] = woEst.estimateNumber
    else:
        context["estimateNumber"] = 0

    if request.method == 'POST':
        #Update Internal PO
        internal = internalPO.objects.filter(id = poID).first()
        status = 2
        
        if woInv:
            internal.invoice = woInv.invoiceNumber
            status = 3
        
        if woEst: 
            internal.estimate = woEst.estimateNumber
            
        internal.Status = status
        internal.save()


        return HttpResponseRedirect("/update_estimate/" + str(wo.id) + '/' + str(woEst.estimateNumber)) 
    
    return render(request, "update_po_to_estimate.html", context) 

@login_required(login_url='/home/')
def add_hours_to_estimate(request, woID, estimateID):
    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = woID).first()
    context["order"] = wo
    
    woInv = woInvoice.objects.filter(woID = wo, estimateNumber = estimateID).first() 
    woEst = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first() 
    
    if woInv:
        context["invoiceNumber"] = woInv.invoiceNumber
    else:
        context["invoiceNumber"] = 0
        
    if woEst: 
        context["estimateNumber"] = woEst.estimateNumber
    else:
        context["estimateNumber"] = 0

    if request.method == 'POST':
        #Update Hours PO
        internal = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True).exclude(Status=4)
        
        for i in internal:

            bill = DailyEmployee.objects.filter(id = i.id).first()
        
            status = 2
            
            if woInv:
                bill.invoice = woInv.invoiceNumber
                status = 3
            
            if woEst: 
                bill.estimate = woEst.estimateNumber
                
            bill.Status = status
            bill.save()


        return HttpResponseRedirect("/update_estimate/" + str(wo.id) + '/' + str(woEst.estimateNumber)) 
    
    return render(request, "update_hours_to_estimate.html", context) 

@login_required(login_url='/home/')
def order_detail(request, id,isSupervisor):
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id=id).first()
    context["order"] = wo
    
    context["isSupervisor"] = isSupervisor

    statusLog = woStatusLog.objects.filter(woID = wo)
    generalLog = ""

    context["general_log"] = statusLog
  
    return render(request, "order_detail.html", context)

@login_required(login_url='/home/')
def deleted_order_detail(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    obj = get_object_or_404(DeletedWorkOrders, id = id)
 

   
    form = DeletedworkOrderForm(request.POST or None, instance = obj)


    if form.is_valid(): 
        anterior = workOrder.objects.filter(id = id).first()    
         
        if form.instance.Status != anterior.Status:
            form.instance.UploadDate = datetime.now()
            log = woStatusLog( 
                            woID = anterior,
                            currentStatus = anterior.Status,
                            nextStatus = form.instance.Status,
                            createdBy = request.user.username,
                            created_date = datetime.now()
                            )
            log.save()
        form.save()       
        return HttpResponseRedirect('/order_detail/' + str(form.instance.id) + '/False')
 
    context["form"] = form
    context["emp"] = emp   
    return render(request, "deleted_order_detail.html", context)

@login_required(login_url='/home/')
def upload_invoice(request, order_id):
    if request.method == 'POST':
        form = WorkOrderFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            work_order = workOrder.objects.filter(id=order_id).first()            
            work_order.invoiceFile = form.cleaned_data['invoice_file']
            work_order.save()
            
            messages.success(request, 'Invoice uploaded successfully.')
            return redirect('order_detail', id=order_id, isSupervisor=False)
        else:
            messages.error(request, 'Failed to upload the invoice. Please try again.')
    else:
        form = WorkOrderFileUploadForm()
    return render(request, 'upload_invoice.html', {'form': form})


### Employees Views

@login_required(login_url='/home/')
def employee_location_list(request, empID):
    
    context = {} 
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    empSelected = Employee.objects.filter(employeeID = empID).first()
    context["empSelected"] = empSelected
    empLocation = employeeLocation.objects.filter(employeeID=empSelected)
    context["empLocation"] = empLocation
  
    return render(request, "employee_location_list.html", context)

@login_required(login_url='/home/')
def create_employee_location(request, empID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()

    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    
    
    empSelected = Employee.objects.filter(employeeID = empID).first()
    empLoca = employeeLocation.objects.filter(employeeID = empSelected )
        
    itemList = []

    itemList.append(empSelected.Location.LocationID) 
    
    for i in empLoca:
        itemList.append(i.LocationID.LocationID) 

    itemLocation = Locations.objects.all().exclude(LocationID__in = itemList)
   
    form = EmployeeLocationForm(request.POST or None,  initial={'employeeID': empSelected}, qs = itemLocation)

    if form.is_valid(): 
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()       
        form.save()
        # Return to Locations List
        return HttpResponseRedirect('/employee_location_list/' + str(empID))

         
    context['form']= form
    context["emp"] = emp
    return render(request, "create_employee_location.html", context)

@login_required(login_url='/home/')
def delete_employee_location(request, empID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(employeeLocation, id = empID)
 
    context["form"] = obj
    context["emp"] = emp
 
    if request.method == 'POST':
        obj.delete()

        return HttpResponseRedirect('/employee_location_list/' + str(obj.employeeID.employeeID))

   
    return render(request, "delete_employee_location.html", context)

@login_required(login_url='/home/')
def select_billing_address(request, id, isPartial, isUpdate):
    context ={}
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = id).first()
    
    addressList = billingAddress.objects.all()
    context["addressList"] = addressList

    if request.method == 'POST':
       addressID =  request.POST.get('addressID')

       if int(isUpdate) == 0:
           return HttpResponseRedirect("/partial_estimate/"+ str(wo.id) + "/" + isPartial + "/1/" + str(addressID))
       else:
           return HttpResponseRedirect("/update_estimate_address/"+ str(wo.id) + "/" + str(addressID) + "/" + str(isUpdate))              



    return render(request, "select_billing_address.html", context)

@login_required(login_url='/home/')
def update_estimate_address(request, woID, addressID, estimateID):
    context ={}
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = woID).first()
    
    addressO = billingAddress.objects.filter(id = addressID).first()
    
    est = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()

    if est:
        est.zipCode =addressO.zipCode
        est.state = addressO.state
        est.city = addressO.city
        est.address = addressO.address
        est.description = addressO.description
        est.save()


    inv = woInvoice.objects.filter(woID = wo, estimateNumber = estimateID).first()

    if inv:
        inv.zipCode =addressO.zipCode
        inv.state = addressO.state
        inv.city = addressO.city
        inv.address = addressO.address
        inv.description = addressO.description
        inv.save()

    return HttpResponseRedirect("/update_estimate/"+ str(wo.id) + "/" + str(estimateID))   

@login_required(login_url='/home/')
def billing_address_list(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    context["addressList"] = billingAddress.objects.all()
    context["emp"]= emp
    return render(request, "billing_address_list.html", context)

@login_required(login_url='/home/')
def create_billing_address(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    form = billingAddressForm(request.POST or None)
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/billing_address_list/")
         
    context['form']= form
    context["emp"]=emp
    return render(request, "create_billing_address.html", context)

@login_required(login_url='/home/')
def update_billing_address(request, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(billingAddress, id = id)
 
    form = billingAddressForm(request.POST or None, instance = obj)
 
    if form.is_valid():
        form.save()
        return HttpResponseRedirect("/billing_address_list/")

    context["form"] = form
    
    return render(request, "create_billing_address.html", context)


@login_required(login_url='/home/')
def invoice_daily_report(request):
    context ={}

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["emp"] = emp


    

    #Getting the locations assigned to the Actual User
    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append(emp.Location.LocationID)

    for i in locaList:
        locationList.append(i.LocationID.LocationID)

    

    if request.method == 'POST':       
       dateSelected =  request.POST.get('date')
       dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()

       if emp.is_superAdmin:
           result = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'),created_date__day=datetime.strftime(dateS, '%d'))
       else:
           result = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'),created_date__day=datetime.strftime(dateS, '%d'), woID__Location__LocationID__in = locationList)

       context["woInvoice"] = result
       context["dateSelected"] =  dateS
       
    
    opType = "Access Option"
    opDetail = "Invoice Daily Report"
    logInAuditLog(request, opType, opDetail)


    return render(request, "invoice_daily_report.html", context)

@login_required(login_url='/home/')
def invoice_monthly_report(request):
    context ={}

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["emp"] = emp

    opType = "Access Option"
    opDetail = "Invoice Monthly Report"
    logInAuditLog(request, opType, opDetail)

    #Getting the locations assigned to the Actual User

    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                        
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)


    if request.method == 'POST':       
       dateSelected =  request.POST.get('date')
       dateSelected2 = request.POST.get('date2')
       dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
       dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()
       status = request.POST.get('status')

       #result = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'))
       if status == "0":
            result = woInvoice.objects.filter(created_date__range=[dateS, dateS2], woID__Location__LocationID__in = locationList)
       else:
            result = woInvoice.objects.filter(created_date__range=[dateS, dateS2], woID__Status = status, woID__Location__LocationID__in = locationList)
       
       resultList = []
        # Calculating Labor

       for i in result:
            totalLabor = 0
            totalMaterials = 0
            totaPO = 0
            per_expenses = 0
            balance= 0
            
            authBilling = authorizedBilling.objects.filter(invoice = i.invoiceNumber)

            for j in authBilling:
                totalLabor += validate_decimals(j.total) 

            internal = internalPO.objects.filter(woID = i.woID, nonBillable = False, invoice = str(i.invoiceNumber))
           
            for data in internal:                
                if data.total != None and data.total != "":                    
                    if data.isAmountRounded:
                        amount = int(round(float(str(data.total))))  
                    else:
                        amount = Decimal(str(data.total)) 
                else:
                    amount = 0

                # Sum all the Internal PO's
                totaPO += amount
            

            if totaPO > 0:
                totalMaterials = totaPO + (totaPO * Decimal(str(0.10)))


            #External Production
            """extProduction = externalProduction.objects.filter(woID = i.woID)
            epTotal = 0 
            for ep in extProduction:
                epTotal += validate_decimals(ep.total_invoice)
            """

            if  validate_decimals(i.woID.POAmount) > 0:
                per_expenses =  ((validate_decimals(totalLabor)  + validate_decimals(totalMaterials))/ validate_decimals(i.woID.POAmount) ) * 100
            else: 
                per_expenses = 0

            balance = validate_decimals(i.woID.POAmount) - (validate_decimals(totalLabor)  + validate_decimals(totalMaterials) )

            resultList.append({'woID': i.woID,'estimateNumber': i.estimateNumber,'invoiceNumber': i.invoiceNumber,'total': i.total,'zipCode' : i.zipCode,
                               'state' : i.state, 'city' : i.city,'address' : i.address,'description' : i.description,
                                'Status' : i.Status, 'is_partial' : i.is_partial, 'created_date' : i.created_date,'createdBy' : i.createdBy, 
                                'labor': validate_decimals(totalLabor),'materials': validate_decimals(totalMaterials), 'per_expenses': validate_decimals(per_expenses), 'balance': balance })
            

       context["woInvoice"] = resultList
       context["dateSelected"] =  dateS
       context["dateSelected2"] =  dateS2
       context["statusSelected"] =  status
       

    return render(request, "invoice_monthly_report.html", context)

@login_required(login_url='/home/')
def payroll_employee_report(request, empID):
    context ={}

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    per = period.objects.filter(status__in=(1,2)).first()


    #Getting the locations assigned to the Actual User
    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                    
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)


    locationList2 = Locations.objects.filter( LocationID__in = locationList)
    

    context["per"] = per
    context["emp"] = emp
    context["location"] = locationList2

    opType = "Access Option"
    opDetail = "Invoice Monthly Report"
    logInAuditLog(request, opType, opDetail)

    employeeID = empID
    context["post"] = False


    



    if request.method == 'POST':       
       dateSelected =  request.POST.get('date')
       dateSelected2 = request.POST.get('date2')
       dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
       dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()       
       location = request.POST.get('location')
       employeeID = request.POST.get('employee')
                         
       
       

       """resultList.append({'woID': i.woID,'estimateNumber': i.estimateNumber,'invoiceNumber': i.invoiceNumber,'total': i.total,'zipCode' : i.zipCode,
                            'state' : i.state, 'city' : i.city,'address' : i.address,'description' : i.description,
                            'Status' : i.Status, 'is_partial' : i.is_partial, 'created_date' : i.created_date,'createdBy' : i.createdBy, 
                            'labor': validate_decimals(totalLabor),'materials': validate_decimals(totalMaterials), 'per_expenses': validate_decimals(per_expenses), 'balance': balance })"""
        
       resultList = get_summary_by_employee(request,dateSelected, dateSelected2, empID, location, 0)

       context["woInvoice"] = resultList
       context["dateSelected"] =  dateS
       context["dateSelected2"] =  dateS2
       context["locationSelected"] =  location
       context["post"] = True

    if employeeID != "0":
        empSel = Employee.objects.filter(employeeID = employeeID ).first()
        
        if empSel:
            context["selectedEmployeeID"] = employeeID
            context["selectedEmployeeName"] = empSel.first_name + " " + empSel.last_name
    else:
        context["selectedEmployeeName"] = ""
        context["selectedEmployeeID"] = 0
       

    return render(request, "payroll_employee_report.html", context)


@login_required(login_url='/home/')
def get_summary_by_employee(request,dateSelected, dateSelected2, empID, LocationID, Tipo):  

    resultList = []

    emp = Employee.objects.filter(user__username__exact = request.user.username).first() 

    #Getting the locations assigned to the Actual User
    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                    
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)

    if LocationID == "0":
        loca = Locations.objects.filter(LocationID__in = locationList).order_by("LocationID")
    else:        
        loca = Locations.objects.filter(LocationID = LocationID)
        
    locList = []
    for empLoc in loca:
        locList.append(empLoc.LocationID)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Summary', cell_overwrite_ok = True) 

    # Sheet header, first row
    row_num = 7

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color light_blue;')

    font_style =  xlwt.XFStyle()                    


    columns = ['Location', 'Date', 'Eid', 'Name', 'RT','OT','DT','TT','RT$','OT$','Bonus', 'Production','own vehicle', 'on call', 'payroll','Supervisor','PID','Address']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 

    
    try:

        dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
        dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()

        per = period.objects.filter(id = 31).first()
        dailyList = Daily.objects.filter(day__range=[dateS, dateS2] , Location__LocationID__in = locList).order_by('Location')
        

        for item in dailyList:        
        
            if empID == "0":               
                demp = DailyEmployee.objects.filter(DailyID=item ).order_by()    
            else:
                empL = Employee.objects.filter(employeeID = empID).first()
                demp = DailyEmployee.objects.filter(DailyID=item, EmployeeID = empL).order_by()    

            empLines = 0    
            

            for i in demp:
                itemProd = 0
                rtPrice = 0
                otPrice = 0
                dtPrice = 0     
                ttp = 0
                ov = 0
                bonus = 0
                on_call = 0
                InvoiceGeneral = 0
                
            
                if validate_decimals(i.payout) > 0:                
                    row_num += 1
                    

                    ws.write(row_num,0,item.Location.name, font_style)
                    ws.write(row_num,1,item.day.strftime("%m/%d/%Y"), font_style)
                    ws.write(row_num,2,i.EmployeeID.employeeID, font_style)
                    ws.write(row_num,3,i.EmployeeID.last_name + ' ' +i.EmployeeID.first_name, font_style)

                    itemProd = DailyItem.objects.filter(DailyID = i.DailyID).count()
                    
                    if itemProd <= 0:                    
                
                        ws.write(row_num,4,validate_print_decimals(i.regular_hours), font_style)
                        ws.write(row_num,5,validate_print_decimals(i.ot_hour), font_style)
                        ws.write(row_num,6,validate_print_decimals(i.double_time), font_style)
                        ws.write(row_num,7,validate_print_decimals(i.total_hours), font_style)

                        if validate_decimals(i.EmployeeID.hourly_rate) != None:
                            rtPrice = (validate_decimals(i.regular_hours) * float(validate_decimals(i.EmployeeID.hourly_rate)))
                            otPrice = ((validate_decimals(i.ot_hour) * (float(validate_decimals(i.EmployeeID.hourly_rate))*1.5)))
                            dtPrice = ((validate_decimals(i.double_time) * (float(validate_decimals(i.EmployeeID.hourly_rate))*2)))

                            ws.write(row_num,8,validate_print_decimals(rtPrice), font_style)
                            ws.write(row_num,9,validate_print_decimals(otPrice + dtPrice), font_style)
                        else:
                            ws.write(row_num,8,'', font_style)
                            ws.write(row_num,9,'', font_style)
                    else:
                        ws.write(row_num,4,'', font_style)
                        ws.write(row_num,5,'', font_style)
                        ws.write(row_num,6,'', font_style)
                        ws.write(row_num,7,'', font_style)
                        ws.write(row_num,8,'', font_style)
                        ws.write(row_num,9,'', font_style)

                    ws.write(row_num,10,validate_print_decimals(i.bonus), font_style)
                    if itemProd > 0:  
                        di = DailyItem.objects.filter(DailyID = i.DailyID)          
                        t = 0
                        for j in di:
                            t += validate_decimals(j.total)

                        if validate_decimals(item.own_vehicle) != None:
                            ov = validate_decimals((((t * validate_decimals(item.own_vehicle)) / 100) * validate_decimals(i.per_to_pay)) /100)
                        else:
                            ov = 0

                        ttp = (t * validate_decimals(i.per_to_pay)) /100
                        ws.write(row_num,round(11,2),validate_print_decimals(ttp), font_style)
                        ws.write(row_num,12,validate_print_decimals(ov), font_style)
                    else:
                        ws.write(row_num,11,'', font_style)
                        ws.write(row_num,12,'', font_style)

                    if validate_decimals(i.bonus) != None:
                        bonus = validate_decimals(i.bonus)
                    
                    if validate_decimals(i.on_call) != None:
                        on_call = validate_decimals(i.on_call)


                    payTotal = validate_decimals(i.payout) #validate_decimals(rtPrice + otPrice + dtPrice + bonus + ttp + ov + on_call)
                    ws.write(row_num,13,validate_print_decimals(i.on_call), font_style)
                    ws.write(row_num,14,validate_print_decimals(payTotal), font_style)
                    if item.woID.WCSup != None:
                        superV = item.woID.WCSup.last_name + ' ' + item.woID.WCSup.first_name
                        ws.write(row_num,15,item.woID.WCSup.last_name + ' ' + item.woID.WCSup.first_name, font_style)
                    else:
                        superV = ""

                    ws.write(row_num,16,item.woID.prismID, font_style)
                    ws.write(row_num,17,item.woID.JobAddress, font_style)

                    empLines += 1
                    
                    # se agregan las columnas de items
                    if empLines == 1:
                        items = DailyItem.objects.filter(DailyID = i.DailyID)
                        col_item =  0
                        itemNumber = 0

                        for z in items:                            
                            col_item += 1
                            itemNumber += 1
                            try:
                                ws.write(7,17 + col_item,'Item'+str(itemNumber), font_title)   
                                ws.write(7,18 + col_item,'Qty'+str(itemNumber), font_title)                                                         
                            except Exception as e:
                                ws.write(7,17 + col_item,'Item', font_title)                             
                            
                            ws.write(row_num,17 + col_item,z.itemID.item.itemID, font_style)
                        
                            col_item += 1                                          
                            
                            ws.write(row_num,17 + col_item,z.quantity, font_style)                            
                           

                    resultList.append({'Location':item.Location.name,'Date':item.day.strftime("%m/%d/%Y"),'Eid':i.EmployeeID.employeeID,
                                       'Name':i.EmployeeID.last_name + ' ' +i.EmployeeID.first_name,
                                       'Production':validate_print_decimals(ttp),
                                       'Payroll':validate_print_decimals(payTotal),
                                       'Supervisor':superV,
                                       'PID':item.woID.prismID,
                                       'Address':item.woID.JobAddress})
        
        sumItem = 0            
        for x in dailyList:

            if empID == "0":
                items = DailyItem.objects.filter(DailyID = x).count()                           
            else:
                
                empIt = DailyEmployee.objects.filter(DailyID = x, EmployeeID__employeeID = empID).first()

                if empIt:
                    items = DailyItem.objects.filter(DailyID = x).count()
                else:
                    items = 0

            if items > sumItem:
                    sumItem = items            
       
        ws.write(7,18 + sumItem*2,'Item Totals', font_title)   
        ws.write(7,19 + sumItem*2,'Invoice', font_title)                   
                
                 
        

        row_num=7
        
        for x in dailyList:
            if empID == "0":               
                demp = DailyEmployee.objects.filter(DailyID=x ).order_by()    
            else:
                empL = Employee.objects.filter(employeeID = empID).first()
                demp = DailyEmployee.objects.filter(DailyID=x, EmployeeID = empL).order_by()    

            #demp = DailyEmployee.objects.filter(DailyID=x).order_by()    
            empLines = 0    

            for y in demp:
                empLines += 1
            
                if validate_decimals(y.payout) > 0:                
                    row_num += 1
                    if empLines == 1:
                        items = DailyItem.objects.filter(DailyID = x)
                        sumQty = 0
                        sumInvoice = 0
                        for z in items:
                            if validate_decimals(z.price) != None:
                                lineInv = validate_decimals(z.quantity) * validate_decimals(z.price)
                            else:
                                lineInv = 0
                            sumInvoice += validate_decimals(lineInv)
                            sumQty += validate_decimals(z.quantity)

                        if sumQty > 0:
                            InvoiceGeneral += validate_decimals(sumInvoice)
                            ws.write(row_num,18 + sumItem*2,validate_decimals(sumQty), font_style)   
                            ws.write(row_num,19 + sumItem*2,validate_decimals(sumInvoice), font_style)     
        

        ws.col(0).width = 3000
        ws.col(2).width = 1500
        ws.col(3).width = 5000
        ws.col(4).width = 1000
        ws.col(5).width = 1000
        ws.col(6).width = 1000
        ws.col(7).width = 1000
        ws.col(8).width = 1000
        ws.col(9).width = 1000
        ws.col(10).width = 1700                                      
        ws.col(11).width = 3500
        ws.col(12).width = 3000
        ws.col(13).width = 1700
        ws.col(14).width = 2200
        ws.col(15).width = 5000
        ws.col(17).width = 11500
        
    except Exception as e:
        ws.write(0,0,str(e), font_style)        
    
    

    if Tipo == 0:
        return resultList
    

    filename = 'Payroll Summary ' + str(empID) + '.xls'    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response
    #else:
    #    return summaryList



@login_required(login_url='/home/')
def employee_list_pay_report(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    LocID = 1  
    
    context = {}    
    context["emp"] = emp    
    context["selectedLocation"] = LocID
    employeeList = Employee.objects.filter(is_active = True)
    context["employeeList"] = employeeList 

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    return render(request, "employee_list_pay_report.html", context)


@login_required(login_url='/home/')
def get_daily_report(request, dateSelected):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('daily-report', cell_overwrite_ok = True) 

    

    # Sheet header, first row
    row_num = 4

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color gray25;')

    
    font_style =  xlwt.XFStyle()              

    font_title2 = xlwt.easyxf('font: bold on, color black;\
                                align: horiz center;\
                                pattern: pattern solid, fore_color gray25;')
                              
    ws.write_merge(3, 3, 0, 8, 'Daily Report ' + dateSelected ,font_title2)   


    columns = ['Invoice', 'Entered By', 'WC Supervisor', 'Attn To', 'System','Partial / Final','PO', 'PID','Invoice Amount']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 


    #Getting the locations assigned to the Actual User
    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append(emp.Location.LocationID)

    for i in locaList:
        locationList.append(i.LocationID.LocationID)


    dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
    if emp.is_superAdmin:
        ordenes = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'),created_date__day=datetime.strftime(dateS, '%d'))
    else:
        ordenes = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'),created_date__day=datetime.strftime(dateS, '%d'), woID__Location__LocationID__in = locationList)

    for item in ordenes:
        row_num += 1
        ws.write(row_num, 0, item.invoiceNumber, font_style) # at 0 row 0 column 
        ws.write(row_num, 1, item.createdBy, font_style) # at 0 row 0 column 
        if item.woID.WCSup != None:
            ws.write(row_num,2, item.woID.WCSup.first_name + ' ' + item.woID.WCSup.last_name, font_style) # at 0 row 0 column 
        else:
            ws.write(row_num, 2, '',font_style) # at 0 row 0 column 
        ws.write(row_num, 3, '', font_style)
        if item.woID.Location != None:
            ws.write(row_num, 4, item.woID.Location.name, font_style) # at 0 row 0 column 
        else:
             ws.write(row_num, 4, '', font_style) 

        ws.write(row_num, 5, item.woID.JobAddress, font_style) # at 0 row 0 column 
        
        if item.is_partial:
            ws.write(row_num, 5, 'Partial', font_style) 
        else:
            ws.write(row_num, 5, 'Final', font_style) 
        
        

        ws.write(row_num, 6, item.woID.PO, font_style)
        ws.write(row_num, 7, item.woID.prismID, font_style)
        ws.write(row_num, 8, '$' + '{0:,.2f}'.format(validate_decimals(item.total)) , font_style)

    ws.col(1).width = 5000
    ws.col(2).width = 9000
    ws.col(3).width = 6000
    ws.col(4).width = 9000
    ws.col(5).width = 4000
    ws.col(6).width = 6000
    ws.col(7).width = 6000
    ws.col(8).width = 6000

    filename = 'daily report ' + dateSelected + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response

@login_required(login_url='/home/')
def get_monthly_report(request, dateSelected, dateSelected2, status):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()


    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('monthly-report', cell_overwrite_ok = True) 

    
    #Getting the locations assigned to the Actual User
    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                    
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)


    # Sheet header, first row
    row_num = 4

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color gray25;')

    
    font_style =  xlwt.XFStyle()              

    font_title2 = xlwt.easyxf('font: bold on, color black;\
                                align: horiz center;\
                                pattern: pattern solid, fore_color gray25;')

    dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
    dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()
    
                              
    ws.write_merge(3, 3, 0, 13, 'Monthly Report ' + str(datetime.strftime(dateS, '%Y')) + ' - ' + str(datetime.strftime(dateS, '%m')),font_title2)   


    columns = ['Invoice', 'Entered By', 'WC Supervisor', 'Attn To', 'System','Partial / Final','PO', 'PID','Labor','Materials','Labor + Materials','Invoice Amount', 'expenses', 'Balance'  ] 

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
      

    
    #ordenes = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'))
    
    if status == "0":
        ordenes = woInvoice.objects.filter(created_date__range=[dateS, dateS2], woID__Location__LocationID__in = locationList)
    else:
        ordenes = woInvoice.objects.filter(created_date__range=[dateS, dateS2], woID__Status = status, woID__Location__LocationID__in = locationList )
       
    for item in ordenes:
        row_num += 1
        ws.write(row_num, 0, item.invoiceNumber, font_style) # at 0 row 0 column 
        ws.write(row_num, 1, item.createdBy, font_style) # at 0 row 0 column 
        if item.woID.WCSup != None:
            ws.write(row_num,2, item.woID.WCSup.first_name + ' ' + item.woID.WCSup.last_name, font_style) # at 0 row 0 column 
        else:
            ws.write(row_num, 2, '',font_style) # at 0 row 0 column 
        ws.write(row_num, 3, item.address, font_style)
        if item.woID.Location != None:
            ws.write(row_num, 4, item.woID.Location.name, font_style) # at 0 row 0 column 
        else:
             ws.write(row_num, 4, '', font_style) 

        ws.write(row_num, 5, item.woID.JobAddress, font_style) # at 0 row 0 column 
        
        if item.is_partial:
            ws.write(row_num, 5, 'Partial', font_style) 
        else:
            ws.write(row_num, 5, 'Final', font_style) 
        
        



        ws.write(row_num, 6, item.woID.PO, font_style)
        ws.write(row_num, 7, item.woID.prismID, font_style)

        totalLabor = 0
        totalMaterials = 0
        totaPO = 0
        per_expenses = 0
        balance = 0

       

        authBilling = authorizedBilling.objects.filter(invoice = item.invoiceNumber)

        for j in authBilling:
            totalLabor += validate_decimals(j.total) 


        internal = internalPO.objects.filter(woID = item.woID, nonBillable = False, invoice = str(item.invoiceNumber))
        
        for data in internal:                
            if data.total != None and data.total != "":                    
                if data.isAmountRounded:
                    amount = int(round(float(str(data.total))))  
                else:
                    amount = Decimal(str(data.total)) 
            else:
                amount = 0

            # Sum all the Internal PO's
            totaPO += amount
        

        if totaPO > 0:
            totalMaterials = totaPO + (totaPO * Decimal(str(0.10)))


        if  validate_decimals(item.woID.POAmount) > 0:
            per_expenses =  ((validate_decimals(totalLabor)  + validate_decimals(totalMaterials) )/ validate_decimals(item.woID.POAmount) ) * 100
            balance = validate_decimals(item.woID.POAmount) - (validate_decimals(totalLabor)  + validate_decimals(totalMaterials) )
        

        ws.write(row_num, 8, '$' + '{0:,.2f}'.format(validate_decimals(totalLabor)) , font_style)
        ws.write(row_num, 9, '$' + '{0:,.2f}'.format(validate_decimals(totalMaterials)) , font_style)
        ws.write(row_num, 10, '$' + '{0:,.2f}'.format(validate_decimals(totalLabor) + validate_decimals(totalMaterials)) , font_style)

        ws.write(row_num, 11, '$' + '{0:,.2f}'.format(validate_decimals(item.total)) , font_style)
        ws.write(row_num, 12, '{0:,.2f}'.format(validate_decimals(per_expenses)) + '%' , font_style)
        ws.write(row_num, 13, '{0:,.2f}'.format(validate_decimals(balance)) , font_style)

    ws.col(1).width = 5000
    ws.col(2).width = 9000
    ws.col(3).width = 6000
    ws.col(4).width = 9000
    ws.col(5).width = 4000
    ws.col(6).width = 6000
    ws.col(7).width = 6000
    ws.col(8).width = 6000
    ws.col(9).width = 6000
    ws.col(10).width = 6000
    ws.col(11).width = 6000
    ws.col(12).width = 3000
    ws.col(13).width = 6000

    filename = 'Monthly report ' + dateSelected + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response


@login_required(login_url='/home/')
def wo_balance_Report(request):
    context ={}

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()    
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
    context["emp"] = emp

    opType = "Access Option"
    opDetail = "Invoice Monthly Report"
    logInAuditLog(request, opType, opDetail)
    estatus = ""
    loc = ""    

    #Getting the locations assigned to the Actual User
    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                    
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)

    locationList2 = Locations.objects.filter( LocationID__in = locationList)
    context["location"]=locationList2

    if request.method == 'POST':       
    
       estatus = request.POST.get('status')
       loc = request.POST.get('location') 

       if loc == None or loc =="":
            loc = "0"
       locationObject = Locations.objects.filter(LocationID=loc).first()
      
       if estatus != "0" and loc != "0":
            result = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )     
       else:
            if estatus != "0":
                result = workOrder.objects.filter(Status = estatus, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 
            else:
                result = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 
       
       resultList = []
        # Calculating Labor

       for i in result:
            #Payroll Detail
            dailys = Daily.objects.filter(woID = i)

            empTotal = 0
            empBalance = 0
            for item in dailys:
                dailyEmp = DailyEmployee.objects.filter(DailyID = item)

                for empI in dailyEmp:
                    empTotal += validate_decimals(empI.payout)

                    if empI.invoice == None:
                        empBalance += validate_decimals(empI.payout)

            
            #Internal PO Detail
            internalpo = internalPO.objects.filter(woID=i)
            poTotal = 0
            poBalance = 0
            for po in internalpo:
                poTotal += validate_decimals(po.total)

                if po.invoice == None:
                    poBalance += validate_decimals(po.total)

            resultList.append({'woID': i,'POAmount': i.POAmount,'Payroll': empTotal,'PendingPayroll': empBalance,'internalPO' : poTotal,'PendingInternalPO': poBalance, 
                             'Status' : i.Status, 'Location':i.Location, 'supervisor': i.WCSup ,'address' : i.JobAddress })
    

       context["woInvoice"] = resultList
       context["selectEstatus"] =  estatus
       context["selectLoc"]=loc

    return render(request, "wo_balance_report.html", context)


@login_required(login_url='/home/')
def get_balance_report(request, status, location):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()  


    #Getting the locations assigned to the Actual User
    if emp.is_superAdmin:
        locationList = Locations.objects.all().values_list('LocationID', flat=True)
    else:    
        locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                    
        locationList = []
        locationList.append(emp.Location.LocationID)

        for i in locaList:
            locationList.append(i.LocationID.LocationID)


    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('monthly-report', cell_overwrite_ok = True) 

    locationObject = Locations.objects.filter(LocationID=location).first()

    # Sheet header, first row
    row_num = 4

    font_title = xlwt.XFStyle()
    font_title.font.bold = True
    font_title = xlwt.easyxf('font: bold on, color black;\
                     borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;\
                     pattern: pattern solid, fore_color gray25;')

    
    font_style =  xlwt.XFStyle()              

    font_title2 = xlwt.easyxf('font: bold on, color black;\
                                align: horiz center;\
                                pattern: pattern solid, fore_color gray25;')
    
                              
    ws.write_merge(3, 3, 0, 9, 'WO Balance Report ',font_title2)   


    columns = ['WO ID', 'PO Amount', 'Payroll', 'Pending Payroll Balance', 'Internal PO','Pending Internal PO Balance','Status', 'Location','Supervisor','Address' ] 

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 


    if status != "0" and location != "0":
        result = workOrder.objects.filter(Status = status, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )     
    else:
        if status != "0":
            result = workOrder.objects.filter(Status = status, Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 
        else:
            result = workOrder.objects.filter(Location__LocationID__in = locationList).exclude(linkedOrder__isnull = False, uploaded = False ) 
    
    for i in result:
        #Payroll Detail
        dailys = Daily.objects.filter(woID = i)

        empTotal = 0
        empBalance = 0
        for item in dailys:
            dailyEmp = DailyEmployee.objects.filter(DailyID = item)

            for empI in dailyEmp:
                empTotal += validate_decimals(empI.payout)

                if empI.invoice == None:
                    empBalance += validate_decimals(empI.payout)

        
        #Internal PO Detail
        internalpo = internalPO.objects.filter(woID=i)
        poTotal = 0
        poBalance = 0
        for po in internalpo:
            poTotal += validate_decimals(po.total)

            if po.invoice == None:
                poBalance += validate_decimals(po.total)
      
        row_num += 1
        ws.write(row_num, 0, i.prismID + " - " + i.workOrderId  + " - " + i.PO, font_style) # at 0 row 0 column 
        ws.write(row_num, 1, '$' + '{0:,.2f}'.format(validate_decimals(i.POAmount)) , font_style)
        ws.write(row_num, 2, '$' + '{0:,.2f}'.format(validate_decimals(empTotal)) , font_style)
        ws.write(row_num, 3, '$' + '{0:,.2f}'.format(validate_decimals(empBalance)) , font_style)
        ws.write(row_num, 4, '$' + '{0:,.2f}'.format(validate_decimals(poTotal)) , font_style)
        ws.write(row_num, 5, '$' + '{0:,.2f}'.format(validate_decimals(poBalance)) , font_style)
       
        # at 0 row 0 column 
        
        if i.Status == "1": 
            ws.write(row_num, 6, "Not Started", font_style)       
        elif i.Status == "2":   
            ws.write(row_num, 6, "Work in Progress", font_style)                                           
        elif i.Status == "3":   
            ws.write(row_num, 6, "Pending Docs", font_style)  
        elif i.Status == "4":   
            ws.write(row_num, 6, "Pending Revised WO", font_style)  
        elif i.Status == "5":   
            ws.write(row_num, 6, "Invoiced", font_style)  
        elif i.Status == "6":   
            ws.write(row_num, 6, "Transferred", font_style)                                         
        else:
            ws.write(row_num, 6, "", font_style)                                         
                                                         
        
        if i.Location != None:
            ws.write(row_num, 7, i.Location.name, font_style) # at 0 row 0 column 
        else:
            ws.write(row_num, 7, '', font_style) 

        if i.WCSup != None:
            ws.write(row_num, 8, i.WCSup.first_name + ' ' + i.WCSup.last_name, font_style) # at 0 row 0 column 
        else:
            ws.write(row_num, 8, '', font_style) 
        
        ws.write(row_num, 9, str(i.JobAddress), font_style) # at 0 row 0 column 

    ws.col(0).width = 9000
    ws.col(1).width = 6000
    ws.col(2).width = 6000
    ws.col(3).width = 6000
    ws.col(4).width = 6000
    ws.col(5).width = 6000
    ws.col(6).width = 6000
    ws.col(7).width = 8000
    ws.col(8).width = 9000
    ws.col(9).width = 14000
    ws.col(10).width = 6000
    ws.col(11).width = 6000
    ws.col(12).width = 3000
    ws.col(13).width = 6000

    filename = 'WO Balance report.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response

@login_required(login_url='/home/')
def wo_comment_log(request, woID, isSupervisor):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 

    wo = workOrder.objects.filter(id=woID).first()
    form = woCommentLogForm(request.POST or None, initial={'woID': wo})
                            
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/order_detail/" + str(woID) + "/" + isSupervisor)
         
    context['form']= form
    context["emp"]=emp
    return render(request, "wo_comment_log.html", context)

def get_wo_comment_log(request, id):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = id).first()

    wo_log = woCommentLog.objects.filter(woID = wo).order_by('created_date')
    context["log"] = wo_log

    
    return render(request, "get_wo_comment_log.html", context)



@login_required(login_url='/home/')
def pending_internal_po(request, id, isPartial, isUpdate):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}    
   
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = id).first()

    intPO = internalPO.objects.filter(woID = wo, Status=1)
    
    poList = []

    contador = 0
    for i in intPO:
        if validate_decimals(i.total) <= 0:
            contador = contador + 1
            poList.append({'poNumber':i.poNumber, 'Product':i.product, 'Quantity': i.quantity})
    
    if contador == 0:
        return HttpResponseRedirect('/select_billing_address/' + str(id) + '/' + str(isPartial) + '/' + str(isUpdate)) 

 
    if request.method == 'POST':        
        return HttpResponseRedirect('/select_billing_address/' + str(id) + '/' + str(isPartial) + '/' + str(isUpdate)) 

    context["poList"] = poList

    return render(request, "pending_internal_po.html", context)




### General Functions
@login_required(login_url='/home/')
def vendorSubcontrator(request):
    vendorList = vendor.objects.filter(is_active = True).only("id", "name").order_by("name")
    subCList = subcontractor.objects.filter(is_active = True).only("id", "name").order_by("name")
    

    vcList = []


    for v in vendorList:
        vcList.append({'id': "V" + str(v.id), 'name': v.name} )

    
    for s in subCList:
       vcList.append({'id': "S" + str(s.id), 'name': s.name} )


    sort_list = sorted(vcList, key=lambda x: x["name"])

    return sort_list


@login_required(login_url='/home/')
def vendor_subcontractor_list(request,woID, tipoOp, id):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    LocID = 1  

    
    context = {}    
    context["emp"] = emp    
    context["selectedLocation"] = LocID
    context["vendorList"] = vendorSubcontrator(request)
    context["woID"] = woID
    context["id"] = id
    context["tipoOp"] = tipoOp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    return render(request, "vendor_subcontractor_list.html", context)



"""def date_difference(orders):   
    
    day_diff = []
    date_format = "%Y-%m-%d"
    today = datetime.now().date()

    for i in orders:
        
        if validate_decimals(i.Status) >= 2 and validate_decimals(i.Status) <=4:   
            try:
                date_format = "%Y-%m-%d"
                a = datetime.strptime(str(datetime.now().date()), date_format)
                #a = datetime.now().date()
                b = datetime.strptime(i.UploadDate[0:10], date_format)
                delta = a - b
                days_overdue = delta.days

                #getting the WO
                wo = workOrder.objects.filter(id = i.id).first()                
                partial_inv = woInvoice.objects.filter(woID = wo).count()

            except Exception as e:
                days_overdue = 0
                partial_inv = 0
        else:
            days_overdue = 0
            partial_inv = 0

        day_diff.append({'id':i.id, 'days': days_overdue, 'prismID': i.prismID, 'workOrderId': i.workOrderId, 'PO': i.PO, 'POAmount':i.POAmount, 'Status': i.Status,  'Location':i.Location, 'WCSup': i.WCSup, 'created_date': i.created_date, 'UploadDate':i.UploadDate, 'IssuedBy':i.IssuedBy, 'JobName': i.JobName, 'JobAddress': i.JobAddress, 'partial_inv': partial_inv, 'Comments': i.Comments  })
    
    return day_diff
    """

from django.db.models import Prefetch, Count

def date_difference(orders):
    """Optimized version with prefetch_related to avoid N+1 queries"""
    
    # Prefetch related invoices using the correct reverse relation name
    orders = orders.prefetch_related('woinvoice_set')
    
    day_diff = []
    date_format = "%Y-%m-%d"
    today = datetime.now().date()
    
    for i in orders:
        if validate_decimals(i.Status) in (2,3,4,6,7,8):
            try:
                if i.UploadDate:
                    upload_date = datetime.strptime(i.UploadDate[0:10], date_format).date()
                    days_overdue = (today - upload_date).days
                else:
                    days_overdue = 0
                
                # Count invoices from prefetched data (no DB query!)
                partial_inv = i.woinvoice_set.all().count()
            except Exception as e:
                days_overdue = 0
                partial_inv = 0
        else:
            days_overdue = 0
            partial_inv = 0
        
        day_diff.append({
            'id': i.id,
            'days': days_overdue,
            'prismID': i.prismID,
            'workOrderId': i.workOrderId,
            'PO': i.PO,
            'POAmount': i.POAmount,
            'Status': i.Status,
            'Location': i.Location,
            'WCSup': i.WCSup,
            'created_date': i.created_date,
            'UploadDate': i.UploadDate,
            'IssuedBy': i.IssuedBy,
            'JobName': i.JobName,
            'JobAddress': i.JobAddress,
            'partial_inv': partial_inv,
            'Comments': i.Comments
        })
    
    return day_diff



@login_required(login_url='/home/')    
def update_item_price_202503(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    fecha = datetime.strptime("2025-03-03", '%Y-%m-%d').date()
    createdItems = 0
    createdItemPrices = 0

    try:        
        
        itemCatalog = item.objects.filter(is_new = False)

        updated = 0
        for it in itemCatalog:
            
            newItem = item (
                itemID = it.itemID + "+",
                name = it.name,
                description = it.description,
                is_active = it.is_active,
                is_new = True,
                created_date = fecha,
                createdBy = "admin"
            )

            newItem.save()
            createdItems += 1

            itemPriceCatalog = itemPrice.objects.filter(item = it)

            for ip in itemPriceCatalog:
                newItemPrice = itemPrice (
                    item = newItem,   
                    location = ip.location,
                    pay_perc = ip.pay_perc,                    
                    price = ip.price,
                    emp_payout = ip.emp_payout,
                    rate = ip.rate
                )   

                newItemPrice.save()

                createdItemPrices += 1
        
        

        return render(request,'landing.html',{ 'message': str(createdItems) + ' Items Created Successfully...  ' + str(createdItemPrices) + 'Item Prices Created Successfully', 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})


@login_required(login_url='/home/')    
def update_linked_orders(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    try:        
        
        linkedOrders = workOrder.objects.filter(linkedOrder__isnull = False)
        updated = 0
        for lo in linkedOrders:
            
            if lo.linkedOrder != "updated":
                manOrder = workOrder.objects.filter(id=lo.id).first()
                
                order = workOrder.objects.filter(id=manOrder.linkedOrder).first()
                
                order.Status = manOrder.Status
                order.Location = manOrder.Location
                order.save()
        
                #Se traslada produccion si la hay a la nueva orden
                
                prod = Daily.objects.filter(woID = manOrder)
                
                for p in prod:
                    temProd = Daily.objects.filter(id = p.id).first()
                    temProd.woID = order
                    temProd.save()
                
                #Se traslada internal PO
                
                internal = internalPO.objects.filter(woID = manOrder)
                
                for i in internal:
                    temInternal = internalPO.objects.filter(id = i.id).first()
                    temInternal.woID = order
                    temInternal.save()
                    
                #Se traslada external Production
                
                external = externalProduction.objects.filter(woID = manOrder)
                
                for e in external:
                    temExternal = externalProduction.objects.filter(id = e.id).first()
                    temExternal.woID = order
                    temExternal.save()
                
                updated += 1    
                
        
        

        return render(request,'landing.html',{ 'message':str(updated) + ' Orders Linked Successfully', 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})

@login_required(login_url='/home/')
def list_linked_orders(request):
    locationList = Locations.objects.all()
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    estatus = "0"
    loc = "0"
    
    context={}

    if request.method == "POST":
        estatus = request.POST.get('status')
        loc = request.POST.get('location') 
        if loc == None or loc =="":
            loc = "0"
        locationObject = Locations.objects.filter(LocationID=loc).first()
    
    context["selectEstatus"] = estatus    
    context["emp"]=emp
    context["location"]=locationList
    context["per"]=per    
    context["selectLoc"]=loc

    if request.user.is_staff:        
        if estatus == "0" and loc == "0":    
            orders = workOrder.objects.filter(linkedOrder__isnull = False)  
        else:
            if estatus != "0" and loc != "0":
                orders = workOrder.objects.filter(Status = estatus, Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  
            else:
                if estatus != "0":
                    orders = workOrder.objects.filter(Status = estatus).exclude(linkedOrder__isnull = False, uploaded = False )  
                else:
                    orders = workOrder.objects.filter(Location = locationObject).exclude(linkedOrder__isnull = False, uploaded = False )  
        context["orders"]=orders

        context["day_diff"]=date_difference(orders)

        return render(request,'order_list.html',context)

    return render(request,'order_linked_list.html',context)


@login_required(login_url='/home/')
def update_item_payout(request):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    

    try:        
        
        itemProduction = DailyItem.objects.all()
        
        updated = 0
        diff = ""
        for prod in itemProduction:           
            
            current = DailyItem.objects.filter(id = prod.id).first()
            if current.emp_payout == None or current.emp_payout == 0:
                current.emp_payout = current.total / current.quantity
                current.price = prod.itemID.price
                current.save()               
                updated += 1    
                
            if prod.itemID.emp_payout != current.emp_payout:
                diff = diff +  prod.itemID.item.itemID + "|" + str(prod.itemID.location.LocationID) + ","
        

        return render(request,'landing.html',{ 'message':str(updated) + ' Items updated Successfully.... Detail:  ' + diff, 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})

@login_required(login_url='/home/')
def update_emp_payout(request):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    
    try:
        #Getting all Dailys     
        dailyObj = Daily.objects.all()
        updated = 0
        
        for crew in dailyObj:
            
            itemCount = 0
            itemSum = 0
            
            itemCount = DailyItem.objects.filter(DailyID = crew).count()
            
            if itemCount > 0:            
                itemList = DailyItem.objects.filter(DailyID = crew)

                for iteml in itemList:
                    itemSum += iteml.total 
                    
            if crew.own_vehicle != None:
                ovp = (itemSum * crew.own_vehicle) / 100
                itemSum += ovp

            empList = DailyEmployee.objects.filter(DailyID = crew)
            
            for empl in empList:
                rt_pay = 0
                ot_pay = 0
                dt_pay = 0
                empRate = 0
                production = 0

                empD = DailyEmployee.objects.filter(id = empl.id).first()
                
                #updatating Work Hours
                empD2 = DailyEmployee.objects.filter(id = empl.id).first()                
                startTime = validate_decimals(empD2.start_time)
                endTime = validate_decimals(empD2.end_time)
                lunch_startTime = validate_decimals(empD2.start_lunch_time)
                lunch_endTime = validate_decimals(empD2.end_lunch_time)

                empD2.total_hours, empD2.regular_hours,empD2.ot_hour, empD2.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)  
                empD2.save()
                
                if itemCount > 0:                   
                    production = validate_decimals(((itemSum * empD.per_to_pay) / 100))
                else: 
                    if validate_decimals(empD.regular_hours) > 0  and validate_decimals(empD.payout) > 0 and validate_decimals(empD.on_call) == 0 and validate_decimals(empD.bonus) == 0:
                        empRate = validate_decimals(empD.payout / empD.regular_hours) 
                    elif validate_decimals(empD.regular_hours) > 0  and validate_decimals(empD.payout) > 0  and (validate_decimals(empD.on_call) != 0 or validate_decimals(empD.bonus) != 0): 
                        empRate = validate_decimals((empD.payout - validate_decimals(empD.on_call) - validate_decimals(empD.bonus)) / empD.regular_hours)         
                    elif empD.EmployeeID.hourly_rate != None: 
                        empRate = validate_decimals(empD.EmployeeID.hourly_rate)
                    else:
                        empRate = 0

                    rt_pay = (empD.regular_hours * empRate)
                    ot_pay = (empD.ot_hour * (empRate * 1.5))
                    dt_pay = (empD.double_time * (empRate * 2))
                
                if empD.production == None:
                    empD.rt_pay = rt_pay
                    empD.ot_pay = ot_pay
                    empD.dt_pay = dt_pay
                    empD.emp_rate = empRate                
                    empD.production = production
                    empD.save()    
            
            
                updated += 1
                
            
        return render(request,'landing.html',{ 'message':str(updated) + ' Items updated Successfully.... Detail:  ' , 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})

@login_required(login_url='/home/')
def update_estimate_closed(request):
    
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()
    
    updated = 0
    
    try:
        estimateList = woEstimate.objects.filter(Status = 3 )
       
        for eList in estimateList:
            updated += 1
            invoiceO = woInvoice.objects.filter(woID = eList.woID, estimateNumber = eList.estimateNumber)
            if invoiceO:
                stat = 2
            else:
                stat = 1

            eList.Status = stat
            eList.save()

            
        return render(request,'landing.html',{ 'message':str(updated) + ' Estimates updated Successfully.... Detail:  ' , 'alertType':'success','emp':emp, 'per':per})
    except Exception as e:
        return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})
    

@login_required(login_url='/home/')
def update_total_invoice(request):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()

    updated = 0
    #try:

    invoiceList = woInvoice.objects.all()

    
    for eList in invoiceList:
        updated += 1
        
        calculate_invoice_total(request, eList.woID.id,eList.invoiceNumber)
        
    return render(request,'landing.html',{ 'message':str(updated) + ' Estimates updated Successfully.... Detail:  ' , 'alertType':'success','emp':emp, 'per':per})
    #except Exception as e:
        #return render(request,'landing.html',{'message':'Somenthing went Wrong!' + str(e), 'alertType':'danger','emp':emp, 'per': per})
    


@login_required(login_url='/home/')
def update_pending_invoice(request):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    per = period.objects.filter(status__in=(1,2)).first()


    woInvoices = woInvoice.objects.filter(invoiceNumber__gte = 64676, invoiceNumber__lte = 64723 )

    for inv in woInvoices:
        wo = inv.woID
        invoiceID = inv.invoiceNumber
        estimateID = inv.estimateNumber

        #Update dailyItems
        dailyI = DailyItem.objects.filter(DailyID__woID = wo, estimate = estimateID)

        for i in dailyI:
            dItem = DailyItem.objects.filter(id = i.id).first()

            dItem.Status = 3
            dItem.invoice = invoiceID
            dItem.save()
        

        #Update daily Employees
        dailyE = DailyEmployee.objects.filter(DailyID__woID = wo, estimate = estimateID).exclude(Status=4)

        for e in dailyE:
            
            if e.total_hours > 0:
                dEmp = DailyEmployee.objects.filter(id = e.id).first()
                
                dEmp.Status = 3
                dEmp.invoice = invoiceID
                dEmp.save()

        #Update externalProdItem
        epItem = externalProdItem.objects.filter(externalProdID__woID = wo, estimate = estimateID)

        for j in epItem:
            eItem = externalProdItem.objects.filter(id = j.id).first()

            eItem.Status = 3
            eItem.invoice = invoiceID
            eItem.save()

        #Update authorizedItem
        authItem = authorizedBilling.objects.filter(woID = wo, estimate = estimateID)

        for k in authItem:
            aItem = authorizedBilling.objects.filter(id = k.id).first()

            aItem.Status = 3
            aItem.invoice = invoiceID
            aItem.save()
        
        #Update Internal PO
        internal = internalPO.objects.filter(woID = wo, estimate = estimateID)

        for l in internal:
            iItem = internalPO.objects.filter(id = l.id).first()

            iItem.Status = 3
            iItem.invoice = invoiceID
            iItem.save()
        

        #adjustments

        adj = woAdjustment.objects.filter(woID = wo, estimateNumber = estimateID).first() 
        if adj:   
            adj.invoiceNumber = invoiceID
            adj.save()

        est = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()       
        est.Status = 2
        est.save()


        calculate_invoice_total(request,wo.id,int(invoiceID))
    
        
    return render(request,'landing.html',{ 'message': ' Invoices updated Successfully.... Detail:  ' , 'alertType':'success','emp':emp, 'per':per})
    

@login_required(login_url='/home/')
def wo_adjustment(request, woID, estimateID):
    emp = Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    wo = workOrder.objects.filter(id=woID).first()
    form = woAdjustEstimateForm(request.POST or None, initial={'woID': wo, 'estimateNumber': estimateID})
                            
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/billing_list/" + str(woID) + "/False")
         
    context['form']= form
    context["emp"]=emp
    return render(request, "wo_adjustment_estimate.html", context)

def update_wo_adjustment(request, woID, estimateID):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = woID).first()

    obj = woAdjustment.objects.filter(woID = wo, estimateNumber = estimateID).first()

    form = woAdjustEstimateForm(request.POST or None, instance = obj)
 
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()
        form.save()               
        return HttpResponseRedirect("/billing_list/" + str(woID) + "/False")

    context["form"] = form
    context["emp"] = emp
    return render(request, "wo_adjustment_estimate.html", context)


def update_woEstimate_comment(request, woID, estimateID):

    emp = Employee.objects.filter(user__username__exact = request.user.username).first()        
    context ={}
    context["emp"] = emp

    per = period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    wo = workOrder.objects.filter(id = woID).first()

    obj = woEstimate.objects.filter(woID = wo, estimateNumber = estimateID).first()

    form = woEstimateCommentForm(request.POST or None, instance = obj)
 
    if form.is_valid():        
        form.save()               
        return HttpResponseRedirect("/billing_list/" + str(woID) + "/False")

    context["form"] = form
    context["emp"] = emp
    return render(request, "update_woEstimate_comment.html", context)


def calculate_billing_amount(request, wo):
    
    #Validate if invoice exist for the order
    
    isRestoring = False
    errorMessage = ""
    
    #TOTAL BILLING AMOUNT INVOICED
    totalInvoiced = 0
    pendingProduction = 0

    per = period.objects.filter(status__in=(1,2)).first()
    
    wo = workOrder.objects.filter(id=wo.id).first()    
    
    #Get all the items associated with an invoice and Estimate and group by itemID and location

    payItems = DailyItem.objects.filter(DailyID__woID = wo, estimate__isnull = False )
    #payItems = DailyItem.objects.filter(DailyID__woID = wo )
    itemResume = []

    try:
        for data in payItems:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
        
        
    except Exception as e:
        print(str(e)) 

    # Group External Production by Item
    try:
        extProduction = externalProdItem.objects.filter(externalProdID__woID = wo, estimate__isnull = False)
        #extProduction = externalProdItem.objects.filter(externalProdID__woID = wo)

        for data in extProduction:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
        
        
    except Exception as e:
        print(str(e)) 

    itemFinal = []    
            
    authorizedItem = authorizedBilling.objects.filter(woID = wo, estimate__isnull = False)
    #authorizedItem = authorizedBilling.objects.filter(woID = wo)
    qtyP = 0
    totalP = 0
    qtyA = 0
    totalA = 0

    for itemA in authorizedItem:
        itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

        if itemResult != None:          
            itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyP += validate_decimals(itemResume[itemResult]['quantity'])
            totalP += validate_decimals(itemResume[itemResult]['amount'])
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)
        else:
            itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)

    #Getting Partial Estimates
    openEstimate = woEstimate.objects.filter(woID = wo, Status = 1).count()

    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate__isnull = False).exclude(Status=4)
    #bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True).exclude(Status=4)

    totalHours = 0
    totalHoursRate =  0

    totalInvoiced += validate_decimals(totalP)
        
    ###############*********************** calculation the production without invoice ############*****************
    
    #Get all the items associated with an invoice and Estimate and group by itemID and location

    payItems = DailyItem.objects.filter(DailyID__woID = wo, estimate__isnull = True )
    #payItems = DailyItem.objects.filter(DailyID__woID = wo )
    itemResume = []

    try:
        for data in payItems:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
        
        
    except Exception as e:
        print(str(e)) 

    # Group External Production by Item
    try:
        extProduction = externalProdItem.objects.filter(externalProdID__woID = wo, estimate__isnull = True)
        #extProduction = externalProdItem.objects.filter(externalProdID__woID = wo)

        for data in extProduction:

            itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == data.itemID.item.itemID), None)
            amount = 0
            amount = Decimal(str(data.quantity)) * Decimal(str(data.itemID.price))  
            if itemResult != None:                  
                itemResume[itemResult]['quantity'] += data.quantity
                itemResume[itemResult]['amount'] += amount
            else:            
                itemResume.append({'item':data.itemID.item.itemID, 'name': data.itemID.item.name, 'quantity': data.quantity, 'price':data.itemID.price, 'amount':amount,'Encontrado':False})
        
        
    except Exception as e:
        print(str(e)) 

    itemFinal = []    
            
    authorizedItem = authorizedBilling.objects.filter(woID = wo, estimate__isnull = True)
    #authorizedItem = authorizedBilling.objects.filter(woID = wo)
    qtyP = 0
    totalP = 0
    qtyA = 0
    totalA = 0

    for itemA in authorizedItem:
        itemResult = next((i for i, item in enumerate(itemResume) if item["item"] == itemA.itemID.item.itemID), None)

        if itemResult != None:          
            itemFinal.append({'item':itemResume[itemResult]['item'], 'name': itemResume[itemResult]['name'], 'quantity': itemResume[itemResult]['quantity'], 'price': itemResume[itemResult]['price'], 'amount':itemResume[itemResult]['amount'], 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyP += validate_decimals(itemResume[itemResult]['quantity'])
            totalP += validate_decimals(itemResume[itemResult]['amount'])
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)
        else:
            itemFinal.append({'item':itemA.itemID.item.itemID, 'name': itemA.itemID.item.name, 'quantity': None, 'price': None, 'amount':None, 'quantityA': itemA.quantity, 'priceA':itemA.itemID.price, 'amountA':itemA.total, 'idA': itemA.id})
            qtyA += validate_decimals(itemA.quantity)
            totalA += validate_decimals(itemA.total)

    
    #Adding Billable Hours

    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, estimate__isnull = True).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    pendingProduction += validate_decimals(totalP)
    
    
    
        
    return totalInvoiced, pendingProduction



def get_invoiced_production_total_for_wo(wo):
    if wo is None:
        return Decimal('0')

    if not hasattr(wo, 'id'):
        wo = workOrder.objects.filter(id=wo).first()
        if wo is None:
            return validate_decimals('0')

    qs = authorizedBilling.objects.filter(woID=wo).exclude(invoice__isnull=True).exclude(invoice='').exclude(invoice='0')

    total = validate_decimals('0')
    for ab in qs:        
        total += validate_decimals(ab.total)

    #po Facturado
    po_facturado = 0
    
    internal_facturado = internalPO.objects.filter(woID = wo, nonBillable = False, invoice__isnull = False )
    
    for i in internal_facturado:
        if i.total:
            if i.isAmountRounded:
                po_facturado += int(round(float(str(i.total))))
            else:
                po_facturado += Decimal(str(i.total))
    
    po_facturado = validate_decimals(po_facturado)  
    
    total_facturado = 0
    total_facturado = validate_decimals(total) + validate_decimals(po_facturado * 1.10)
    
    #Adding Billable Hours
    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice__isnull = False).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))

    total_facturado += validate_decimals(totalHoursRate) 
    return validate_decimals(total_facturado)

def get_uninvoiced_production_total_for_wo(wo):
    if wo is None:
        return Decimal('0')

    if not hasattr(wo, 'id'):
        wo = workOrder.objects.filter(id=wo).first()
        if wo is None:
            return validate_decimals('0')

    qs = authorizedBilling.objects.filter(woID=wo, Status__in = (1,2))

    total = validate_decimals('0')
    for ab in qs:        
        total += validate_decimals(ab.total)
        
        
    #po No Facturado
    po_no_facturado = 0
    
    internal_no_facturado = internalPO.objects.filter(woID = wo, nonBillable = False, invoice__isnull = True )
    
    for i in internal_no_facturado:
        if i.total:
            if i.isAmountRounded:
                po_no_facturado += int(round(float(str(i.total))))
            else:
                po_no_facturado += Decimal(str(i.total))
    
    po_no_facturado = validate_decimals(po_no_facturado)     
    total_no_facturado = 0   
    total_no_facturado = validate_decimals(total) + validate_decimals(po_no_facturado * 1.10)
    
    #Adding Billable Hours
    bill = DailyEmployee.objects.filter(DailyID__woID =wo, billableHours = True, invoice__isnull = True).exclude(Status=4)
    

    totalHours = 0
    totalHoursRate =  0

    for b in bill:
        totalHours +=  validate_decimals(b.total_hours) 
        #Calculating Regular Hours
        totalHoursRate += (validate_decimals(b.regular_hours) * validate_decimals(b.EmployeeID.hourly_rate))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.ot_hour) * (validate_decimals(b.EmployeeID.hourly_rate)* 1.5))

        #Calculating OT Hours
        totalHoursRate += (validate_decimals(b.double_time) * (validate_decimals(b.EmployeeID.hourly_rate)* 2))

    total_no_facturado += validate_decimals(totalHoursRate) 
    return validate_decimals(total_no_facturado)


def get_unestimated_production_total(wo):
    if wo is None:
        return Decimal('0')

    if not hasattr(wo, 'id'):
        wo = workOrder.objects.filter(id=wo).first()
        if wo is None:
            return Decimal('0')

    total = Decimal('0')

    daily_items = DailyItem.objects.filter(
        DailyID__woID=wo,
        Status=1
    )

    for item in daily_items:
        if item.total not in (None, ''):
            total += Decimal(str(validate_decimals(item.total)))
        else:
            price = item.price if item.price not in (None, '') else item.itemID.price
            total += Decimal(str(validate_decimals(item.quantity))) * Decimal(str(validate_decimals(price)))

    external_items = externalProdItem.objects.filter(
        externalProdID__woID=wo,
        Status=1
    )

    for item in external_items:
        if item.total not in (None, ''):
            total += Decimal(str(validate_decimals(item.total)))
        else:
            total += Decimal(str(validate_decimals(item.quantity))) * Decimal(str(validate_decimals(item.itemID.price)))

    return validate_decimals(total)