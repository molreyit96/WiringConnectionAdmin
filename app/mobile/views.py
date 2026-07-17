from ast import Try, parse
from django.views.generic import View
from django.views.generic import CreateView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
import xlwt
from datetime import datetime
from django.contrib.auth import authenticate, login as login_process
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, redirect
from .models import *
from .forms import * 
from . import views
from sequences import get_next_value, Sequence
from workOrder import models as catalogModel
from datetime import datetime, timedelta
from django.db import transaction
import os
from utils.email import send_email_with_attachment
from django.core.files.base import ContentFile
import tempfile
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from xhtml2pdf import pisa
import base64
from django.views.decorators.http import require_POST
from django.db.models import Sum, OuterRef, Subquery, Value, CharField, IntegerField
from django.db.models.functions import Concat, Cast

@login_required(login_url='/home/')
def mobile(request):
    emp =  catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = catalogModel.period.objects.filter(status=1).first()

    #Select the location according to the parameter
    
    if emp:
        if emp.Location is None or not emp.Location:        
            return render(request,'mobile/landing.html',{'message':'This user does not have a location assigned', 'alertType':'danger', 'emp':emp})
        elif not per:
            return render(request,'mobile/landing.html',{'message':'no active period found', 'alertType':'danger', 'emp':emp})
    else:
        return render(request,'mobile/landing.html',{'message':'This user does not have a location assigned', 'alertType':'danger', 'emp':emp})
    
    if emp:
        LocID = emp.Location.LocationID
    else: 
        LocID = 0
    
    context ={}


    context["period"] = per    
    context["emp"]= emp

    return HttpResponseRedirect('/mobile/home/' + str(LocID))       



@login_required(login_url='/home/')
def mobile_home(request, LocID):
    emp =  catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = catalogModel.period.objects.filter(status=1).first()
    
    #Select the location according to the parameter
    loca = catalogModel.Locations.objects.filter(LocationID = LocID).first()

    if not per:
        per = catalogModel.period.objects.filter(periodID=-1).first()

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        per.fromDate = yesterday
        per.toDate = today
        per.payDate = today
        per.save()

    else:
        rejectedDailys = DailyMob.objects.filter(Period=per, Status=5, created_by=request.user.username, Location = loca)


    context ={}
    context["period"] = per    
    context["emp"]= emp
    context["rejectedDailys"] = rejectedDailys 

    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append({'LocationID': emp.Location.LocationID, 'name':emp.Location.name })
    
    for i in locaList:
        locationList.append({'LocationID': i.LocationID.LocationID, 'name': i.LocationID.name} )

    context["locationList"] = locationList

    if LocID == 0:
        context["selectedLocation"] = emp.Location.LocationID
    else:
        context["selectedLocation"] = LocID

    
    
    # validate that yesterday and today are within the active period
    from_date = getattr(per, 'fromDate', None)
    to_date = getattr(per, 'toDate', None)
    
    if hasattr(from_date, 'date'):
        from_date = from_date.date()
    if hasattr(to_date, 'date'):
        to_date = to_date.date()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    message = ""

    # determine membership of each date in the active period
    today_in = from_date <= today <= to_date
    yesterday_in = from_date <= yesterday <= to_date

    yesterday_period = None
    today_period = None

    if today_in and yesterday_in:
        message = ""  # both inside -> no warning
        yesterday_period = per
        today_period = per
    elif today_in and not yesterday_in:
        message = "Warning: Yesterday is outside the active period."
        yesterday_period = catalogModel.period.objects.filter(periodID=-1).first()
        today_period = per
    elif yesterday_in and not today_in:
        message = "Warning: Today is outside the active period."
        today_period = catalogModel.period.objects.filter(periodID=-1).first()
        yesterday_period = per
    else:
        message = "Warning: Today's date and Yesterday's date are outside the active period."
        yesterday_period = catalogModel.period.objects.filter(periodID=-1).first()
        today_period = catalogModel.period.objects.filter(periodID=-1).first()
    

    #getting the list of days per week
    startDate = yesterday
    numDays = 2
    week1 = []
    totalRejected = 0
    totalDeleted = 0

    for x in range(0,numDays):
        selectedDay = False
        fullDate = startDate + timedelta(days = x)
        shortDate = fullDate.strftime("%a") + ' ' + fullDate.strftime("%d")
        longDate = fullDate.strftime("%A") + ' ' + fullDate.strftime("%d")
        day = fullDate.strftime("%d")
        
        user = request.user.username

        #obtengo la cantidad de Items asociados
        dItems = DailyMob.objects.filter(Period = per, Location = loca, day = fullDate, created_by = user)
        totalItems = 0
        
        
        type ="success"
        for d in dItems:
            
            dItemDetail = DailyMobItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

        
            if d.Status == 5:
                totalRejected += 1
                type="danger"
            
            if d.Status == 6:
                totalDeleted += 1
                type="danger"

        pr = None

        if day == yesterday.strftime("%d"):
            pr = yesterday_period
        elif day == today.strftime("%d"):
            pr = today_period     
                

        week1.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay, 'type':type, 'actual_period': pr })

    """startDate += timedelta(days = numDays)
    week2 = []
    for x in range(0,numDays):
        selectedDay = False
        fullDate = startDate + timedelta(days = x)
        shortDate = fullDate.strftime("%a") + ' ' + fullDate.strftime("%d")
        longDate = fullDate.strftime("%A") + ' ' + fullDate.strftime("%d")
        day = fullDate.strftime("%d")

        #obtengo la cantidad de Items asociados
        dItems = DailyMob.objects.filter(Period = per, Location = loca, day = fullDate)
        totalItems = 0
        type ="success"
        
        for d in dItems:
            dItemDetail = DailyMobItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

            
            if d.Status == 5:
                totalRejected += 1
                type="danger"
            
            if d.Status == 6:
                totalDeleted += 1
                type="danger"

        week2.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay, 'type':type })
   """
    context["week1"] = week1
    context["message"] = message
    context["totalRejected"] = totalRejected
    context["totalDeleted"] = totalDeleted

    return render(request, "mobile/home.html", context)

@login_required(login_url='/home/')
def crew(request, perID, dID, crewID, LocID):
    emp =  catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    #per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    per = catalogModel.period.objects.filter(status=1).first()

    if not per:
        per = catalogModel.period.objects.filter(periodID=-1).first()


    context["per"] = per        
    context["emp"]= emp
    context["dailyactual"] =""

    #Select the location
    loca = catalogModel.Locations.objects.filter(LocationID = LocID).first()

    twTitle = ''


    #Validate if the Location receiver is valid for the current user

    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append({'LocationID': emp.Location.LocationID, 'name':emp.Location.name })
    
    for i in locaList:
        locationList.append({'LocationID': i.LocationID.LocationID, 'name': i.LocationID.name} )

    
    # Validation to check if LocationID 40 exists
    location_exists = any(str(loc['LocationID']) == str(LocID) for loc in locationList)
    if not location_exists:
        return redirect('/mobile/home/' + str(emp.Location.LocationID))


    #**************************************************************

    
    # validate that yesterday and today are within the active period
    from_date = getattr(per, 'fromDate', None)
    to_date = getattr(per, 'toDate', None)
    
    if hasattr(from_date, 'date'):
        from_date = from_date.date()
    if hasattr(to_date, 'date'):
        to_date = to_date.date()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    

    message = ""

    # determine membership of each date in the active period
    today_in = from_date <= today <= to_date
    yesterday_in = from_date <= yesterday <= to_date
    yesterday_period = None
    today_period = None

    if today_in and yesterday_in:
        message = ""  # both inside -> no warning
        yesterday_period = per
        today_period = per
    elif today_in and not yesterday_in:
        message = "Warning: Yesterday is outside the active period."
        yesterday_period = catalogModel.period.objects.filter(periodID=-1).first()
        today_period = per
    elif yesterday_in and not today_in:
        message = "Warning: Today is outside the active period."
        today_period = catalogModel.period.objects.filter(periodID=-1).first()
        yesterday_period = per
    else:
        message = "Warning: Today's date and Yesterday's date are outside the active period."
        yesterday_period = catalogModel.period.objects.filter(periodID=-1).first()
        today_period = catalogModel.period.objects.filter(periodID=-1).first()

    
    if dID == yesterday.strftime("%d"):
        context["period"] = yesterday_period
    elif dID == today.strftime("%d"):
        context["period"] = today_period
    else:
        context["period"] = per

    #***********************************************************************************************************
    #StartDate is taken from the Period.From because it is possible to edit rejected Dailys from other days than yesterday or today

    #getting the list of days per week
    #startDate = yesterday
    #getting the list of days per week
    startDate = per.fromDate
    numDays = 15
    week1 = []
    #***********************************************************************************************************
    for x in range(0,numDays):
        selectedDay = False
        fullDate = startDate + timedelta(days = x)
        shortDate = fullDate.strftime("%a") + ' ' + fullDate.strftime("%d")
        longDate = fullDate.strftime("%A") + ' ' + fullDate.strftime("%d")
        day = fullDate.strftime("%d")
        if dID == day:
            selectedDay = True
            selectedDate = fullDate
            twTitle +=  fullDate.strftime("%A").upper() + ', ' + fullDate.strftime("%B %d, %Y").upper()
        
        
        #obtengo la cantidad de Items asociados
        dItems = DailyMob.objects.filter(Period = per, Location = loca, day = fullDate)
        totalItems = 0

        for d in dItems:
            dItemDetail = DailyMobItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

        pr = None

        if day == yesterday.strftime("%d"):
            pr = yesterday_period
        elif day == today.strftime("%d"):
            pr = today_period

        week1.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay, 'actual_period': pr })

    """startDate += timedelta(days = numDays)
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
            twTitle +=  fullDate.strftime("%A").upper() + ', ' + fullDate.strftime("%B %d, %Y").upper()

        #obtengo la cantidad de Items asociados
        dItems = DailyMob.objects.filter(Period = per, Location = loca, day = fullDate)
        totalItems = 0

        for d in dItems:
            dItemDetail = DailyMobItem.objects.filter(DailyID=d)

            for i in dItemDetail:
                totalItems += i.quantity

        week2.append({'day':day, 'shortDate': shortDate, 'longDate': longDate, 'fullDate': fullDate, 'Total': totalItems, 'selected': selectedDay })
    """
    

    if request.user.is_staff or emp.is_superAdmin:
        superV = catalogModel.Employee.objects.filter(is_supervisor=True)
    else:
        superV = catalogModel.Employee.objects.filter(is_supervisor=True)

    user = request.user.username
    

    if dID != "0":

        #If selectedDate is not yesterday or today, just get the dailys in Rejected Status
        if selectedDate != yesterday and selectedDate != today:
            crews = DailyMob.objects.filter(Period = perID, day=selectedDate, Location = loca, Status=5, created_by = user).order_by('crew')
            context["AddCrew"] = False
        else:
            # get the list of dailys for the period, Day selected and Location
            crews = DailyMob.objects.filter(Period = perID, day=selectedDate, Location = loca, created_by = user).order_by('crew')
            context["AddCrew"] = True
        
        context["crew"] = crews

  

    if crews.count() == 1:
        crewID = crews.first().crew

    if crewID != "0":
        dailyID = DailyMob.objects.filter(Period = perID, day=selectedDate, crew = crewID, Location = loca, created_by = user ).first()

        
        dailyEmp = DailyMobEmployee.objects.filter(DailyID = dailyID).order_by('created_date')
        context["dailyEmp"] = dailyEmp

        dailyItem = DailyMobItem.objects.filter(DailyID = dailyID).order_by('created_date')
        dailyTotal = 0
        ovT = 0
        for di in dailyItem:
            dailyTotal += di.total 


        if dailyID.own_vehicle != None:
            ovT = (dailyTotal * dailyID.own_vehicle) / 100
        
        granTotal = dailyTotal + ovT

        #Adding the documents Maps
        dailyDocs = DailyMobDocs.objects.filter(DailyID = dailyID, docType=1).order_by('created_date')

        #Adding the documents Pictures
        dailyDocsPic = DailyMobDocs.objects.filter(DailyID = dailyID, docType=2).order_by('created_date')

        #Adding the documents Material Backup
        dailyDocsMB = DailyMobDocs.objects.filter(DailyID = dailyID, docType=3).order_by('created_date')
    

        context["dailyactual"] = dailyID
        context["dailyItem"] = dailyItem
        context["dailyDocs"] = dailyDocs
        context["dailyDocsPic"] = dailyDocsPic
        context["dailyDocsMB"] = dailyDocsMB
        context["TotalItem"] = dailyTotal
        context["ovTotal"] = ovT
        context["GranTotalItem"] = granTotal

    context["week1"] = week1
    context["message"] = message
    context["selectedDate"] = twTitle
    context["superV"] = superV
    context["selectedCrew"] = int(crewID)
    context["selectedDay"] = int(dID)
    context["selectedLocation"] = LocID
    context["selectedLoca"] = loca

    return render(request, "mobile/crew.html", context)


