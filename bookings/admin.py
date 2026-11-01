from django.contrib import admin
from .models import Client, Service, Appointment, Payment


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    fields = ("service", "start_time", "status")
    show_change_link = True

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("amount", "phone", "mpesa_receipt", "status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone")
    inlines = [AppointmentInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("client", "service", "start_time", "status")
    list_filter = ("status", "service", "start_time")
    search_fields = ("client__name", "client__phone")
    date_hierarchy = "start_time"
    inLines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("appointment", "amount", "status", "mpesa_receipt", "created_at")
    list_filter = ("status",)
    search_fields = ("mpesa_receipt", "phone")