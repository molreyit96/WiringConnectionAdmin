from django.contrib import admin
from mobile.models import *


# Register your models here.

class TimesheetAdmin(admin.ModelAdmin):
        list_display = ('date', 'EmployeeID', 'Status')
        search_fields = ['date', 'Status',]

class  DailyMobAdmin(admin.ModelAdmin):
    list_display = ('id','woID', 'crew', 'Location','Period','day','Status')
    search_fields = ('id','woID__prismID','woID__workOrderId','woID__PO')

class DailyMobItemAdmin(admin.ModelAdmin):
    list_display = ('id','itemID','DailyID','invoice')
    search_fields = ('id','itemID__item__itemID', 'DailyID__woID__prismID','invoice')

class DailyMobEmployeeAdmin(admin.ModelAdmin):
    list_display = ('id','Status')
    search_fields = ('id','Status')
    list_filter = ('Status',)

class DailyMobDocsAdmin(admin.ModelAdmin):
    list_display = ('id','Status')
    search_fields = ('id','Status')
    list_filter = ('Status',)

class DailyMobStatusAuditAdmin(admin.ModelAdmin):
    list_display = ('id','dailymob_id','old_status','new_status','operation','changed_at','db_user','app_user')
    search_fields = ('dailymob_id','app_user','db_user')
    list_filter = ('operation','new_status')

admin.site.register(Timesheet, TimesheetAdmin)
admin.site.register(DailyMob, DailyMobAdmin)
admin.site.register(DailyMobItem, DailyMobItemAdmin)    
admin.site.register(DailyMobEmployee, DailyMobEmployeeAdmin)
admin.site.register(DailyMobDocs, DailyMobDocsAdmin)
admin.site.register(DailyMobStatusAudit, DailyMobStatusAuditAdmin)