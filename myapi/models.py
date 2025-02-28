from django.db import models
from django.contrib.auth.models import User

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
    def __str__(self):
        return self.name


class Purchase(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,null=True)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2 ,default=0.0)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, null=False, default=1, related_name='purchase')
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Purchase {self.id} by {self.buyer}"



class CashupOwingDeposit(models.Model):
    cashup_owing_main_balance = models.DecimalField(max_digits=10, decimal_places=2)  # Owing deposit balance
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, related_name='cashup_owing_deposits')
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)  # Timestamp of the deposit

    def __str__(self):
        return f"Owing Deposit: {self.cashup_owing_main_balance} by {self.buyer.name if self.buyer else 'Unknown Buyer'}"


class CashupDeposit(models.Model):
    cashup_main_balance = models.DecimalField(max_digits=10, decimal_places=2)  # Cashup deposit balance
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, related_name='cashup_deposits')
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)  # Timestamp of the deposit
    

    def __str__(self):
        return f"Cashup Deposit: {self.cashup_main_balance} by {self.buyer.name if self.buyer else 'Unknown Buyer'}"


from django.db.models.signals import post_save
from django.dispatch import receiver

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