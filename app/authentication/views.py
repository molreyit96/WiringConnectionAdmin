from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse
from datetime import datetime
from django.contrib.auth import authenticate, login as login_process, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
# Actualizado: 2026-07-29 - Envio de correos migrado de SMTP a la API de Brevo
from utils.email import send_email_via_brevo
from workOrder import models as woModels
from mobile import models as mobModels
from workOrder import views as woViews
from . import views


def calculate_payroll(locID):
    per = woModels.period.objects.filter(status__in=(1,2)).first()   
    
    if locID > 0:
        loca = woModels.Locations.objects.filter(LocationID = locID)
    else:
        loca = woModels.Locations.objects.all()
    
    TotPayroll = 0
    TotInvoice = 0
    Totperc = 0
    for locItem in loca:
        daily = woModels.Daily.objects.filter(Location = locItem, Period = per)     
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
            production = woModels.DailyItem.objects.filter(DailyID=dailyItem).count()

            dailyemp = woModels.DailyEmployee.objects.filter(DailyID=dailyItem)

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

            
            dailyprod =  woModels.DailyItem.objects.filter(DailyID=dailyItem)
            total = 0
            
            ov = 0
            for j in dailyprod:                
                total += validate_decimals(j.total)
                if validate_decimals(j.price) != None:
                    invoice += (validate_decimals(j.quantity) * float(validate_decimals(j.price)) )
                if validate_decimals(j.emp_payout) != None:    
                    payroll2 += (validate_decimals(j.quantity) * float(validate_decimals(j.emp_payout)) )


            if validate_decimals(dailyItem.own_vehicle) != None:
                ov = validate_decimals(((validate_decimals(total) * validate_decimals(dailyItem.own_vehicle)) / 100))
                ownvehicle += validate_decimals(ov)
            prod += validate_decimals(total)

        if validate_decimals(invoice) > 0:                    
            perc = validate_decimals((validate_decimals(payroll) * 100) / validate_decimals(invoice))

        
        TotPayroll += payroll
        TotInvoice += invoice
        if TotInvoice > 0:
            Totperc = (TotPayroll*100) / TotInvoice

    return round(float(TotPayroll),2), TotInvoice, Totperc


def validate_decimals(value):
    try:
        return round(float(value), 2)
    except:
       return 0