@login_required(login_url='/home/')
def update_supervisor(request, perID, dID, crewID, LocID):
    emp =  catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per    
    context["period"] = per    
    context["emp"]= emp

    if request.user.is_staff or emp.is_superAdmin:
        superV = catalogModel.Employee.objects.filter(is_supervisor=True).order_by('first_name')
    else:
        superV = catalogModel.Employee.objects.filter(is_supervisor=True).order_by('first_name')
    
    crew = DailyMob.objects.filter(id = crewID).first()

    if request.method == 'POST':
        dailyID = request.POST.get('daily')
        sup = request.POST.get('supervisor') 
        split = request.POST.get('split')
        ptp = request.POST.get('ptp')
        ov = request.POST.get('ov')
        crew = DailyMob.objects.filter(id = dailyID).first()
        if crew:            
            crew.supervisor = sup                      
            crew.split_paymet = bool(split)   

            if ov != '':
                crew.own_vehicle = ov
            else:
                crew.own_vehicle = None    

            emp_ptp = update_ptp_Emp(dailyID, bool(split))
            emp_ptp = 0

            crew.total_pay = emp_ptp     
            crew.save()
            per = crew.Period.id  

            emp_ptp = update_ptp_Emp(dailyID, bool(split))       
            
            if int(str(sup))>0 and crew.woID != None:
                super = catalogModel.Employee.objects.filter(employeeID = sup ).first()
                if super:   
                    wo = catalogModel.workOrder.objects.filter( id = crew.woID.id).first()
                    if wo:             
                        wo.WCSup = super
                        wo.save()           

        return HttpResponseRedirect('/mobile/crew/' + str(per) + '/' + dID  + '/'+ str(crew.crew) +'/'+LocID)       

    context["superV"] = superV            
    context["selectedCrew"] = int(crewID)
    context["dailyObj"] = crew
    context["selectedDay"] = int(dID)
    context["selectedLocation"] = LocID      

    return render(request, "mobile/update_supervisor.html", context)


