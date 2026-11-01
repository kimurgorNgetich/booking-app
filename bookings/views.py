from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookingForm
from .models import Client, Appointment


def book(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            client, _ = Client.objects.get_or_create(
                phone=data["phone"], defaults={"name": data["name"]}
            )
            appointment = Appointment.objects.create(
                client=client, service=data["service"], start_time=data["start_time"]
            )
            return redirect("booking_success", pk=appointment.pk)
    else:
        form = BookingForm()
    return render(request, "bookings/book.html", {"form": form})


def booking_success(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "bookings/success.html", {"appointment": appointment})