@login_required(login_url='/login/')
def home(request):
    context = {}    
    emp = woModels.Employee.objects.filter(user__username__exact = request.user.username).first()
    per = woModels.period.objects.filter(status__in=(1,2)).first()
    totPayroll=0 
    totInvoice=0 
    totPerc= 0
    OrderStatus = []
    OrderStatusValues = []
    status = []
    totalOrders = 0
    dailies = 0
    woRTB = 0

    if emp:

        if emp.is_mobile:
            return HttpResponseRedirect('/mobile/')
        else:
            #Get total Orders by Rol
            if emp.is_superAdmin  or request.user.is_staff:
                totalOrders = woModels.workOrder.objects.all().count()
                totPayroll, totInvoice, totPerc = calculate_payroll(0)
                s1 = woModels.workOrder.objects.filter(Status=1).exclude(linkedOrder__isnull = False, uploaded = False).count()
                if s1 > 0:
                    OrderStatus.append('Not Started')
                    OrderStatusValues.append(s1)
                    status.append({'status':'Not Started', 'total': s1})
                s2 = woModels.workOrder.objects.filter(Status=2).exclude(linkedOrder__isnull = False, uploaded = False).count()
                if s2 > 0:
                    OrderStatus.append('Work in Progress')
                    OrderStatusValues.append(s2)
                    status.append({'status':'Work in Progress', 'total': s2})
                s3 = woModels.workOrder.objects.filter(Status=3).exclude(linkedOrder__isnull = False, uploaded = False).count()
                if s3 > 0:
                    OrderStatus.append('Pending Docs')
                    OrderStatusValues.append(s3)
                    status.append({'status':'Pending Docs', 'total': s3})
                s4 = woModels.workOrder.objects.filter(Status=4).exclude(linkedOrder__isnull = False, uploaded = False).count()
                if s4 > 0:
                    OrderStatus.append('Pending Revised WO')
                    OrderStatusValues.append(s4)
                    status.append({'status':'Pending Revised WO', 'total': s4})        
                s5 = woModels.workOrder.objects.filter(Status=5).exclude(linkedOrder__isnull = False, uploaded = False).count()
                if s5 > 0:
                    OrderStatus.append('Invoiced')
                    OrderStatusValues.append(s5)
                    status.append({'status':'Invoiced', 'total': s5})
            else:
                if emp.Location!= None:
                    totalOrders = woModels.workOrder.objects.filter(Location = emp.Location).count()
                    totPayroll, totInvoice, totPerc = calculate_payroll(emp.Location.LocationID)
                    s1 = woModels.workOrder.objects.filter(Status=1, Location = emp.Location).exclude(linkedOrder__isnull = False, uploaded = False).count()
                    if s1 > 0:
                        OrderStatus.append('Not Started')
                        OrderStatusValues.append(s1)
                        status.append({'status':'Not Started', 'total': s1})
                    s2 = woModels.workOrder.objects.filter(Status=2, Location = emp.Location).exclude(linkedOrder__isnull = False, uploaded = False).count()
                    if s2 > 0:
                        OrderStatus.append('Work in Progress')
                        OrderStatusValues.append(s2)
                        status.append({'status':'Work in Progress', 'total': s2})
                    s3 = woModels.workOrder.objects.filter(Status=3, Location = emp.Location).exclude(linkedOrder__isnull = False, uploaded = False).count()
                    if s3 > 0:
                        OrderStatus.append('Pending Docs')
                        OrderStatusValues.append(s3)
                        status.append({'status':'Pending Docs', 'total': s3})
                    s4 = woModels.workOrder.objects.filter(Status=4, Location = emp.Location).exclude(linkedOrder__isnull = False, uploaded = False).count()
                    if s4 > 0:
                        OrderStatus.append('Pending Revised WO')
                        OrderStatusValues.append(s4)
                        status.append({'status':'Pending Revised WO', 'total': s4})
                    s5 = woModels.workOrder.objects.filter(Status=5, Location = emp.Location).exclude(linkedOrder__isnull = False, uploaded = False).count()
                    if s5 > 0:
                        OrderStatus.append('Invoiced')
                        OrderStatusValues.append(s5)
                        status.append({'status':'Invoiced', 'total': s5})


            #Getting Pending dailies to Approve
            #Getting the Location of the employee

            locaList = woModels.employeeLocation.objects.filter(employeeID = emp)
                
            locationList = []
            locationList.append(emp.Location.LocationID)
            
            for i in locaList:
                locationList.append(i.LocationID.LocationID)
            
            if emp.is_manager or emp.is_admin:
                dailies = mobModels.DailyMob.objects.filter(Location__in = locationList, Status__in = (2,3)).count()
            elif emp.is_supervisor:
                dailies = mobModels.DailyMob.objects.filter(supervisor = emp.employeeID, Status__in = (2,3)).count()

            if emp.is_admin:
                woRTB = woModels.workOrder.objects.filter(Location__in = locationList, Status=7).exclude(linkedOrder__isnull = False, uploaded = False).count()

            
                  
    context["emp"] = emp
    context["per"] = per
    context["totalOrders"] = totalOrders
    context["payroll"] = totPayroll
    context["invoice"] = totInvoice
    context["perToPay"] = totPerc
    context["OrderStatus"] = OrderStatus
    context["OrderStatusValues"] = OrderStatusValues
    context["title"] ='Home Page'
    context["status"] = status
    context["year"] = datetime.now().year
    context["dailies"] = dailies
    context["woRTB"] = woRTB

    return render(
        request,
        'home.html',
        context        
    )

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

def login(request):
    state = 0
    message = ""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

       

        if user is not None:
            login_process(request, user)
            state = 1
            message = ""

            opType = "Log In"
            opDetail = "Login Successfull"

            woViews.logInAuditLog(request, opType, opDetail)

            return redirect('/home/')
        else:
            state = 2
            opType = "Log In"
            opDetail = "Login Failed, Username or password is incorrect - " + username + " -"

            woViews.logInAuditLog(request, opType, opDetail)

            message = "Username or password is incorrect"
    dic = {'state': state, 'message': message}
    return render(request, 'login.html', dic)


def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            users = User.objects.filter(email__iexact=email)
            for user in users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    f'/forgot-password/{uid}/{token}/'
                )
                # Envio via API Brevo (HTTPS). Agregado: 2026-07-29
                # Antes usaba django.core.mail (SMTP), bloqueado en DigitalOcean.
                send_email_via_brevo(
                    subject='Password Reset - Wiring Connection',
                    message=f'Click the following link to reset your password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email.',
                    recipient_list=[email],
                )
        return render(request, 'password_reset_done.html')
    return render(request, 'password_reset.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            if new_password and new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                return render(request, 'password_reset_complete.html')
            else:
                return render(request, 'password_reset_confirm.html', {
                    'validlink': True,
                    'error': 'Passwords do not match.',
                    'uidb64': uidb64,
                    'token': token,
                })
        return render(request, 'password_reset_confirm.html', {
            'validlink': True,
            'uidb64': uidb64,
            'token': token,
        })
    return render(request, 'password_reset_confirm.html', {'validlink': False})


@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if new_password and new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            return render(request, 'change_password_done.html')
        else:
            return render(request, 'change_password.html', {
                'error': 'Passwords do not match.'
            })
    return render(request, 'change_password.html')