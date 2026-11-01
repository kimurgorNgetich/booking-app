import json
import secrets as pysecrets
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.core import signing
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import BookingForm
from .models import Client, Appointment, Payment
import logging

import requests

from .mpesa import stk_push

logger = logging.getLogger(__name__)


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

            try:
                result = stk_push(
                    phone=client.phone,
                    amount=data["service"].price,
                    account_reference=f"AC{appointment.pk}",
                    description="Booking deposit",
                )
                Payment.objects.create(
                    appointment=appointment,
                    amount=data["service"].price,
                    phone=client.phone,
                    checkout_request_id=result["CheckoutRequestID"],
                )
            except (requests.RequestException, RuntimeError, KeyError):
                logger.exception("STK push failed for appointment %s", appointment.pk)

            token = signing.dumps(appointment.pk, salt="booking-success")
            return redirect("booking_success", token=token)
    else:
        form = BookingForm()
    return render(request, "bookings/book.html", {"form": form})


def booking_success(request, token):
    try:
        pk = signing.loads(token, salt="booking-success", max_age=60*60)
    except signing.BadSignature:
        raise Http404("Booking not found")
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "bookings/success.html", {"appointment": appointment})


ACCEPTED = {"ResultCode": 0, "ResultDesc": "Accepted"}


@csrf_exempt
@require_POST
def mpesa_callback(request, secret):
    expected = settings.MPESA_CALLBACK_SECRET
    if not expected or not pysecrets.compare_digest(secret, expected):
        raise Http404()

    try:
        stk = json.loads(request.body)["Body"]["stkCallback"]
        checkout_id = stk["CheckoutRequestID"]
        result_code = int(stk["ResultCode"])
    except (ValueError, KeyError, TypeError):
        logger.warning("Malformed M-Pesa callback")
        return JsonResponse(ACCEPTED)

    with transaction.atomic():
        payment = (
            Payment.objects.select_for_update()
            .filter(checkout_request_id=checkout_id)
            .select_related("appointment")
            .first()
        )
        if payment is None:
            logger.warning("Callback for unknown CheckoutRequestID %s", checkout_id)
        elif payment.status != Payment.Status.PENDING:
            logger.info("Duplicate callback for %s ignored", checkout_id)
        elif result_code != 0:
            payment.status = Payment.Status.FAILED
            payment.save()
            logger.info("Payment %s failed: %s", checkout_id, stk.get("ResultDesc"))
        else:
            items = {
                i.get("Name"): i.get("Value")
                for i in stk.get("CallbackMetadata", {}).get("Item", [])
            }
            try:
                paid = Decimal(str(items.get("Amount")))
            except InvalidOperation:
                paid = None

            if paid != payment.amount:
                payment.status = Payment.Status.FAILED
                payment.save()
                logger.error("Amount mismatch for %s: paid %s, expected %s", checkout_id, paid, payment.amount)
            else:
                payment.status = Payment.Status.SUCCESS
                payment.mpesa_receipt = str(items.get("MpesaReceiptNumber", ""))
                payment.save()
                appointment = payment.appointment
                appointment.status = Appointment.Status.CONFIRMED
                appointment.save()

    return JsonResponse(ACCEPTED)