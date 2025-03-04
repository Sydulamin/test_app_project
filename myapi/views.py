from rest_framework import viewsets , generics , mixins
from .models import Purchase, Buyer ,Item , CashupOwingDeposit ,CashupDeposit
from .serializers import PurchaseSerializer,ItemSerializer, LoginSerializer,BuyerTransactionSerializer,TransferSerializer,CashupDepositSerializer,DepositSerializer ,BuyerSerializer , CashupOwingDepositSerializer ,DepositSerializer
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UpdateBuyerProfileSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction 



# Create your views here.
class ProductView(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `retrieve`, `create`, `update`, and `destroy` actions.
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

class BuyerView(viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    """
    This viewset automatically provides `list`, `retrieve`, `create`, `update`, and `destroy` actions.
    """
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
class ItemView(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `retrieve`, `create`, `update`, and `destroy` actions.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class ConfirmedProductsList(generics.ListAPIView):
    queryset = Purchase.objects.filter(confirmed=True)
    serializer_class = PurchaseSerializer

class CartedProductsList(generics.ListAPIView):
    permission_classes=[IsAuthenticated]
    queryset = Purchase.objects.filter(confirmed=False)
    serializer_class = PurchaseSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView,mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
class BuyerDetail(generics.RetrieveUpdateDestroyAPIView,mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    
    def get_object(self):
        # Get the authenticated user from the JWT token
        user = self.request.user
        
        # Retrieve the Buyer instance associated with the authenticated user
        buyer = get_object_or_404(Buyer, user=user)
        
        return buyer
    

class ConfirmedBuyerView(generics.ListAPIView):
    permission_classes=[IsAuthenticated]
    """
    This viewset provides `list`, `retrieve`, `create`, `update`, and `destroy` actions for confirmed buyers.
    """
    queryset = Buyer.objects.filter(purchase__confirmed=True).distinct()
    serializer_class = BuyerSerializer



class ConfirmedBuyersForProducts(APIView):
    permission_classes=[IsAuthenticated]
    """
    This view provides a list of all products with their confirmed buyers.
    """
    def get(self, request):
        # Fetch confirmed purchases and prefetch related buyers
        purchases = Purchase.objects.filter(confirmed=True).select_related('buyer')

        data = []
        for purchase in purchases:
            # Serialize the product (purchase)
            product_serializer = PurchaseSerializer(purchase)

            # Serialize the buyer (if exists) and exclude unwanted fields
            buyer_data = None
            if purchase.buyer:
                buyer_serializer = BuyerSerializer(purchase.buyer)
                buyer_data = buyer_serializer.data

                # Remove unwanted fields from the buyer data
                unwanted_fields = ['date_of_birth', 'gender']
                for field in unwanted_fields:
                    buyer_data.pop(field, None)  # Remove the field if it exists

            data.append({
                'product': product_serializer.data,
                'confirmed_buyer': buyer_data
            })

        return Response(data)

class BuyerPurchasesAPIView(APIView):
    permission_classes=[IsAuthenticated]

    """
    This view provides the purchased products for a specific buyer and calculates the discount prices and total cost.
    """
    def get(self, request, *args, **kwargs):
        buyer_id = kwargs.get('buyer_id')
        buyer = get_object_or_404(Buyer, id=request.user.id)
        products = Purchase.objects.filter(buyer=buyer, confirmed=True,paid=True)
        
        total_cost = 0
        product_list = []
        
        for product in products:
            original_price = product.total_price
            discount_rate = product.discount_rate
            quantity = product.quantity
            
            discount_price = original_price - (discount_rate * original_price / 100)
            total_cost += discount_price * quantity
            
            product_data = {
                'quantity': quantity,
                'product': PurchaseSerializer(product).data,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'discount_price': discount_price,
                'total_cost': discount_price * quantity
            }
            product_list.append(product_data)
        
        response_data = {
            'buyer': BuyerSerializer(buyer).data,
            'products': product_list,
            'total_cost': total_cost
        }
        
        return Response(response_data)
from django.db.models import Prefetch
from rest_framework import generics
from .models import CashupOwingDeposit, Buyer
from .serializers import CashupOwingDepositSerializer
import logging

logger = logging.getLogger(__name__)



from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BuyerTransactionSerializer
from .models import Buyer

class BuyerTransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user  # The logged-in user (assuming the buyer is the authenticated user)

        # Get the corresponding Buyer instance for the logged-in user
        try:
            buyer = Buyer.objects.get(user=user)  # Assuming there's a ForeignKey in Buyer model to User
        except Buyer.DoesNotExist:
            return Response({"detail": "Buyer instance not found for this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Make a mutable copy of the request data
        data = request.data.copy()

        # Set the 'buyer' field to the found Buyer instance
        data['buyer'] = buyer.id  # This assumes the 'buyer' field is a foreign key in BuyerTransaction model

        # Now, proceed with the serialization and saving of the transaction
        serializer = BuyerTransactionSerializer(data=data)
        
        if serializer.is_valid():
            # Save the transaction instance, buyer will automatically be set
            serializer.save(buyer=buyer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    

class CashupOwingDepositByBuyerAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view
    serializer_class = CashupOwingDepositSerializer

    def get_queryset(self):
        # Get the authenticated user from the JWT token
        user = self.request.user
        
        # Retrieve the Buyer instance associated with the authenticated user
        buyer = get_object_or_404(Buyer, user=user)
        
        # Filter CashupOwingDeposit instances for the authenticated buyer
        # Use select_related to fetch the related Buyer information in a single query
        return CashupOwingDeposit.objects.filter(buyer=buyer).select_related('buyer')
    

class CashupDepositByBuyerAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view
    serializer_class = CashupDepositSerializer

    def get_queryset(self):
        # Get the authenticated user from the JWT token
        user = self.request.user
        
        # Retrieve the Buyer instance associated with the authenticated user
        buyer = get_object_or_404(Buyer, user=user)



from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import RegisterSerializer
from .models import Buyer, User
class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()  # Create the user with serializer's `create` method

            # Ensure buyer is created only if the user doesn't already have one
            if not hasattr(user, 'buyer'):  # Check if buyer already exists
                Buyer.objects.create(
                    user=user,
                    phone_number=request.data.get('phone_number'),
                    gender=request.data.get('gender'),
                    date_of_birth=request.data.get('date_of_birth'),
                    name=f"{request.data.get('first_name')} {request.data.get('last_name')}"
                )

            return Response({
                'message': 'User and buyer created successfully.',
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.buyer.phone_number,
                'gender': user.buyer.gender,
                'date_of_birth': str(user.buyer.date_of_birth),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# --break-system-packages
class LoginAPIView(APIView):
    """
    API view for user login. Returns JWT tokens on successful authentication.
    """
    def post(self, request, *args, **kwargs):
        # Initialize the serializer with the request data
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        # Validate the input data
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If validation passes, create and return the JWT tokens
        tokens = serializer.save()
        return Response(tokens, status=status.HTTP_200_OK)
    


class UpdateBuyerProfileAPIView(APIView):
    """
    API view for updating the Buyer profile.
    """
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    def get_object(self):
        """
        Retrieve the Buyer instance associated with the logged-in user.
        """
        try:
            return Buyer.objects.get(user=self.request.user)
        except Buyer.DoesNotExist:
            return None

    def put(self, request, *args, **kwargs):
        """
        Handle the PUT request to update the Buyer profile.
        """
        buyer = self.get_object()
        if not buyer:
            return Response(
                {"detail": "Buyer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateBuyerProfileSerializer(buyer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from django.db.models import Sum
from django.db import transaction
from django.db.models import Sum


from django.db import transaction
from django.db.models import Sum
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.db.models import Sum
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Buyer, CashupOwingDeposit
from .serializers import DepositSerializer
from decimal import Decimal

class DepositToMainBalance(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the buyer associated with the authenticated user
        buyer = get_object_or_404(Buyer, id=request.user.id)
        
        # Validate the incoming data using the DepositSerializer
        serializer = DepositSerializer(data=request.data)

        if serializer.is_valid():
            # Convert the amount to Decimal
            amount = Decimal(serializer.validated_data['amount'])

            # Update the buyer's main balance
            buyer.main_balance += amount
            buyer.save()

            # Print the updated main balance for debugging
            print(f"New main balance: {buyer.main_balance}")

            # Return a success response
            return Response(
                {
                    "message": f"Deposited {amount} to main balance.",
                    "new_balance": float(buyer.main_balance),  # Convert Decimal to float for JSON serialization
                },
                status=status.HTTP_200_OK
            )
        
        # Return an error response if the serializer is not valid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TransferToCashupDeposit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        buyer = get_object_or_404(Buyer, id=request.user.id)
        serializer = TransferSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']

            if buyer.main_balance < amount:
                return Response({"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)

            buyer.main_balance -= amount
            buyer.save()

            CashupDeposit.objects.create(
                cashup_main_balance=amount,
                buyer=buyer,
            )

            return Response({"message": f"Transferred {amount} to Cashup Deposit", "new_balance": buyer.main_balance}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from .models import CashupOwingDeposit

from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class TransferToCashupOwingDeposit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        buyer = get_object_or_404(Buyer, id=request.user.id)
        serializer = TransferSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            
            with transaction.atomic():
                # Retrieve all CashupOwingDeposit instances for the buyer
                cashup_owing_deposits = CashupOwingDeposit.objects.filter(buyer=buyer)

                total_cashup_owing_main_balance = 0
                if cashup_owing_deposits.exists():
                    # Update the cashup_owing_main_balance for existing instances
                    for deposit in cashup_owing_deposits:
                        deposit.cashup_owing_main_balance = deposit.cashup_owing_main_balance + amount
                        deposit.save()
                        total_cashup_owing_main_balance = deposit.cashup_owing_main_balance
                else:
                    # Create a new CashupOwingDeposit instance if none exist
                    cashup_owing_deposit = CashupOwingDeposit.objects.create(
                        cashup_owing_main_balance=amount,
                        buyer=buyer,
                    )
                    total_cashup_owing_main_balance = cashup_owing_deposit.cashup_owing_main_balance

            return Response({"message": f"Transferred {amount} to Cashup Owing Deposit", "cashup_owing_main_balance": total_cashup_owing_main_balance}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




from .serializers import PurchaseSerializer

class PurchaseProduct(APIView):
    def post(self, request):
        serializer = PurchaseSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Purchase successful", "purchase": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# views.py
import random
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Buyer, BuyerOTP
from .serializers import BuyerOTPSerializer

class SendOTPToBuyer(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            buyer = Buyer.objects.get(phone_number=phone_number)
        except Buyer.DoesNotExist:
            return Response({'error': 'Buyer not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = str(random.randint(100000, 999999))
        # Save OTP to database
        otp_instance = BuyerOTP.objects.create(buyer=buyer, otp=otp)

        # Send OTP via BulkSMS BD
        api_key = 'sZPisZCH9HlXyM4JpXeX'
        sender_id = 'Cashup'
        message = f'Your OTP is {otp}'
        url = f'http://bulksmsbd.net/api/smsapi?api_key={api_key}&type=text&number={phone_number}&senderid={sender_id}&message={message}'

        response = requests.get(url)
        if response.status_code == 200:
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class VerifyBuyerOTP(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        if not phone_number or not otp:
            return Response({'error': 'Phone number and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            buyer = Buyer.objects.get(phone_number=phone_number)
            otp_instance = BuyerOTP.objects.filter(buyer=buyer, otp=otp, is_verified=False).latest('created_at')
        except Buyer.DoesNotExist:
            return Response({'error': 'Buyer not found'}, status=status.HTTP_404_NOT_FOUND)
        except BuyerOTP.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_instance.is_expired():
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

        otp_instance.is_verified = True
        otp_instance.save()

        return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)

from rest_framework.permissions import IsAuthenticated


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch the buyer profile associated with the authenticated user
        try:
            buyer = Buyer.objects.get(user=request.user)
        except Buyer.DoesNotExist:
            return Response(
                {"detail": "Buyer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch purchases associated with the buyer
        purchases = Purchase.objects.filter(buyer=buyer)

        # Serialize the buyer profile and purchases
        buyer_serializer = BuyerSerializer(buyer)
        

        # Combine the serialized data
        response_data = {
            "buyer": buyer_serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)