@login_required(login_url='/home/')
def create_daily(request, pID, dID, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    
    context = {}    
    context["emp"] = emp    
    per = catalogModel.period.objects.filter(id = pID).first()

    #perActual = catalogModel.period.objects.filter(status__in=(1,2)).first()
    perActual = catalogModel.period.objects.filter(status=1).first()
    context["per"] = perActual

    if int(LocID) > 0:
        loc = catalogModel.Locations.objects.filter(LocationID = LocID).first()
    else:
        loc = catalogModel.Locations.objects.filter(LocationID = emp.Location.LocationID).first()

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

        crewNumber = DailyMob.objects.filter( Period = per, day = selectedDate, Location = loc).last()
        if crewNumber:
            crewNo = crewNumber.crew
        else:
            crewNo = 0

        user = request.user.username
        crewNumberByUser = DailyMob.objects.filter( Period = per, day = selectedDate, Location = loc, created_by = user).last()
        if crewNumberByUser:
            crewNoByUser = crewNumberByUser.crew_by_user
        else:
            crewNoByUser = 0

        crew  = DailyMob(
            Period = per,
            Location = loc,
            day = selectedDate,
            crew = int(crewNo) + 1,
            created_date = datetime.now(),
            created_by = request.user.username,
            crew_by_user = int(crewNoByUser) + 1
        )

        crew.save()
        per = crew.Period.id
        
        #Adding Audit
        
        operationDetail = "Period: " + str(per) + ", Crew: " + str(crew.crew)       
        

        return HttpResponseRedirect('/mobile/crew/' + str(per) + '/' + crew.day.strftime("%d")  + '/'+ str(crew.crew) +'/'+LocID)
    else:
        return HttpResponseRedirect('/mobile/')

@login_required(login_url='/home/')
def delete_daily(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per


    obj = get_object_or_404(DailyMob, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
 
    actual_wo = obj.woID
    
    obj.delete()

    if actual_wo != None:
        lastD = DailyMob.objects.filter(woID = actual_wo).last()
        wo = catalogModel.workOrder.objects.filter(id = actual_wo.id).first()
        
        if lastD:                 
            wo.UploadDate = lastD.created_date

            if lastD.supervisor != None:
                sup = catalogModel.Employee.objects.filter(employeeID = lastD.supervisor ).first()
                if sup:                
                    wo.WCSup = sup

            wo.save()
        else:             

            wo.Status = 1
            wo.Location = None
            wo.UploadDate = None
            wo.UserName = None
            wo.WCSup = None
            wo.UploadDate = datetime.now()
            wo.save()

        
    return HttpResponseRedirect('/mobile/crew/' + str(obj.Period.id) + '/' + obj.day.strftime("%d") + '/0/' + str(LocID)) 

@login_required(login_url='/home/')
def update_order_daily(request, woID, dailyID, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()

    context = {}    
    context["emp"] = emp    

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    crew = DailyMob.objects.filter(id = dailyID).first()
    wo = catalogModel.workOrder.objects.filter(id = woID).first()
    
    anterior = None

    if crew and wo:

        if crew.woID != None:
            anterior = catalogModel.workOrder.objects.filter(id = crew.woID.id).first()

            if anterior:                

                anterior.Status = 1
                anterior.Location = None
                anterior.UploadDate = None
                anterior.UserName = None
                anterior.WCSup = None
                anterior.UploadDate = datetime.now()
                anterior.save()


        crew.woID = wo
        crew.save()

        
        wo.Status = 2
        wo.Location = crew.Location
        wo.UploadDate = datetime.now()
        wo.UserName = request.user.username
        if crew.supervisor != None:
            sup = catalogModel.Employee.objects.filter(employeeID = crew.supervisor ).first()
            if sup:                
                wo.WCSup = sup

        wo.save()

        per = crew.Period.id      
        

    return HttpResponseRedirect('/mobile/crew/' + str(per) + '/' + crew.day.strftime("%d")  + '/'+ str(crew.crew) +'/' + str(LocID))


#************** DAILY EMP ***********************

@login_required(login_url='/home/')    
def create_daily_emp(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    dailyID = DailyMob.objects.filter(id = id).first()

    dailyE = DailyMobEmployee.objects.filter(DailyID = dailyID)
    empList = []

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    for i in dailyE:
       empList.append(i.EmployeeID.employeeID) 

    EmpLocation = catalogModel.Employee.objects.filter(is_active = True, is_supervisor = False).exclude(employeeID__in = empList)

    #Get Schedule from the first Daily Employee
    dailyEmp1st = DailyMobEmployee.objects.filter(DailyID = dailyID).exclude(start_time=None).order_by('id').first()

    if dailyEmp1st:
        startTime = dailyEmp1st.start_time
        endTime = dailyEmp1st.end_time
        lunch_startTime = dailyEmp1st.start_lunch_time
        lunch_endTime = dailyEmp1st.end_lunch_time
        
        form = DailyMobEmpForm(request.POST or None, initial={'DailyID': dailyID, 'start_time': startTime, 'end_time': endTime,'start_lunch_time': lunch_startTime, 'end_lunch_time':lunch_endTime}, qs = EmpLocation)

    else:
        form = DailyMobEmpForm(request.POST or None, initial={'DailyID': dailyID}, qs = EmpLocation)


    if form.is_valid():                
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time


        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)
        form.instance.created_date = datetime.now()

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = catalogModel.Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp
        form.save()  
          
        update_ptp_Emp(id, dailyID.split_paymet)             
        return HttpResponseRedirect('/mobile/crew/' + str(dailyID.Period.id) + '/' + dailyID.day.strftime("%d") + '/' + str(dailyID.crew) +'/' + str(LocID))        
         
    
    context['form']= form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    context["selectedLocation"] = LocID
    return render(request, "mobile/create_daily_emp.html", context)

@login_required(login_url='/home/')    
def create_daily_emp_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    dailyID = DailyMob.objects.filter(id = id).first()

    dailyE = DailyMobEmployee.objects.filter(DailyID = dailyID)
    empList = []

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    for i in dailyE:
       empList.append(i.EmployeeID.employeeID) 

    EmpLocation = catalogModel.Employee.objects.filter(is_active = True, is_supervisor = False).exclude(employeeID__in = empList)

    form = DailyMobEmpForm(request.POST or None, initial={'DailyID': dailyID}, qs = EmpLocation)
    if form.is_valid():                
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time

        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)
        form.instance.created_date = datetime.now()

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = catalogModel.Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp
        form.save()  
          
        update_ptp_Emp(id, dailyID.split_paymet)             
        return HttpResponseRedirect('/mobile/approve_timesheet/' + str(dailyID.id) )        
         
    
    context['form']= form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    context["selectedLocation"] = LocID
    return render(request, "mobile/create_daily_emp_sup.html", context)

@login_required(login_url='/home/')
def update_daily_emp(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}    
    obj = get_object_or_404(DailyMobEmployee, id = id)

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per    

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    EmpLocation = catalogModel.Employee.objects.all()
    empSelected = catalogModel.Employee.objects.filter(employeeID = obj.EmployeeID.employeeID ).first()
 
    form = DailyMobEmpForm(request.POST or None, instance = obj, qs = EmpLocation)
 
    if form.is_valid():      
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time

        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = catalogModel.Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp

        form.save()       

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        context["emp"] = emp       
        return HttpResponseRedirect('/mobile/crew/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) + '/' + str(LocID)) 

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    context["form"] = form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    context["empSelected"] = empSelected
    context["selectedLocation"] = LocID
    
    return render(request, "mobile/update_daily_emp.html", context)

@login_required(login_url='/home/')
def update_daily_emp_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}    
    obj = get_object_or_404(DailyMobEmployee, id = id)

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per    

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    EmpLocation = catalogModel.Employee.objects.all()
    empSelected = catalogModel.Employee.objects.filter(employeeID = obj.EmployeeID.employeeID ).first()
 
    form = DailyMobEmpForm(request.POST or None, instance = obj, qs = EmpLocation)
 
    if form.is_valid():      
        startTime = form.instance.start_time
        endTime = form.instance.end_time
        lunch_startTime = form.instance.start_lunch_time
        lunch_endTime = form.instance.end_lunch_time

        form.instance.total_hours, form.instance.regular_hours,form.instance.ot_hour, form.instance.double_time = calculate_hours(startTime, endTime, lunch_startTime, lunch_endTime)

        empid = request.POST.get('EmployeeID')
        
        selectedEmp = catalogModel.Employee.objects.filter(employeeID = empid).first()
        form.instance.EmployeeID = selectedEmp

        form.save()       

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        context["emp"] = emp       
        return HttpResponseRedirect('/mobile/approve_timesheet/' + str(obj.DailyID.id)) 

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    context["form"] = form
    context["emp"] = emp
    context["daily"] = dailyID
    context["empList"] = EmpLocation
    context["empSelected"] = empSelected
    context["selectedLocation"] = LocID
    
    return render(request, "mobile/update_daily_emp_sup.html", context)


@login_required(login_url='/home/')
def delete_daily_emp(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    obj = get_object_or_404(DailyMobEmployee, id = id)
 
    context["form"] = obj
    context["emp"] = emp

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    if obj:
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet)        
       
    return HttpResponseRedirect('/mobile/crew/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 

@login_required(login_url='/home/')
def delete_daily_emp_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    obj = get_object_or_404(DailyMobEmployee, id = id)
 
    context["form"] = obj
    context["emp"] = emp

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per
 
    if obj:
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet)        
       
    return HttpResponseRedirect('/mobile/approve_timesheet/' + str(obj.DailyID.id) ) 

   

@login_required(login_url='/home/')
def create_daily_item(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    dailyID = DailyMob.objects.filter(id = id).first()

    dailyI = DailyMobItem.objects.filter(DailyID = dailyID)
    itemList = []

    for i in dailyI:
       itemList.append(i.itemID.item.itemID) 


    #Validate if the WO was created after the Prices Update
    priceUpdate = "2025-03-03"
    priceCreated = dailyID.woID.created_date

    #if priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date():
    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= True).exclude(item__itemID__in = itemList)
    #else:
    #    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= False).exclude(item__itemID__in = itemList)

    #context["is_new"] = priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date()
    #context["created"] = datetime.strftime(priceCreated.date(), "%Y-%m-%d")

    form = DailyMobItemForm(request.POST or None, initial={'DailyID': dailyID}, qs = itemLocation)
    if form.is_valid():    
        
        itemid = request.POST.get('itemID')
        
        selectedItem = catalogModel.itemPrice.objects.filter(id = itemid).first()
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
        
        update_ptp_Emp(id, dailyID.split_paymet)

        return HttpResponseRedirect('/mobile/crew/' + str(dailyID.Period.id) + '/' + dailyID.day.strftime("%d") + '/' + str(dailyID.crew) +'/' + str(LocID))        
         
    context['form']= form
    context["emp"] = emp
    context["DailyID"] = dailyID
    context["itemList"] = itemLocation
    context["selectedLocation"] = LocID
    return render(request, "mobile/create_daily_item.html", context)

@login_required(login_url='/home/')
def create_daily_item_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    dailyID = DailyMob.objects.filter(id = id).first()

    dailyI = DailyMobItem.objects.filter(DailyID = dailyID)
    itemList = []

    for i in dailyI:
       itemList.append(i.itemID.item.itemID) 


    #Validate if the WO was created after the Prices Update
    priceUpdate = "2025-03-03"
    priceCreated = dailyID.woID.created_date

    #if priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date():
    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= True).exclude(item__itemID__in = itemList)
    #else:
    #    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = dailyID.Location.LocationID, item__is_new= False).exclude(item__itemID__in = itemList)

    #context["is_new"] = priceCreated.date() >= datetime.strptime(priceUpdate, "%Y-%m-%d").date()
    #context["created"] = datetime.strftime(priceCreated.date(), "%Y-%m-%d")

    form = DailyMobItemForm(request.POST or None, initial={'DailyID': dailyID}, qs = itemLocation)
    if form.is_valid():    
        
        itemid = request.POST.get('itemID')
        
        selectedItem = catalogModel.itemPrice.objects.filter(id = itemid).first()
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
        
        update_ptp_Emp(id, dailyID.split_paymet)

        return HttpResponseRedirect('/mobile/approve_timesheet/' + str(dailyID.id) )        
         
    context['form']= form
    context["emp"] = emp
    context["DailyID"] = dailyID
    context["itemList"] = itemLocation
    context["selectedLocation"] = LocID
    return render(request, "mobile/create_daily_item_sup.html", context)

@login_required(login_url='/home/')
def update_daily_item(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobItem, id = id)

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = obj.DailyID.Location.LocationID)
    
    itemSelected = catalogModel.itemPrice.objects.filter(id = obj.itemID.id ).first()

    form = DailyMobItemForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if form.is_valid():
        #PJIG Aqui se modifico antes estaba price = form.instance.itemID.emp_payout
        price = form.instance.itemID.price    
        form.instance.price = float(price)
        
        #PJIG aqui se modifica ya que debede utilizar el emp_payout en lugar de price
        #form.instance.total = form.instance.quantity * float(price)        
        form.instance.total = form.instance.quantity * float(form.instance.itemID.emp_payout)
        
        itemid = request.POST.get('itemID')
        
        selectedItem = catalogModel.itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        form.save()
        context["emp"] = emp    

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        return HttpResponseRedirect('/mobile/crew/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/'+str(LocID)) 

    context["form"] = form
    context["emp"] = emp
    context["itemSelected"] = itemSelected
    context["DailyID"] = dailyID
    context["selectedLocation"] = LocID
    return render(request, "mobile/update_daily_item.html", context)

@login_required(login_url='/home/')
def update_daily_item_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobItem, id = id)

    dailyID = DailyMob.objects.filter(id = obj.DailyID.id).first()

    itemLocation = catalogModel.itemPrice.objects.filter(location__LocationID = obj.DailyID.Location.LocationID)
    
    itemSelected = catalogModel.itemPrice.objects.filter(id = obj.itemID.id ).first()

    form = DailyMobItemForm(request.POST or None, instance = obj, qs = itemLocation)
 
    if form.is_valid():
        #PJIG Aqui se modifico antes estaba price = form.instance.itemID.emp_payout
        price = form.instance.itemID.price    
        form.instance.price = float(price)


        #PJIG aqui se modifica ya que debede utilizar el emp_payout en lugar de price
        #form.instance.total = form.instance.quantity * float(price)        
        form.instance.total = form.instance.quantity * float(form.instance.itemID.emp_payout)
        
        itemid = request.POST.get('itemID')
        
        selectedItem = catalogModel.itemPrice.objects.filter(id = itemid).first()
        form.instance.itemID = selectedItem

        form.save()
        context["emp"] = emp    

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

        return HttpResponseRedirect('/mobile/approve_timesheet/' + str(obj.DailyID.id)) 

    context["form"] = form
    context["emp"] = emp
    context["itemSelected"] = itemSelected
    context["DailyID"] = dailyID
    context["selectedLocation"] = LocID
    return render(request, "mobile/update_daily_item_sup.html", context)

