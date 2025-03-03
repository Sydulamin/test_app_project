from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.db import models
from django.utils import timezone
from datetime import timedelta



class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


from django.db import models

from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the product")
    description = models.TextField(blank=True, help_text="Description of the product")
    is_available = models.BooleanField(default=True, help_text="Availability status of the product")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Price of the product
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    discount_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True, editable=False)
    members_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    item_image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Image of the product")

    def save(self, *args, **kwargs):
        # Calculate discount_price based on price and discount_rate
        if self.price is not None:
            if self.discount_rate is not None and self.discount_rate > 0:
                self.discount_price = self.price - (self.price * self.discount_rate / 100)
            else:
                # If discount_rate is 0 or None, discount_price equals price
                self.discount_price = self.price
        

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
from decimal import Decimal
from django.db import models
from django.db.models import Sum


class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    membership_status = models.BooleanField(default=False)
    main_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date_of_birth = models.DateField(null=True, blank=True)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    buyer_image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Image of the buyer")

    def save(self, *args, **kwargs):
        # Save the instance to ensure it has a valid primary key
        if not self.pk:
            super(Buyer, self).save(*args, **kwargs)
        
        # Calculate the total cashup_owing_main_balance for this buyer
        total_owing = CashupOwingDeposit.objects.filter(buyer=self).aggregate(
            total_owing=Sum('cashup_owing_main_balance')
        )['total_owing']

        # If no owing balance exists, set it to 0
        if total_owing is None:
            total_owing = Decimal('0.0')
        self.main_balance = Decimal(self.main_balance) - total_owing
        super(Buyer, self).save(*args, **kwargs)

    def __str__(self):
        return self.name



class BuyerOTP(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.buyer.phone_number} - {self.otp}"

    def is_expired(self):
        """Check if the OTP has expired (e.g., after 5 minutes)."""
        return timezone.now() > self.created_at + timedelta(minutes=5)

class Purchase(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    discount_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, null=False, default=1, related_name='purchase')
    confirmed = models.BooleanField(default=False)
    paid=models.BooleanField(default=False)
    membership_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)

    def __str__(self):
        return f"Purchase {self.id} by {self.buyer}"
    


    def save(self, *args, **kwargs):
        if self.item:
            item_price = self.item.price
            self.total_price = item_price * self.quantity

        if self.item:
            item_price = self.item.price
            self.total_price = item_price * self.quantity

        if self.discount_rate > 0:
            self.discount_price = item_price - (item_price * (self.discount_rate / 100))
            self.discount_total_price = self.discount_price * self.quantity
        else:
            self.discount_price = item_price
            self.discount_total_price = self.total_price

        if self.confirmed and self.paid:
            buyer = self.buyer
        if self.discount_total_price <= buyer.main_balance:
            buyer.main_balance -= self.discount_total_price  # Deduct the purchase amount from the main_balance
            buyer.save()
        else:
            raise ValueError("Insufficient balance to complete the purchase.")

        super().save(*args, **kwargs)
        
    

    def __str__(self):
        return f"Purchase {self.id} by {self.buyer}"
        




class CashupOwingDeposit(models.Model):
    cashup_owing_main_balance = models.DecimalField(max_digits=10, decimal_places=2)  # Owing deposit balance
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, related_name='cashup_owing_deposits')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Timestamp of the deposit
    daily_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    compounding_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default value added
    monthly_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    withdraw = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    compounding_withdraw = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_compounding_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_compounding_profit=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    def __str__(self):
        return f"Owing Deposit: {self.cashup_owing_main_balance} by {self.buyer.name if self.buyer else 'Unknown Buyer'}"


from django.db import models
from .models import Buyer  # Ensure you import the Buyer model if it's in a different file

class CashupDeposit(models.Model):
    cashup_main_balance = models.DecimalField(max_digits=10, decimal_places=2)  # Owing deposit balance
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, related_name='cashup_deposits')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Timestamp of the deposit
    daily_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    compounding_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default value added
    monthly_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    withdraw = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    compounding_withdraw = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_compounding_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_compounding_profit=models.DecimalField(max_digits=10,decimal_places=2,default=0)

    def __str__(self):
        return f"Deposit: {self.cashup_main_balance} by {self.buyer.name if self.buyer else 'Unknown Buyer'}"





@receiver(post_save, sender=User)
def create_buyer(sender, instance, created, **kwargs):
    if created:
        # Use the username (phone_number) as the phone_number
        phone_number = instance.username if instance.username else ''
        Buyer.objects.create(
            user=instance,
            name=f"{instance.first_name} {instance.last_name}",
            phone_number=phone_number,  # Set phone_number to username
            address='',  # Set a default or leave blank
            membership_status=False
        )
class BuyerTransaction(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15)
    amount=models.CharField(max_length=15,default=0)
    METHOD_CHOICES = [
        ('Bkash', 'BKash'),
        ('Nagad', 'Nagad'),
    ]
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='Bkash')
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_id} - {self.phone_number}'