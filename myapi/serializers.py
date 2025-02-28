import re  # Import the re module for regular expressions
from rest_framework import serializers
from .models import Purchase, Buyer, CashupOwingDeposit, Item, CashupDeposit ,BuyerTransaction
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from datetime import date

# Custom ValidationError
class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

# Item Serializer
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'is_available', 'price','members_price','item_image']

# Buyer Serializer
class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['id', 'name', 'phone_number','main_balance','date_of_birth','gender', 'membership_status', 'main_balance','buyer_image']

# Purchase Serializer
class PurchaseSerializer(serializers.ModelSerializer):
    buyer = serializers.PrimaryKeyRelatedField(queryset=Buyer.objects.all())  # Allow buyer to be set via ID
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())  # Allow item to be set via ID
    members_price = serializers.SerializerMethodField()  # Calculate members price dynamically

    class Meta:
        model = Purchase
        fields = [
            'id', 'item', 'total_price', 'discount_rate', 'quantity', 'buyer', 'members_price', 'confirmed'
        ]

    def get_members_price(self, obj):
        """
        Calculate the members price if the buyer has a membership.
        """
        if obj.buyer and obj.buyer.membership_status:
            return obj.total_price * (1 - obj.discount_rate / 100)
        return None

    def validate(self, data):
        """
        Validate the purchase data.
        """
        buyer = data.get('buyer')
        item = data.get('item')
        quantity = data.get('quantity', 1)

        if not item:
            raise serializers.ValidationError("Item is required.")

        total_price = item.price * quantity

        if buyer.main_balance < total_price:
            raise serializers.ValidationError("Insufficient funds.")

        return data

    def create(self, validated_data):
        """
        Create a new purchase and deduct the total price from the buyer's main balance.
        """
        buyer = validated_data['buyer']
        item = validated_data['item']
        quantity = validated_data.get('quantity', 1)
        total_price = item.price * quantity

        # Deduct the total price from the buyer's main balance
        buyer.main_balance -= total_price
        buyer.save()

        # Create the purchase
        purchase = Purchase.objects.create(
            item=item,
            total_price=item.price,
            discount_rate=validated_data.get('discount_rate', 0),
            quantity=quantity,
            buyer=buyer,
            confirmed=True,
        )

        return purchase

# CashupOwingDeposit Serializer


class CashupOwingDepositSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(read_only=True)  # Nested serializer for buyer (read-only)

    class Meta:
        model = CashupOwingDeposit
        fields = [
            'id',
            'cashup_owing_main_balance',  # Updated field name (from cashup_owing_main_balance)
            'buyer',
            'created_at',
            'daily_profit',
            'compounding_profit',
            'monthly_profit',
            'withdraw',
            'product_profit',
            'compounding_withdraw',
        ]
        read_only_fields = ['created_at'] 

        
# CashupDeposit Serializer
class CashupDepositSerializer(serializers.ModelSerializer):
    buyer = BuyerSerializer(read_only=True)  # Nested serializer for buyer (read-only)

    class Meta:
        model = CashupDeposit
        fields = [
            'id',
            'cashup_main_balance',  # Updated field name (from cashup_owing_main_balance)
            'buyer',
            'created_at',
            'daily_profit',
            'compounding_profit',
            'monthly_profit',
            'withdraw',
            'product_profit',
            'compounding_withdraw',
        ]
        read_only_fields = ['created_at']  # Automatically set by the model

# Password Validation
def validate_password(value):
    """
    Validate the password to ensure it meets the requirements.
    """
    print(f"Validating password: {value}")  # Debugging
    if len(value) != 6:
        raise ValidationError('Password must be exactly 6 characters long.')
    return value

class BuyerTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerTransaction
        fields = ['buyer', 'transaction_id', 'phone_number']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Password',
        style={'input_type': 'password'},
        max_length=6,
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Confirm Password',
        style={'input_type': 'password'}
    )
    phone_number = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Phone number of the user'
    )
    gender = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Gender of the user (M, F, O)'
    )
    date_of_birth = serializers.DateField(
        write_only=True,
        required=True,
        help_text='Date of birth of the user (YYYY-MM-DD)'
    )
    first_name = serializers.CharField(
        write_only=True,
        required=True,
        help_text='First name of the user'
    )
    last_name = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Last name of the user'
    )

    class Meta:
        model = User
        fields = ['password', 'password2', 'phone_number', 'first_name', 'last_name', 'gender', 'date_of_birth']

    def validate(self, data):
        """
        Validate the input data.
        """
        # Check if passwords match
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Remove password2 from validated_data
        del data['password2']

        # Check if phone number is already in use as a username
        if User.objects.filter(username=data['phone_number']).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        
        # Check if phone number is already in use in the Buyer model
        if Buyer.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError("Phone number is already registered.")
        
        # Validate gender
        valid_genders = ['M', 'F', 'O']
        if data['gender'] not in valid_genders:
            raise serializers.ValidationError("Invalid gender. Allowed values are M, F, O.")
        
        # Validate date_of_birth
        today = date.today()
        if data['date_of_birth'] > today:
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        
        return data

    def create(self, validated_data):
        """
        Create a new User.
        """
        # Create the User (Buyer creation is deferred to the view)
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['phone_number']  # Use phone number as the username
        )
        user.set_password(validated_data['password'])
        user.save()

        return user



# Login Serializer
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if not phone_number or not password:
            raise serializers.ValidationError('Must include "phone_number" and "password"')

        # Authenticate using the phone_number as the username
        user = authenticate(
            request=self.context.get('request'),
            username=phone_number,  # Use phone_number as the username
            password=password
        )

        if not user:
            raise serializers.ValidationError('Invalid phone number or password')

        # Ensure the user has a linked Buyer
        buyer, created = Buyer.objects.get_or_create(
            user=user,
            defaults={
                'name': f"{user.first_name} {user.last_name}",
                'phone_number': user.username,  # Use username (phone_number) as the phone_number
                'membership_status': False
            }
        )

        data['user'] = user
        data['buyer'] = buyer
        return data

    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

# Update Buyer Profile Serializer
class UpdateBuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['name', 'phone_number', 'membership_status','date_of_birth','item_image']
        extra_kwargs = {
            'phone_number': {'required': False},  # Make phone_number optional for updates
            'membership_status': {'required': False}  # Make membership_status optional
        }

    def validate_phone_number(self, value):
        if value and Buyer.objects.filter(phone_number=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value

# Deposit Serializer
class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

# Transfer Serializer
class TransferSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value