@login_required(login_url='/home/')
def delete_daily_item(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobItem, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if obj:
        
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

    return HttpResponseRedirect('/mobile/crew/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 

@login_required(login_url='/home/')
def delete_daily_item_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobItem, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if obj:
        
        obj.delete()

        update_ptp_Emp(obj.DailyID.id, obj.DailyID.split_paymet) 

    return HttpResponseRedirect('/mobile/approve_timesheet/' + str(obj.DailyID.id) ) 


#************** DAILY DOCS ***********************
class BulkUploadView(View):
    def post(self, request, id, LocID, docType, *args, **kwargs):
        form = DailyMobDocsForm(request.POST, request.FILES)

        if form.is_valid():
            daily_id = form.cleaned_data['DailyID']
            doc_type = form.cleaned_data['docType']            
            files = self.request.FILES.getlist('files')
            
            created_docs = []
            for file in files:
                doc = DailyMobDocs(
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
        emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
        context ={}

        per = catalogModel.period.objects.filter(status__in=(1,2)).first()
        context["per"] = per

        dailyID = DailyMob.objects.filter(id = id).first()

        # Add this if you need a GET handler for the form page
        form = DailyMobDocsForm(initial={
            'DailyID': dailyID , # Auto-set DailyID from URL parameter if needed
            'docType': docType
        })

        return render(request, 'mobile/create_daily_doc.html', {'form': form, 'dailyID': dailyID, 'emp': emp, 'docType': docType,'selectedLocation': LocID})
    
class BulkUploadViewSup(View):
    def post(self, request, id, LocID, docType, *args, **kwargs):
        form = DailyMobDocsForm(request.POST, request.FILES)

        if form.is_valid():
            daily_id = form.cleaned_data['DailyID']
            doc_type = form.cleaned_data['docType']
            files = self.request.FILES.getlist('files')
            
            created_docs = []
            for file in files:
                doc = DailyMobDocs(
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
        emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
        context ={}

        per = catalogModel.period.objects.filter(status__in=(1,2)).first()
        context["per"] = per

        dailyID = DailyMob.objects.filter(id = id).first()

        # Add this if you need a GET handler for the form page
        form = DailyMobDocsForm(initial={
            'DailyID': dailyID, # Auto-set DailyID from URL parameter if needed
            'docType': docType
        })

        return render(request, 'mobile/create_daily_doc_sup.html', {'form': form, 'dailyID': dailyID, 'emp': emp,  'docType': docType, 'selectedLocation': LocID})
    
@login_required(login_url='/home/')
def delete_daily_docs(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobDocs, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if obj:
        
        obj.delete()

    return HttpResponseRedirect('/mobile/crew/' + str(obj.DailyID.Period.id) + '/' + obj.DailyID.day.strftime("%d") + '/' + str(obj.DailyID.crew) +'/' + str(LocID)) 
       
def delete_daily_docs_sup(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["per"] = per

    obj = get_object_or_404(DailyMobDocs, id = id)
 
    context["form"] = obj
    context["emp"] = emp
 
    if obj:
        
        obj.delete()

    return HttpResponseRedirect('/mobile/approve_timesheet/' + str(obj.DailyID.id) ) 
       

@login_required(login_url='/home/')
def send_payroll(request, id, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    obj = get_object_or_404(DailyMob, id = id)
    
    if obj:
        obj.send_date = datetime.now()    
        obj.Status = 2
        obj.save()
        
        
    context["emp"] = emp
    context["id"] = id
    
    return HttpResponseRedirect('/mobile/crew/' + str(obj.Period.id) + '/' + obj.day.strftime("%d") + '/0/' + str(LocID)) 


@login_required(login_url='/home/')
def orders_payroll(request, dailyID, LocID):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    daily = DailyMob.objects.filter(id = dailyID).first()    
    loca = list(catalogModel.Locations.objects.all().exclude(LocationID = daily.Location.LocationID))
    
    WOdailyList = list(DailyMob.objects.filter(Period = daily.Period, day = daily.day, Location__LocationID = LocID).exclude(woID = None).values_list('woID__id',flat=True))


    wo = catalogModel.workOrder.objects.filter(Status__in = [1,2]).exclude(Location__in = loca).exclude(id__in = WOdailyList )
    context = {}    
    context["orders"] = wo
    context["emp"] = emp    
    context["daily"] = dailyID
    context["dailyObj"] = daily
    context["selectedLocation"] = LocID

    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context["period"] = per
    #context["WOdailyList"] = WOdailyList

    return render(request, "mobile/orders_payroll.html", context)

def update_ptp_Emp(dailyID, split):
    emp_ptp = 0
    crew = DailyMob.objects.filter(id = dailyID).first()
    if crew:
        itemCount = 0
        itemSum = 0
        
        if bool(split):
            empCount = DailyMobEmployee.objects.filter(DailyID = crew).count()
           
            if empCount > 0:
                empPtp =  validate_decimals(100 / empCount)
                empList = DailyMobEmployee.objects.filter(DailyID = crew)

                for empl in empList:
                    empD = DailyMobEmployee.objects.filter(id = empl.id).first()
                    empD.per_to_pay = empPtp
                    empD.save()
      

        itemCount = DailyMobItem.objects.filter(DailyID = crew).count()
        if itemCount > 0:            
            itemList = DailyMobItem.objects.filter(DailyID = crew)

            for iteml in itemList:
                itemSum += iteml.total 

        # Deactivate Own Vehicle per Crew
        """if crew.own_vehicle != None:
            ovp = (itemSum * crew.own_vehicle) / 100
            itemSum += ovp         """          
                                      
        empList = DailyMobEmployee.objects.filter(DailyID = crew)
        
        for empl in empList:
            rt_pay = 0
            ot_pay = 0
            dt_pay = 0
            empRate = 0
            production = 0
            ovEmp = 0
            
            empD = DailyMobEmployee.objects.filter(id = empl.id).first()    
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

# ****************************************************************************
def employee_list(request):
    emp =  catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    
    context["dataset"] = Timesheet.objects.filter(EmployeeID = emp, Status__in = (1,5)).order_by('-date').values()
    
    context["emp"]= emp

    return render(request, "mobile/employee_list.html", context)

@login_required(login_url='/home/')
def employee_submitted_list(request):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    
    context["dataset"] = Timesheet.objects.filter(EmployeeID = emp, Status__in = (2,3,4)).order_by('-date').values()
    
    context["emp"]= emp

    return render(request, "mobile/employee_submitted_list.html", context)



@login_required(login_url='/home/')
def create(request):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}


    
    form = TimesheetForm(request.POST or None, initial = {'EmployeeID': emp})
    
    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()   

        if request.POST.get('newstatus') != '' :
            form.instance.Status = request.POST.get('newstatus')

        if request.POST.get('newTotalM') != '' :    
            form.instance.total_mileage = request.POST.get('newTotalM')
        else:
            form.instance.total_mileage = 0

        form.instance.total_mileage = validate_decimals(validate_decimals(form.cleaned_data["end_mileage"]) - validate_decimals(form.cleaned_data["start_mileage"]))
        form.instance.total_hours = calculate_hours(form.instance.start_time, form.instance.end_time, form.instance.start_lunch_time, form.instance.end_lunch_time)
        form.save() 

        # Return to Locations List
        return HttpResponseRedirect('/mobile/employee_list/')
       
 
    context['form']= form
    context["emp"] = emp
    return render(request, "mobile/timesheet.html", context)


@login_required(login_url='/home/')
def update(request, id):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    obj = get_object_or_404(Timesheet, id = id)

    if int(obj.Status) >= 2 and int(obj.Status) <= 4:
        form = TimesheetDisabledForm(request.POST or None, instance = obj)
    else: 
        form = TimesheetForm(request.POST or None, instance = obj)

    if form.is_valid():
        if request.POST.get('newstatus') != '' :
            form.instance.Status = request.POST.get('newstatus')

        form.instance.total_mileage = validate_decimals(validate_decimals(form.instance.end_mileage) - validate_decimals(form.instance.start_mileage))
        form.instance.total_hours = calculate_hours(form.instance.start_time, form.instance.end_time, form.instance.start_lunch_time, form.instance.end_lunch_time)
        form.instance.updatedBy = request.user.username
        form.instance.updated_date = datetime.now()    
        form.save()
        # Return to Locations List
        return HttpResponseRedirect('/mobile/employee_list/')

    context["object"] = obj     
    context['form']= form
    context["emp"] = emp
    context["id"] = id
    return render(request, "mobile/timesheet.html", context)


"""
**************** SUPERVISOR *********************************
"""

@login_required(login_url='/home/')
def supervisor_list(request):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    status = 0
    dateS = ""
    dateS2 = ""
    loc = "0"
    employee = "0"

    locationList = catalogModel.Locations.objects.all()
    empList = catalogModel.Employee.objects.all()


    #Getting the locations assigned to the Actual User
    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append(emp.Location.LocationID)

    for i in locaList:
        locationList.append(i.LocationID.LocationID)

    location = catalogModel.Locations.objects.filter(LocationID__in = locationList)
    context["locationList"] = location
    


    if request.method == "POST":
        dateSelected =  request.POST.get('date')
        dateSelected2 = request.POST.get('date2')
        # dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
        # dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()
        status = request.POST.get('status')        
        loc = request.POST.get('location') 
        employee = request.POST.get('emp')

        if loc == None or loc =="":
            loc = "0"
        
        if emp == None or emp =="":
            emp = "0"

        if request.user.is_staff or emp.is_superAdmin:
            if status == "0" and loc == "0" and employee == "0":
                #ts = DailyMob.objects.filter(Status__in = (2,3), day__range=[dateS, dateS2])
                ts = DailyMob.objects.filter( Status__in = (2,3))
            else:
                if status != "0" and loc != "0" and employee != "0":

                    empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                    #ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, day__range=[dateS, dateS2])  
                    ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, created_by = empFilter.user)  
                else:
                    if status != "0" and loc!= "0":    
                        ts = DailyMob.objects.filter( Status = status , Location__LocationID = loc)            
                    else:    
                        if  status != "0" and employee != "0":
                            empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                            ts = DailyMob.objects.filter(Status = status , created_by = empFilter.user)   
                        else:
                            if  loc != "0" and employee != "0":
                                empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                ts = DailyMob.objects.filter(Location__LocationID = loc, created_by = empFilter.user)   
                            else:
                                if status != "0":
                                    ts = DailyMob.objects.filter(Status = status ) 
                                else:
                                    if loc != "0":
                                        ts = DailyMob.objects.filter(Location__LocationID = loc) 
                                    else:
                                        empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                        ts = DailyMob.objects.filter(created_by = empFilter.user) 
        elif emp.is_manager:
            if status == "0" and loc == "0" and employee == "0":
                #ts = DailyMob.objects.filter(Status__in = (2,3), day__range=[dateS, dateS2])
                ts = DailyMob.objects.filter(Location__LocationID__in = locationList, Status__in = (2,3))
            else:
                if status != "0" and loc != "0" and employee != "0":

                    empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                    #ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, day__range=[dateS, dateS2])  
                    ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, created_by = empFilter.user)  
                else:
                    if status != "0" and loc!= "0":    
                        ts = DailyMob.objects.filter( Status = status , Location__LocationID = loc)            
                    else:    
                        if  status != "0" and employee != "0":
                            empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                            ts = DailyMob.objects.filter(Location__LocationID__in = locationList, Status = status , created_by = empFilter.user)   
                        else:
                            if  loc != "0" and employee != "0":
                                empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                ts = DailyMob.objects.filter(Location__LocationID = loc, created_by = empFilter.user)   
                            else:
                                if status != "0":
                                    ts = DailyMob.objects.filter(Location__LocationID__in = locationList, Status = status ) 
                                else:
                                    if loc != "0":
                                        ts = DailyMob.objects.filter(Location__LocationID = loc) 
                                    else:
                                        empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                        ts = DailyMob.objects.filter(Location__LocationID__in = locationList, created_by = empFilter.user) 
        else:
            if status == "0" and loc == "0" and employee == "0":
                #ts = DailyMob.objects.filter(Status__in = (2,3), day__range=[dateS, dateS2])
                ts = DailyMob.objects.filter(supervisor = emp.employeeID, Status__in = (2,3))
            else:
                if status != "0" and loc != "0" and employee != "0":

                    empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                    #ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, day__range=[dateS, dateS2])  
                    ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, created_by = empFilter.user)  
                else:
                    if status != "0" and loc!= "0":    
                        ts = DailyMob.objects.filter(supervisor = emp.employeeID, Status = status , Location__LocationID = loc)            
                    else:    
                        if  status != "0" and employee != "0":
                            empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                            ts = DailyMob.objects.filter(supervisor = emp.employeeID,Status = status , created_by = empFilter.user)   
                        else:
                            if  loc != "0" and employee != "0":
                                empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                ts = DailyMob.objects.filter(supervisor = emp.employeeID,Location__LocationID = loc, created_by = empFilter.user)   
                            else:
                                if status != "0":
                                    ts = DailyMob.objects.filter(supervisor = emp.employeeID,Status = status ) 
                                else:
                                    if loc != "0":
                                        ts = DailyMob.objects.filter(supervisor = emp.employeeID,Location__LocationID = loc) 
                                    else:
                                        empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                        ts = DailyMob.objects.filter(supervisor = emp.employeeID, created_by = empFilter.user) 
    else:
        if request.user.is_staff or emp.is_superAdmin:
            ts = DailyMob.objects.filter()
        elif emp.is_manager:
            ts = DailyMob.objects.filter(Location__LocationID__in = locationList, Status__in = (2,3))
        else:
            ts = DailyMob.objects.filter(supervisor = emp.employeeID , Status__in = (2,3))


    supervisor_name_subquery = catalogModel.Employee.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name')
    ).filter(employeeID=Cast(OuterRef('supervisor'), IntegerField())).values('full_name')[:1]

    ts = ts.annotate(
        total_payout=Sum('dailymobemployee__payout'),
        supervisor_name=Subquery(supervisor_name_subquery, output_field=CharField())
    )
    
    
        
    context["origen"] = "supervisor_list"
    context["emp"] = emp
    context["dataset"] = ts
    context["location"]=locationList
    context["empList"]=empList
    context["selectLoc"]=loc
    context["selectEstatus"] = status 
    context["selectEmployee"] = employee 
    context["dateSelected"] =  dateS
    context["dateSelected2"] =  dateS2


        
    return render(request, "mobile/supervisor_list.html", context)




@login_required(login_url='/home/')
def createBySupervisor(request):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    form = TimesheetSuperForm(request.POST or None)

    if form.is_valid():
        form.instance.createdBy = request.user.username
        form.instance.created_date = datetime.now()    
        form.instance.total_mileage = validate_decimals(validate_decimals(form.instance.end_mileage) - validate_decimals(form.instance.start_mileage))
        form.instance.total_hours = calculate_hours(form.instance.start_time, form.instance.end_time, form.instance.start_lunch_time, form.instance.end_lunch_time)
        form.save()
        # Return to Locations List
        return HttpResponseRedirect('/mobile/supervisor_list/')

         
    context['form']= form
    context["emp"] = emp
    return render(request, "mobile/supervisor_timesheet.html", context)

@login_required(login_url='/home/')
def update_status(request, id, status):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    obj = get_object_or_404(Timesheet, id = id)
    
    if obj:
        obj.updatedBy = request.user.username
        obj.updated_date = datetime.now()    
        obj.Status = status
        obj.save()
        # Return to Locations List
        return HttpResponseRedirect('/mobile/supervisor_list/')

        
    context["emp"] = emp
    context["id"] = id
    return render(request, "mobile/timesheet.html/" + str(id), context)

@login_required(login_url='/home/')
def updateBySuper(request, id):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}

    obj = get_object_or_404(Timesheet, id = id)

    if obj.Status == 4:
        form = TimesheetSuperFormApproved(request.POST or None, instance = obj)
    else:
        form = TimesheetSuperForm(request.POST or None, instance = obj)

    if form.is_valid():
    
        if request.POST.get('newstatus') != '' :
                form.instance.Status = request.POST.get('newstatus')

        form.instance.total_mileage = validate_decimals(validate_decimals(form.instance.end_mileage) - validate_decimals(form.instance.start_mileage))
        form.instance.total_hours = calculate_hours(form.instance.start_time, form.instance.end_time, form.instance.start_lunch_time, form.instance.end_lunch_time)

        form.instance.updatedBy = request.user.username
        form.instance.updated_date = datetime.now()    
        form.save()
        # Return to Locations List
        return HttpResponseRedirect('/mobile/supervisor_list/')

         
    context['obj']= obj
    context['form']= form
    context["emp"] = emp
    context["id"] = id
    return render(request, "mobile/supervisor_timesheet.html", context)


def reject_timesheet(request, id, origen):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context ={}
    context["per"] = per

    obj = get_object_or_404(DailyMob, id = id)

    superV = catalogModel.Employee.objects.filter(is_supervisor=True)

    form = DailyMobRejectedForm(request.POST or None, instance = obj) 
    
    dailyEmp = DailyMobEmployee.objects.filter(DailyID = obj)

    dailyItem = DailyMobItem.objects.filter(DailyID = obj)

    dailyTotal = 0
    ovT = 0
    for di in dailyItem:
        dailyTotal += di.total 


    if obj.own_vehicle != None:
        ovT = (dailyTotal * obj.own_vehicle) / 100
    
    granTotal = dailyTotal + ovT

    context["dailyItem"] = dailyItem
    context["TotalItem"] = dailyTotal
    context["ovTotal"] = ovT
    context["GranTotalItem"] = granTotal
    context["id"] = id

    is_error = False
    errorMessage = ""

    if form.is_valid():
        
        form.instance.Status = 5
        form.instance.rejected_by = request.user.username
        form.instance.rejected_date = datetime.now()
        form.save()

        day = obj.day.strftime("%m-%d-%Y")

        for emp in dailyEmp:
            empD = catalogModel.Employee.objects.filter(employeeID = emp.EmployeeID.employeeID).first()

            
            if empD:
                # Send email to notify rejection
                message_body = f" <html> <p>Hello {empD.first_name} {empD.last_name}, <u></u><u></u></p>\n\n" \
                    f"<p>I would like to bring to your attention that the <strong>daily form submitted on {day}</strong> has been found to contain\n" \
                    f"errors and unfortunately, has been rejected. <u></u><u></u></p>\n\n" \
                    f"<p>Please review the comments that the supervisor wrote before making any corrections.\n\n" \
                    f"If you have any question, please contact your supervisor.<u></u><u></u></p>\n\n" \
                    f"<p>HHRR. </p></html>\n\n" \

                if empD.email != None:
                    is_error, errorMessage = send_email_with_attachment(
                        subject="Action Required: Daily Form Submission Rejected",
                        message=message_body,
                        html_message=message_body,
                        recipient_list=[empD.email],)
                    
                    if is_error:
                        errorMessage +=  "Error sending email to employee: " + empD.email + " - " + errorMessage
                    
                    
            
        if is_error:
            context["errorMessage"] = errorMessage            
        else:
            # Return to Locations List
            return HttpResponseRedirect('/mobile/supervisor_list/')     
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Error en {field}: {error}")
                errorMessage += f"Error en {field}: {error}"
        if form.non_field_errors():
            print("Errores no relacionados con campos:")
            errorMessage += f"Errores no relacionados con campos:\n"
            for error in form.non_field_errors():
                errorMessage += error
        
        context["errorMessage"] = errorMessage                                                                            

    #Adding the documents Maps
    dailyDocs = DailyMobDocs.objects.filter(DailyID = obj, docType=1).order_by('created_date')

    #Adding the documents Pictures
    dailyDocsPic = DailyMobDocs.objects.filter(DailyID = obj, docType=2).order_by('created_date')

    #Adding the documents Material Backup
    dailyDocsMB = DailyMobDocs.objects.filter(DailyID = obj, docType=3).order_by('created_date')
    
    context["dailyDocs"] = dailyDocs
    context["dailyDocsPic"] = dailyDocsPic
    context["dailyDocsMB"] = dailyDocsMB
    context["origen"] = origen

    context['form']= form     
    context["emp"] = emp
    context["dailyEmp"] = dailyEmp
    context["dailyItem"] = dailyItem
    context["superV"] = superV
    context["dailyWO"] = obj
    context["id"] = id
    return render(request, "mobile/reject_timesheet.html", context)




@login_required(login_url='/home/')
@require_POST
def save_daily_comment(request, daily_id):
    """
    Receives a POST with 'comment' and saves it to DailyMob.comments field.
    """
    comment = request.POST.get('comment','').strip()
    if comment is None or comment.strip() == "":
        return JsonResponse({'success': False, 'message': 'No comment provided.'})
    daily = get_object_or_404(DailyMob, id=daily_id)
    daily.daily_comments = comment
    daily.save()
    return JsonResponse({'success': True, 'message': 'Comment saved.'})

@login_required(login_url='/home/')
@transaction.atomic
def approve_timesheet(request, id):
    
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context ={}
    context["per"] = per

    obj = get_object_or_404(DailyMob, id = id)

    superV = catalogModel.Employee.objects.filter(is_supervisor=True)

    form = DailyMobApprovedForm(request.POST or None, instance = obj) 
    
    dailyEmp = DailyMobEmployee.objects.filter(DailyID = obj)

    dailyItem = DailyMobItem.objects.filter(DailyID = obj)

    #Adding the documents Maps
    dailyDocs = DailyMobDocs.objects.filter(DailyID = obj).order_by('created_date')

    #Adding the documents Maps
    dailyDocsMap = DailyMobDocs.objects.filter(DailyID = obj, docType=1).order_by('created_date')

    #Adding the documents Pictures
    dailyDocsPic = DailyMobDocs.objects.filter(DailyID = obj, docType=2).order_by('created_date')

    #Adding the documents Material Backup
    dailyDocsMB = DailyMobDocs.objects.filter(DailyID = obj, docType=3).order_by('created_date')
    

    dailyTotal = 0
    ovT = 0
    for di in dailyItem:
        dailyTotal += di.total 


    if obj.own_vehicle != None:
        ovT = (dailyTotal * obj.own_vehicle) / 100
    
    granTotal = dailyTotal + ovT

    context["dailyItem"] = dailyItem
    context["daily"] = obj
    context["dailyDocs"] = dailyDocsMap
    context["dailyDocsPic"] = dailyDocsPic
    context["dailyDocsMB"] = dailyDocsMB

    context["TotalItem"] = dailyTotal
    context["ovTotal"] = ovT
    context["GranTotalItem"] = granTotal

    is_error = False

    if form.is_valid():
        try:
            form.instance.daily_date = datetime.now()           
            form.save()
            
            #Validate if the id Mobile Exists in the Daily Table
            exists_in_daily = catalogModel.Daily.objects.filter(mobile_id=obj.id).exists()
            if exists_in_daily:
                
                form.instance.Status = 4
                form.instance.approved_by = request.user.username
                form.instance.approved_date = datetime.now()
                form.save()
                
                context['form']= form     
                context["emp"] = emp
                context["dailyEmp"] = dailyEmp
                context["dailyItem"] = dailyItem
                context["superV"] = superV
                context["dailyWO"] = obj
                context["id"] = id
                context["errorMessage"] = "Error: This timesheet has already been approved." 
                #return render(request, "mobile/approve_timesheet.html", context)
                return HttpResponseRedirect('/mobile/supervisor_list/')

            #Get the pdf daily Html
            htlmDaily = request.POST.get('htmlDaily')

            #convert the html to pdf
            is_success, errorMessage, htlmDaily = html_to_pdf_save(htlmDaily, obj)

            if not is_success:
                context['form']= form     
                context["emp"] = emp
                context["dailyEmp"] = dailyEmp
                context["dailyItem"] = dailyItem
                context["superV"] = superV
                context["dailyWO"] = obj
                context["id"] = id
                context["errorMessage"] = errorMessage 
                return render(request, "mobile/approve_timesheet.html", context)

            crewNumber = catalogModel.Daily.objects.filter( Period = per, day = obj.day, Location = obj.Location).last()
            if crewNumber:
                crewNo = crewNumber.crew
            else:
                crewNo = 0

        
            newDaily = catalogModel.Daily.objects.create(
                crew = int(crewNo) + 1,
                Location = obj.Location,
                Period = obj.Period,
                day = obj.day,
                woID = obj.woID,
                supervisor = obj.supervisor,
                own_vehicle = obj.own_vehicle, 
                total_pay = obj.total_pay,
                split_paymet = obj.split_paymet,
                pdfDaily = obj.pdfDaily,
                created_date = obj.created_date,
                approved_by =  request.user.username,
                approved_date = datetime.now(),
                sent_by = obj.created_by,
                crew_by_user = obj.crew_by_user,
                mobile_id = obj.id,
                mobile_tech_comments = obj.daily_comments,
                mobile_sup_comments = obj.comments,
            )
            
            

            for emp in dailyEmp:
                catalogModel.DailyEmployee.objects.create(                
                    DailyID = newDaily,
                    EmployeeID = emp.EmployeeID,
                    per_to_pay =  emp.per_to_pay,
                    on_call = emp.on_call,
                    bonus =  emp.bonus,
                    start_time = emp.start_time,
                    start_lunch_time = emp.start_lunch_time,
                    end_lunch_time = emp.end_lunch_time,
                    end_time = emp.end_time,
                    total_hours = emp.total_hours,
                    regular_hours = emp.regular_hours,
                    rt_pay = emp.rt_pay,
                    ot_hour = emp.ot_hour,
                    ot_pay = emp.ot_pay,
                    double_time = emp.double_time,
                    dt_pay = emp.dt_pay,
                    own_vehicle_pay = emp.own_vehicle_pay,
                    is_own_vehicle = emp.is_own_vehicle,
                    payout =  emp.payout,
                    emp_rate = emp.emp_rate,
                    production = emp.production, 
                    billableHours = emp.billableHours,
                    estimate = None,
                    invoice = None,
                    Status = 1,   
                    created_date = datetime.now()
                )


            for item in dailyItem:
                catalogModel.DailyItem.objects.create(
                    DailyID = newDaily,
                    itemID = item.itemID,
                    quantity = item.quantity,
                    price = item.price,
                    total = item.total,
                    emp_payout = item.emp_payout,      
                    estimate = None,
                    invoice = None,
                    Status = 1,   
                    isAuthorized = False,
                    authorized_date = None,
                    autorizedID = None,
                    created_date = datetime.now(),
                    createdBy = request.user.username,
                    updated_date = None,
                    updatedBy = None
                )

            for doc in dailyDocs:
                catalogModel.DailyDocs.objects.create(
                    DailyID = newDaily,
                    docType = doc.docType,
                    docName = doc.docName,
                    docDescription = doc.docDescription,
                    document = doc.document,
                    Status = 1,   
                    isAuthorized = False,
                    authorized_date = None,
                    autorizedID = None,
                    created_date = datetime.now(),
                    createdBy = request.user.username,
                    updated_date = None,
                    updatedBy = None
                )

            
            
            form.instance.Status = 4
            form.instance.approved_by = request.user.username
            form.instance.approved_date = datetime.now()
            form.save()

            #If Daily is Ready to Bill Update the Work Order Status to 7 - Ready to Bill
            if obj.woID != None: 
                if obj.daily_rtb or obj.daily_rtb_pep:                           
                    wo = catalogModel.workOrder.objects.filter(id = obj.woID.id).first()
                    if wo:                                              
                        if obj.daily_rtb:
                            wo.Status = '7'  #Ready to Bill
                        elif obj.daily_rtb_pep:
                            wo.Status = '8'  #Ready to Bill PEP
                        
                        wo.save()


            # Send email to notify approval
            for emp in dailyEmp:
                empD = catalogModel.Employee.objects.filter(employeeID = emp.EmployeeID.employeeID).first()
                day = obj.day.strftime("%m-%d-%Y")

                if empD:
                    # Send email to notify rejection
                    message_body = f" <html> <p>Hello {empD.first_name} {empD.last_name}, <u></u><u></u></p>\n\n" \
                        f"<p>Attached you will find the daily report dated <strong> {day}</strong>. \n" \
                        f"Please review it and let me know if you have any questions or issues.</p>\n\n" \
                        f"<p>Best regards, <u></u><u></u></p>\n\n" \
                        f"<p>HR Department </p></html>\n\n" \
                        
                    message_body += htlmDaily

                    if empD.email != None:
                        is_error, errorMessage = send_email_with_attachment(
                            subject="Daily Report – " + obj.day.strftime("%m-%d-%Y"),
                            message=message_body,
                            html_message=message_body,
                            recipient_list=[empD.email])
                    
                    
            
            if is_error:
                context["errorMessage"] = errorMessage            
            else:
                # Return to Locations List
                return HttpResponseRedirect('/mobile/supervisor_list/')

        except Exception as e:
            raise


        # Return to Locations List
        return HttpResponseRedirect('/mobile/supervisor_list/')

    context['form']= form     
    context["emp"] = emp
    context["dailyEmp"] = dailyEmp
    context["dailyItem"] = dailyItem
    context["superV"] = superV
    context["dailyWO"] = obj
    context["id"] = id
    return render(request, "mobile/approve_timesheet.html", context)


@login_required(login_url='/home/')
@transaction.atomic
@csrf_exempt 
def save_pdf_daily(request, id):
    
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = catalogModel.period.objects.filter(status__in=(1,2)).first()
    context ={}
    context["per"] = per

    obj = get_object_or_404(DailyMob, id = id)


    if request.method == 'POST' and request.FILES.get('pdfDaily'):

        pdf_file = request.FILES['pdfDaily']
        pdf_file.name = f'daily_report_{obj.crew_by_user}.pdf'

        obj.pdfDaily.save(
            pdf_file.name,
            ContentFile(pdf_file.read()),
            save=True
        )

        return JsonResponse({'status': 'success'})
  
    context["emp"] = emp
    context["dailyWO"] = obj
    context["id"] = id

    return JsonResponse({'status': 'error'}, status = 400)


"""
****************  REPORTS *********************************
"""
@login_required(login_url='/home/')
def report_list(request):
    
    context ={}
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context["emp"]= emp

    status = 0
    dateS = ""
    dateS2 = ""
    loc = "0"
    employee = "0"
    radio = None

    locationList = catalogModel.Locations.objects.all()
    empList = catalogModel.Employee.objects.all()

    if request.method == "POST":
        dateSelected =  request.POST.get('date')
        dateSelected2 = request.POST.get('date2')
        dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
        dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()
        status = request.POST.get('status')   
        employee =  request.POST.get('emp') 
        radio = request.POST.get('searchBy')

        loc = request.POST.get('location') 
        
        if loc == None or loc =="":
            loc = "0"
        
        if emp == None or emp =="":
            emp = "0"

        if radio == "byWork":
            if status == "0" and loc == "0" and employee == "0":
                ts = Timesheet.objects.filter(Status__in = (2,3), date__range=[dateS, dateS2])
            else:
                if status != "0" and loc != "0" and employee != "0":
                    ts = Timesheet.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, date__range=[dateS, dateS2])  
                else:
                    if status != "0" and loc!= "0":    
                        ts = Timesheet.objects.filter(Status = status , Location__LocationID = loc, date__range=[dateS, dateS2])            
                    else:    
                        if  status != "0" and employee != "0":
                            ts = Timesheet.objects.filter(Status = status , EmployeeID__employeeID = employee, date__range=[dateS, dateS2])   
                        else:
                            if  loc != "0" and employee != "0":
                                ts = Timesheet.objects.filter(Location__LocationID = loc, EmployeeID__employeeID = employee, date__range=[dateS, dateS2])   
                            else:
                                if status != "0":
                                    ts = Timesheet.objects.filter(Status = status , date__range=[dateS, dateS2]) 
                                else:
                                    if loc != "0":
                                        ts = Timesheet.objects.filter(Location__LocationID = loc, date__range=[dateS, dateS2]) 
                                    else:
                                        ts = Timesheet.objects.filter(EmployeeID__employeeID = employee, date__range=[dateS, dateS2])  
        elif radio == "byCreated":
            if status == "0" and loc == "0" and employee == "0":
                ts = Timesheet.objects.filter(Status__in = (2,3), created_date__date__range=[dateS, dateS2])
            else:
                if status != "0" and loc != "0" and employee != "0":
                    ts = Timesheet.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])  
                else:
                    if status != "0" and loc!= "0":    
                        ts = Timesheet.objects.filter(Status = status , Location__LocationID = loc, created_date__date__range=[dateS, dateS2])            
                    else:    
                        if  status != "0" and employee != "0":
                            ts = Timesheet.objects.filter(Status = status , EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])   
                        else:
                            if  loc != "0" and employee != "0":
                                ts = Timesheet.objects.filter(Location__LocationID = loc, EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])   
                            else:
                                if status != "0":
                                    ts = Timesheet.objects.filter(Status = status , created_date__date__range=[dateS, dateS2]) 
                                else:
                                    if loc != "0":
                                        ts = Timesheet.objects.filter(Location__LocationID = loc, created_date__date__range=[dateS, dateS2]) 
                                    else:
                                        ts = Timesheet.objects.filter(EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])  
    else:
        ts = Timesheet.objects.filter(Status = -1)
        
    context["dataset"] = ts
    context["radio"] = radio
    context["location"]=locationList
    context["empList"]=empList
    context["selectLoc"]=loc
    context["selectEstatus"] = status 
    context["selectEmployee"] = employee 
    context["dateSelected"] =  dateS
    context["dateSelected2"] =  dateS2


    return render(request, "mobile/report_list.html", context)


