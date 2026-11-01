from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email= models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Service(models.Model):
    name = models.CharField(max_length=100)
    price  = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return f"{self.name} - KES {self.price}"


class Appointment(models.Model):
        class Status(models.TextChoices):
            PENDING = "pending", "Pending"
            CONFIRMED = "confirmed", "Confirmed"
            COMPLETED = "completed", "Completed"
            CANCELLED = "cancelled", "Cancelled"

        client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="appointments")
        service = models.ForeignKey(Service, on_delete=models.PROTECT)
        start_time = models.DateTimeField()
        status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.client.name} - {self.service.name} on {self.start_time:%d %b %H:%M}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    phone = models.CharField(max_length=15)
    checkout_request_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    mpesa_receipt = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KES {self.amount} - {self.status}"