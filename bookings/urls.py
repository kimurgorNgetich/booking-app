from django.urls import path
from . import views

urlpatterns = [
    path("", views.book, name="book"),
    path("booked/<str:token>/", views.booking_success, name="booking_success"),
        path("mpesa/callback/<str:secret>/", views.mpesa_callback, name="mpesa_callback"),
]