@login_required(login_url='/home/')
def get_report_list(request, dateSelected, dateSelected2, status, location, employee, type):
    

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('employee-report', cell_overwrite_ok = True) 

    

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
    
                              
    ws.write_merge(3, 3, 0, 14, 'Employee Report ' + str(datetime.strftime(dateS, "%m/%d/%Y")) + ' - ' + str(datetime.strftime(dateS2, "%m/%d/%Y")),font_title2)   


                   

    columns = ['Date','Created Date' ,'Name', 'Location', 'Clock In', 'Lunch Start','Lunch End','Clock Out','Hours worked', 'Starting Mileage','Ending Mileage','Total Mileage','Status', 'Updated By', 'Comments' ] 

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_title) # at 0 row 0 column 
      

    
    #ordenes = woInvoice.objects.filter(created_date__year = datetime.strftime(dateS, '%Y'), created_date__month = datetime.strftime(dateS, '%m'))


    """if status == "0" and location == "0":
        ts = Timesheet.objects.filter(date__range=[dateS, dateS2])
    else:
        if status != "0" and location != "0":
            ts = Timesheet.objects.filter(Status = status, Location__LocationID = location, date__range=[dateS, dateS2])  
        else:
            if status != "0":    
                ts = Timesheet.objects.filter(Status = status , date__range=[dateS, dateS2])                     
            else:
                ts = Timesheet.objects.filter(Location__LocationID = location , date__range=[dateS, dateS2])  """


    if type =="byWork":      
        if status == "0" and location == "0" and employee == "0":
            ts = Timesheet.objects.filter(Status__in = (2,3), date__range=[dateS, dateS2])
        else:
            if status != "0" and location != "0" and employee != "0":
                ts = Timesheet.objects.filter(Status = status, Location__LocationID = location, EmployeeID__employeeID = employee, date__range=[dateS, dateS2])  
            else:
                if status != "0" and location!= "0":    
                    ts = Timesheet.objects.filter(Status = status , Location__LocationID = location, date__range=[dateS, dateS2])            
                else:    
                    if  status != "0" and employee != "0":
                        ts = Timesheet.objects.filter(Status = status , EmployeeID__employeeID = employee, date__range=[dateS, dateS2])   
                    else:
                        if  location != "0" and employee != "0":
                            ts = Timesheet.objects.filter(Location__LocationID = location, EmployeeID__employeeID = employee, date__range=[dateS, dateS2])   
                        else:
                            if status != "0":
                                ts = Timesheet.objects.filter(Status = status , date__range=[dateS, dateS2]) 
                            else:
                                if location != "0":
                                    ts = Timesheet.objects.filter(Location__LocationID = location, date__range=[dateS, dateS2]) 
                                else:
                                    ts = Timesheet.objects.filter(EmployeeID__employeeID = employee, date__range=[dateS, dateS2])  
    elif type=="byCreated":
        if status == "0" and location == "0" and employee == "0":
            ts = Timesheet.objects.filter(Status__in = (2,3), created_date__date__range=[dateS, dateS2])
        else:
            if status != "0" and location != "0" and employee != "0":
                ts = Timesheet.objects.filter(Status = status, Location__LocationID = location, EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])  
            else:
                if status != "0" and location!= "0":    
                    ts = Timesheet.objects.filter(Status = status , Location__LocationID = location, created_date__date__range=[dateS, dateS2])            
                else:    
                    if  status != "0" and employee != "0":
                        ts = Timesheet.objects.filter(Status = status , EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])   
                    else:
                        if  location != "0" and employee != "0":
                            ts = Timesheet.objects.filter(Location__LocationID = location, EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])   
                        else:
                            if status != "0":
                                ts = Timesheet.objects.filter(Status = status , created_date__date__range=[dateS, dateS2]) 
                            else:
                                if location != "0":
                                    ts = Timesheet.objects.filter(Location__LocationID = location, created_date__date__range=[dateS, dateS2]) 
                                else:
                                    ts = Timesheet.objects.filter(EmployeeID__employeeID = employee, created_date__date__range=[dateS, dateS2])  


       
    for item in ts:
        row_num += 1
        ws.write(row_num, 0, item.date.strftime("%m/%d/%Y"), font_style) # at 0 row 0 column 
        ws.write(row_num, 1, item.created_date.strftime("%m/%d/%Y"), font_style) # at 0 row 0 column 
        ws.write(row_num, 2, item.EmployeeID.first_name + ' ' + item.EmployeeID.last_name , font_style) # at 0 row 0 column  
        ws.write(row_num,3, item.Location.LocationID + '-' + item.Location.name, font_style) # at 0 row 0 column        
        ws.write(row_num, 4, item.start_time, font_style)
        ws.write(row_num, 5, item.start_lunch_time, font_style)
        ws.write(row_num, 6, item.end_lunch_time, font_style)
        ws.write(row_num, 7, item.end_time, font_style)
        ws.write(row_num, 8, item.total_hours, font_style)
        ws.write(row_num, 9, item.start_mileage, font_style)
        ws.write(row_num, 10, item.end_mileage, font_style)
        ws.write(row_num, 11, item.total_mileage, font_style)

        if item.Status == 1:
            ws.write(row_num, 12, 'Draft', font_style)
        elif item.Status == 2:
            ws.write(row_num, 12, 'Sent', font_style)
        elif item.Status == 3:
            ws.write(row_num, 12, 'Pending', font_style)
        elif item.Status == 4:
            ws.write(row_num, 12, 'Approved', font_style)
        elif item.Status == 5:
            ws.write(row_num, 12, 'Rejected', font_style)

        ws.write(row_num, 13, item.updatedBy, font_style)
        ws.write(row_num, 14, item.comments, font_style)
            


    ws.col(2).width = 12000
    ws.col(3).width = 6000
    ws.col(4).width = 3000
    ws.col(5).width = 3000
    ws.col(6).width = 3000
    ws.col(7).width = 3000
    ws.col(8).width = 4000
    ws.col(9).width = 4000
    ws.col(10).width = 4000
    ws.col(11).width = 7000
    ws.col(12).width = 6000
    ws.col(13).width = 3000
    ws.col(14).width = 8000
 

    filename = 'Employee report ' + dateSelected + '.xls'
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename 

    wb.save(response)

    return response


