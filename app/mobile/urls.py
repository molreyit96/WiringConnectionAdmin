from turtle import home
from django.contrib import admin
from django.urls import path, include
from mobile import views

urlpatterns = [
     # ****** Home **********************
     path('',views.mobile),
     path('home/<LocID>',views.mobile_home),

     # ****** DAILY **********************
     path('crew/<perID>/<dID>/<crewID>/<LocID>',views.crew),
     path('update_supervisor/<perID>/<dID>/<crewID>/<LocID>',views.update_supervisor),
     path('create_daily/<pID>/<dID>/<LocID>',views.create_daily),
     path('delete_daily/<id>/<LocID>',views.delete_daily),
     path('update_order_daily/<woID>/<dailyID>/<LocID>',views.update_order_daily),
     path('orders_payroll/<dailyID>/<LocID>',views.orders_payroll),   
     path('send_payroll/<id>/<LocID>',views.send_payroll),   
     path('save_daily_comment/<daily_id>', views.save_daily_comment),

     # ****** DAILY EMPLOYEE**********************
     path('create_daily_emp/<id>/<LocID>',views.create_daily_emp),
     path('update_daily_emp/<id>/<LocID>',views.update_daily_emp),
     path('delete_daily_emp/<id>/<LocID>',views.delete_daily_emp),
     
     # ****** DAILY ITEM **********************
     path('create_daily_item/<id>/<LocID>',views.create_daily_item),
     path('update_daily_item/<id>/<LocID>',views.update_daily_item),
     path('delete_daily_item/<id>/<LocID>',views.delete_daily_item),

     # ****** Daily Docs **********************
     path('create_daily_docs/<id>/<LocID>/<docType>', views.BulkUploadView.as_view(), name='bulk-upload'),
     path('create_daily_docs_compressed/<id>/<LocID>/<docType>', views.BulkUploadCompressedView.as_view(), name='bulk-upload-compressed'),
     path('delete_daily_docs/<id>/<LocID>',views.delete_daily_docs),

     # ****** Employee **********************
     path('employee_list/',views.employee_list),   
     path('employee_submitted_list/',views.employee_submitted_list), 
     
     # ****** Supervisor **********************
     path('supervisor_list/',views.supervisor_list), 
     path('approve_timesheet/<id>',views.approve_timesheet),
     path('update_daily_pdf/<id>',views.save_pdf_daily),
     path('save-pdf/<id>', views.save_pdf_daily, name='save_pdf'),
     path('reject_timesheet/<id>/<origen>',views.reject_timesheet),

     path('create_daily_emp_sup/<id>/<LocID>',views.create_daily_emp_sup),
     path('update_daily_emp_sup/<id>/<LocID>',views.update_daily_emp_sup),
     path('delete_daily_emp_sup/<id>/<LocID>',views.delete_daily_emp_sup),

     path('delete_daily_item_sup/<id>/<LocID>',views.delete_daily_item_sup),
     path('create_daily_item_sup/<id>/<LocID>',views.create_daily_item_sup),
     path('update_daily_item_sup/<id>/<LocID>',views.update_daily_item_sup),
     
     path('create_daily_docs_sup/<id>/<LocID>/<docType>', views.BulkUploadViewSup.as_view(), name='bulk-upload-sup'),
     path('delete_daily_docs_sup/<id>/<LocID>',views.delete_daily_docs_sup),


     
     # ****** Crew  Supervisor **********************
     path('create/',views.create),
     path('update/<id>',views.update),
     path('create/',views.create),
     
     path('create_by_supervisor/',views.createBySupervisor),
     path('update_by_super/<id>',views.updateBySuper),
     path('update_status/<id>/<status>',views.update_status),
     
     
     # ****** Reports **********************
     path('report_list/',views.report_list), 
     path('get_report_list/<dateSelected>/<dateSelected2>/<status>/<location>/<employee>/<type>',views.get_report_list),

     # ******** ADMIN ************************
     path('approved_dailies/',views.approved_dailies),
]