from django.urls import path
from . import views

urlpatterns = [
    path("", views.book, name="book"),
    path("booked/<str:token>/", views.booking_success, name="booking_success"),
]