"""
*********************************** ADMIN ********************************************************
"""
@login_required(login_url='/home/')
def approved_dailies(request):
    emp = catalogModel.Employee.objects.filter(user__username__exact = request.user.username).first()
    context ={}
    status = 0
    dateS = ""
    dateS2 = ""
    loc = "0"
    employee = "0"

    locationList = catalogModel.Locations.objects.all()
    empList = catalogModel.Employee.objects.all()


    #Getting the locations assigned to the Actual User
    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
                
    locationList = []
    locationList.append(emp.Location.LocationID)

    for i in locaList:
        locationList.append(i.LocationID.LocationID)


    current_period = catalogModel.period.objects.filter(status__in=(1,2)).first()
    


    if request.method == "POST":
        dateSelected =  request.POST.get('date')
        dateSelected2 = request.POST.get('date2')
        # dateS = datetime.strptime(dateSelected, '%Y-%m-%d').date()
        # dateS2 = datetime.strptime(dateSelected2, '%Y-%m-%d').date()
        status = 4 #request.POST.get('status')        
        loc = request.POST.get('location') 
        employee = "0"

        if loc == None or loc =="":
            loc = "0"
        
        if emp == None or emp =="":
            emp = "0"

        if request.user.is_staff or emp.is_superAdmin or emp.is_admin:
            if status == "0" and loc == "0" and employee == "0":
                #ts = DailyMob.objects.filter(Status__in = (2,3), day__range=[dateS, dateS2])
                ts = DailyMob.objects.filter( Status__in = (2,3))
            else:
                if status != "0" and loc != "0" and employee != "0":

                    empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                    #ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, day__range=[dateS, dateS2])  
                    ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, created_by = empFilter.user)  
                else:
                    if status != "0" and loc!= "0":    
                        ts = DailyMob.objects.filter( Status = status , Location__LocationID = loc, Period = current_period )            
                    else:    
                        if  status != "0" and employee != "0":
                            empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                            ts = DailyMob.objects.filter(Status = status , created_by = empFilter.user)   
                        else:
                            if  loc != "0" and employee != "0":
                                empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                ts = DailyMob.objects.filter(Location__LocationID = loc, created_by = empFilter.user)   
                            else:
                                if status != "0":
                                    ts = DailyMob.objects.filter(Status = status, Period = current_period, Location__LocationID__in = locationList ) 
                                else:
                                    if loc != "0":
                                        ts = DailyMob.objects.filter(Location__LocationID = loc, Period = current_period) 
                                    else:
                                        empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                        ts = DailyMob.objects.filter(created_by = empFilter.user, Period = current_period) 
        
        else:
            if status == "0" and loc == "0" and employee == "0":
                #ts = DailyMob.objects.filter(Status__in = (2,3), day__range=[dateS, dateS2])
                ts = DailyMob.objects.filter(supervisor = emp.employeeID, Status__in = (2,3))
            else:
                if status != "0" and loc != "0" and employee != "0":

                    empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                    #ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, EmployeeID__employeeID = employee, day__range=[dateS, dateS2])  
                    ts = DailyMob.objects.filter(Status = status, Location__LocationID = loc, created_by = empFilter.user)  
                else:
                    if status != "0" and loc!= "0":    
                        ts = DailyMob.objects.filter(supervisor = emp.employeeID, Status = status , Location__LocationID = loc)            
                    else:    
                        if  status != "0" and employee != "0":
                            empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                            ts = DailyMob.objects.filter(supervisor = emp.employeeID,Status = status , created_by = empFilter.user)   
                        else:
                            if  loc != "0" and employee != "0":
                                empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                ts = DailyMob.objects.filter(supervisor = emp.employeeID,Location__LocationID = loc, created_by = empFilter.user)   
                            else:
                                if status != "0":
                                    ts = DailyMob.objects.filter(supervisor = emp.employeeID,Status = status ) 
                                else:
                                    if loc != "0":
                                        ts = DailyMob.objects.filter(supervisor = emp.employeeID,Location__LocationID = loc) 
                                    else:
                                        empFilter = catalogModel.Employee.objects.filter(employeeID = employee ).first()

                                        ts = DailyMob.objects.filter(supervisor = emp.employeeID, created_by = empFilter.user) 
    else:
        if request.user.is_staff or emp.is_superAdmin or emp.is_admin:
            ts = DailyMob.objects.filter(Status = 4, Period = current_period, Location__LocationID__in = locationList)
        else:
            ts = DailyMob.objects.filter(supervisor = emp.employeeID , Status__in = (2,3))


    ts = ts.annotate(total_payout=Sum('dailymobemployee__payout'))

    #if emp:
    #    if emp.is_admin:
    locaList = catalogModel.employeeLocation.objects.filter(employeeID = emp)
        
    locationList = []
    locationList.append({'LocationID': emp.Location.LocationID, 'name':emp.Location.name })
    
    for i in locaList:
        locationList.append({'LocationID': i.LocationID.LocationID, 'name': i.LocationID.name} )
    #    else:
    #        locationList = catalogModel.Locations.objects.all()
    #else:
    #    locationList = catalogModel.Locations.objects.all()
        
    context["origen"] = "approved_dailies"    
    context["emp"] = emp
    context["dataset"] = ts
    context["location"]=locationList
    context["empList"]=empList
    context["selectLoc"]=loc
    context["selectEstatus"] = status 
    context["selectEmployee"] = employee 
    context["dateSelected"] =  dateS
    context["dateSelected2"] =  dateS2


        
    return render(request, "mobile/approved_dailies.html", context)



