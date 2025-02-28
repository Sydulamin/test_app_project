from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal



class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the product")
    description = models.TextField(blank=True, help_text="Description of the product")
    is_available = models.BooleanField(default=True, help_text="Availability status of the product")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Price of the product
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    members_price= models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    item_image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Image of the product")


    def __str__(self):
        return self.name


class Buyer(models.Model):
    # Existing fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    membership_status = models.BooleanField(default=False)
    main_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date_of_birth = models.DateField(null=True, blank=True)  # Allows null values and blank input
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)  # Allows null values and blank input
    address = models.CharField(max_length=255, blank=True, null=True)
    buyer_image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Image of the buyer")
    def __str__(self):
        return self.name

class Purchase(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
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

            if self.discount_rate > 0:
                self.discount_price = item_price - (item_price * (self.discount_rate / 100))
                self.discount_total_price = self.discount_price * self.quantity
            else:
                self.discount_price = item_price
                self.discount_total_price = self.total_price

   
        super().save(*args, **kwargs)




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
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_id} - {self.phone_number}'