"""
****************  UTILITIES *********************************
"""
def validate_decimals(value):
    try:
        return round(float(str(value)), 2)
    except:
       return 0
    
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

def html_to_pdf_save(html_content, daily_obj):
    """
    Convert HTML content to PDF and save it to Daily model's pdfDaily field
    Args:
        html_content (str): Plain text HTML content
        daily_obj: Daily model instance to save the PDF to
    Returns:
        bool: True if successful, False otherwise
    """
    try:

        supervisor_name = ''
        if daily_obj.supervisor:
            supervisor = catalogModel.Employee.objects.filter(employeeID=daily_obj.supervisor).first()
            if supervisor:
                supervisor_name = f"{supervisor.first_name} {supervisor.last_name}"

        supervisor_signature_html = ""
        if daily_obj.supervisor:
            supervisor = catalogModel.Employee.objects.filter(employeeID=daily_obj.supervisor).first()
            if supervisor and hasattr(supervisor, 'signature') and supervisor.signature:
                try:
                    with open(supervisor.signature.path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                        supervisor_signature_html = f'<img src="data:image/png;base64,{encoded_string}" style="max-height: 30px;">'
                except Exception as e:
                    supervisor_signature_html = '<span style="color: #666; font-style: italic;">Signature not available</span>'
            else:
                supervisor_signature_html = '<span style="color: #666; font-style: italic;">No signature on file</span>'


                # Get related data
        dailyEmp = DailyMobEmployee.objects.filter(DailyID=daily_obj)
        dailyItem = DailyMobItem.objects.filter(DailyID=daily_obj)
        
        # Calculate totals
        dailyTotal = sum(di.total for di in dailyItem)
        ovT = (dailyTotal * daily_obj.own_vehicle / 100) if daily_obj.own_vehicle else 0
        granTotal = dailyTotal + ovT

        # Generate the complete HTML content
        html_content = f"""
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
            <tr style="background-color: #4a6baf; color: white;">
                <td style="padding: 2px; width: 40%;">PO #: {daily_obj.woID.PO if daily_obj.woID else ''}</td>
                <td style="padding: 2px; width: 35%;">Spectrum</td>
                <td style="padding: 2px; width: 25%; text-align: right;">PID#: {daily_obj.woID.prismID if daily_obj.woID else ''}</td>
            </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 0.5px solid #666;">
            <tr style="background-color: #f2f2f2;">
                <td style="border: 0.5px solid #666; padding: 4px; width: 40%;">Job Address</td>
                <td style="border: 0.5px solid #666; padding: 4px; width: 20%;">Date</td>
                <td style="border: 0.5px solid #666; padding: 4px; width: 10%;">Zone</td>
                <td style="border: 0.5px solid #666; padding: 4px; width: 30%;">Supervisor's Name</td>
            </tr>
            <tr>
                <td style="border: 0.5px solid #666; padding: 4px;">{daily_obj.woID.JobAddress if daily_obj.woID else ''}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{daily_obj.day.strftime('%m/%d/%Y')}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{daily_obj.daily_zone if daily_obj.daily_zone else '-'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">
                    {supervisor_name}
                </td>
            </tr>
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 0.5px solid #666;">
            <tr style="background-color: #f2f2f2;">
                <td style="border: 0.5px solid #666; padding: 4px;">Employee Crew Names</td>
                <td style="border: 0.5px solid #666; padding: 4px;">%</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Start Time</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Start Lunch</td>
                <td style="border: 0.5px solid #666; padding: 4px;">End Lunch</td>
                <td style="border: 0.5px solid #666; padding: 4px;">End Time</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Regular Hrs</td>
                <td style="border: 0.5px solid #666; padding: 4px;">O.T. Hrs</td>
                <td style="border: 0.5px solid #666; padding: 4px;">O.V.</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Signature</td>
            </tr>
        """

        # Add employee rows
        for emp in dailyEmp:
            signature_html = ""
            if hasattr(emp.EmployeeID, 'signature') and emp.EmployeeID.signature:
                try:
                    with open(emp.EmployeeID.signature.path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                        signature_html = f'<img src="data:image/png;base64,{encoded_string}" style="max-height: 30px;">'
                except Exception as e:
                    signature_html = '<span style="color: #666; font-style: italic;">Signature not available</span>'
            else:
                signature_html = '<span style="color: #666; font-style: italic;">No signature on file</span>'

            html_content += f"""
            <tr>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.EmployeeID}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.per_to_pay}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.start_time or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.start_lunch_time or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.end_lunch_time or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.end_time or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.regular_hours or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{emp.ot_hour or '&nbsp;'}</td>
                <td style="border: 0.5px solid #666; padding: 4px; text-align: center;">
                    {'X' if emp.is_own_vehicle else '&nbsp;'}
                </td>
                <td style="border: 0.5px solid #666; padding: 4px; text-align: center;">{signature_html}</td>
            </tr>
            """


        # Tech Comments
        tech_comments_html = ""
        if daily_obj.daily_comments:
            tech_comments_html = daily_obj.daily_comments
        

        # Add signature disclaimer
        html_content += f"""
            <tr>
                <td colspan="9" style="border: 0.5px solid #666; padding: 4px; font-size: 10px;">
                    By signing, the employee attests that the information above is true and accurate record of hours worked and that all breaks and read periods, as required by law, have been taken. Further acknowledge that any recorded overtime hours have been authorized.
                </td>
                <td style="border: 0.5px solid #666; padding: 4px; text-align: center;">
                    {supervisor_signature_html}<br>
                    Supervisor Signature
                </td>
            </tr>
        </table>

        <div style="margin: 10px 0; border-bottom: 0.5px solid #666;"></div>
        
        <div style="margin: 10px 0;">Comments / Notes:  {tech_comments_html}</div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 0.5px solid #666;">
            <tr style="background-color: #f2f2f2;">
                <td style="border: 0.5px solid #666; padding: 4px;">Code</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Description</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Qty</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Price</td>
                <td style="border: 0.5px solid #666; padding: 4px;">Total</td>
            </tr>
        """

        # Add items
        for item in dailyItem:
            html_content += f"""
            <tr>
                <td style="border: 0.5px solid #666; padding: 4px;">{item.itemID.item.itemID}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{item.itemID.item.description}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">{item.quantity}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">${item.emp_payout:.2f}</td>
                <td style="border: 0.5px solid #666; padding: 4px;">${item.total:.2f}</td>
            </tr>
            """
        
        empty_box = "&#x25A1;"  # □
        checked_box = "&#x2713;"  # ✓

        # Add totals
        html_content += f"""
            <tr style="background-color: #f2f2f2;">
                <td colspan="4" style="border: 0.5px solid #666; padding: 4px; text-align: right;"><strong>Total:</strong></td>
                <td style="border: 0.5px solid #666; padding: 4px;"><strong>${dailyTotal:.2f}</strong></td>
            </tr>
        </table>

        <div style="margin: 10px 0; border-bottom: 0.5px solid #666;"></div>

        <div style="background-color: #4a6baf; color: white; padding: 8px; margin: 10px 0;">Materials PO #</div>
        
        <div style="margin: 10px 0;">
            <strong>Check List</strong><br>
            {"Is this the only production for this project? &#x2713; Yes ☐ No<br>" if getattr(daily_obj, "daily_production", False) else "Is this the only production for this project? ☐ Yes &#x2713;  No<br>"}            
            Date:  {daily_obj.daily_date.strftime('%m/%d/%Y')} <br><br>

            ☐ Production &nbsp;&nbsp;&nbsp;
            ☐ As - Built &nbsp;&nbsp;&nbsp;
            ☐ Pictures &nbsp;&nbsp;&nbsp;
            ☐ Make Ready &nbsp;&nbsp;&nbsp;
            ☐ Work Order &nbsp;&nbsp;&nbsp;
            ☐ Material Receipt &nbsp;&nbsp;&nbsp;
            ☐ Maps<br><br>

            <strong>Status:</strong><br>
            """
        

        if daily_obj.daily_rtb:
            html_content += f""" 
                                 {checked_box} Ready to bill &nbsp;&nbsp;&nbsp;"""
        else:
            html_content += f""" 
                                {empty_box} Ready to bill &nbsp;&nbsp;&nbsp;"""
            
        if daily_obj.daily_wp:
            html_content += f""" 
                                {checked_box} Work in progress &nbsp;&nbsp;&nbsp;"""
        else:
            html_content += f""" 
                                {empty_box} Work in progress &nbsp;&nbsp;&nbsp;"""


        if daily_obj.daily_cd:
            html_content += f""" 
                                {checked_box} Construction Done &nbsp;&nbsp;&nbsp;"""
        else:
            html_content += f""" 
                                {empty_box} Construction Done &nbsp;&nbsp;&nbsp;"""
            
        if daily_obj.daily_nfs:
            html_content += f""" 
                                {checked_box} Needs Fiber Splicing &nbsp;&nbsp;&nbsp;"""
        else:
            html_content += f""" 
                                {empty_box} Needs Fiber Splicing &nbsp;&nbsp;&nbsp;"""
            
        if daily_obj.daily_fd:
            html_content += f""" 
                                {checked_box} Fiber Done<br><br>"""
        else:
            html_content += f""" 
                                {empty_box} Fiber Done<br><br>"""


        html_content += f"""

            <strong>Supervisor Comments:</strong><br>
            <div style="height: 50px; border: 0.5px solid #666; margin: 5px 0;"></div>

            <table style="width: 100%; margin-top: 20px;">
                <tr>
                    <td style="width: 50%;">
                        Supervisor's Signature<br>
                        <div style="border-top: 0.5px solid #666; width: 200px; margin-top: 30px;"></div>
                    </td>
                    <td style="width: 50%;">
                        Signature of P.C.<br>
                        <div style="border-top: 0.5px solid #666; width: 200px; margin-top: 30px;"></div>
                    </td>
                </tr>
            </table>
        </div>
        """
        html_mail = ""
        html_mail = html_content

         # Add DailyMobDocs images section
        dailyDocs = DailyMobDocs.objects.filter(DailyID=daily_obj).order_by('docType')
        html_content += """
        <div style="margin: 10px 0; "></div>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
           
        """
        for doc in dailyDocs:
            doc_preview_html = ""
            if doc.document:
                try:
                    with open(doc.document.path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                        doc_preview_html = f'<img src="data:image/png;base64,{encoded_string}" style="max-height: 100px;">'
                except Exception as e:
                    doc_preview_html = '<span style="color: #666; font-style: italic;">Preview not available</span>'
            else:
                doc_preview_html = '<span style="color: #666; font-style: italic;">No file available</span>'
            html_content += f"""
            <tr>                
                <td style=" padding: 4px; text-align: center;">{doc_preview_html}</td>
            </tr>
            """
        html_content += "</table>"

        # Wrap the content with HTML structure and CSS
        final_html = f"""
        <!DOCTYPE HTML>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: letter;
                    margin: 0.15in;
                }}
                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 5px;
                }}
                th, td {{
                    border: 0.5px solid #666;
                    padding: 4px;
                    text-align: left;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        

        # Create a BytesIO buffer to receive PDF data
        result = BytesIO()

        # Convert HTML to PDF
        pisa.CreatePDF(
            src=html_content,  # the HTML to convert
            dest=result,       # the BytesIO buffer
            encoding='utf-8'
        )

        # Get the value of the BytesIO buffer
        pdf = result.getvalue()
        result.close()
        # Create a unique filename for the PDF
        pdf_filename = f'daily_report_{daily_obj.crew}_{daily_obj.day.strftime("%Y%m%d")}.pdf'

        # Save PDF to model's pdfDaily field
        daily_obj.pdfDaily.save(
            pdf_filename,
            ContentFile(pdf),
            save=True
        )

        return True, "", html_mail

    except Exception as e:
        print(f"Error converting HTML to PDF: {str(e)}")
        return False, f"Error converting HTML to PDF: {str(e)}",""