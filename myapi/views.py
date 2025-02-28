from rest_framework import viewsets , generics , mixins
from .models import Purchase, Buyer ,Item , CashupOwingDeposit ,CashupDeposit
from .serializers import PurchaseSerializer, LoginSerializer,TransferSerializer,CashupDepositSerializer,DepositSerializer ,BuyerSerializer , CashupOwingDepositSerializer ,DepositSerializer
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



# Create your views here.
class ProductView(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `retrieve`, `create`, `update`, and `destroy` actions.
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

class BuyerView(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `retrieve`, `create`, `update`, and `destroy` actions.
    """
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer


class ConfirmedProductsList(generics.ListAPIView):
    queryset = Purchase.objects.filter(confirmed=True)
    serializer_class = PurchaseSerializer

class CartedProductsList(generics.ListAPIView):
    queryset = Purchase.objects.filter(confirmed=False)
    serializer_class = PurchaseSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView,mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class ConfirmedBuyerView(generics.ListAPIView):
    """
    This viewset provides `list`, `retrieve`, `create`, `update`, and `destroy` actions for confirmed buyers.
    """
    queryset = Buyer.objects.filter(purchase__confirmed=True).distinct()
    serializer_class = BuyerSerializer


class ConfirmedBuyersForProducts(APIView):
    """
    This view provides a list of all products with their confirmed buyers.
    """
    def get(self, request):
        products = Purchase.objects.filter(confirmed=True).prefetch_related(
            Prefetch('buyer', queryset=Buyer.objects.all(), to_attr='confirmed_buyer')
        )
        data = []
        for product in products:
            buyer_serializer = BuyerSerializer(product.confirmed_buyer) if product.confirmed_buyer else None
            product_serializer = PurchaseSerializer(product)
            data.append({
                'product': product_serializer.data,
                'confirmed_buyer': buyer_serializer.data if buyer_serializer else None
            })
        return Response(data)

class BuyerPurchasesAPIView(APIView):
    """
    This view provides the purchased products for a specific buyer and calculates the discount prices and total cost.
    """
    def get(self, request, *args, **kwargs):
        buyer_id = kwargs.get('buyer_id')
        buyer = Buyer.objects.get(id=buyer_id)
        products = Purchase.objects.filter(buyer=buyer, confirmed=True)
        
        total_cost = 0
        product_list = []
        
        for product in products:
            original_price = product.original_price
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

class CashupOwingDepositByBuyerAPIView(generics.ListAPIView):
    serializer_class = CashupOwingDepositSerializer

    def get_queryset(self):
        buyer_id = self.kwargs['buyer_id']
        logger.info(f"Fetching CashupOwingDeposit records for buyer_id: {buyer_id}")
        
        # Check if the buyer exists
        buyer_exists = Buyer.objects.filter(id=buyer_id).exists()
        logger.info(f"Buyer exists: {buyer_exists}")
        
        # Fetch CashupOwingDeposit records
        queryset = CashupOwingDeposit.objects.filter(buyer__id=buyer_id)
        logger.info(f"Number of records found: {queryset.count()}")
        
        return queryset
class CashupDepositByBuyerAPIView(generics.ListAPIView):
    serializer_class = CashupDepositSerializer

    def get_queryset(self):
        buyer_id = self.kwargs['buyer_id']
        return CashupOwingDeposit.objects.filter(buyer__id=buyer_id).prefetch_related(Prefetch('buyer', queryset=Buyer.objects.all()))




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer


class RegisterView(APIView):
    """
    View for user registration.
    """
    def post(self, request, *args, **kwargs):
        """
        Handle user registration.
        """
        # Pass the request data to the serializer
        serializer = RegisterSerializer(data=request.data)
        
        # Validate the input data
        if serializer.is_valid():
            # Save the user and buyer instances
            user = serializer.save()
            
            # Return a success response
            return Response({
                'message': 'User registered successfully.',
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }, status=status.HTTP_201_CREATED)
        
        # If the data is invalid, return an error response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
class DepositToMainBalance(APIView):
    def post(self, request, buyer_id):
        buyer = get_object_or_404(Buyer, id=buyer_id)
        serializer = DepositSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            buyer.main_balance += amount
            buyer.save()
            return Response({"message": f"Deposited {amount} to main balance", "new_balance": buyer.main_balance}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TransferToCashupDeposit(APIView):
    def post(self, request, buyer_id):
        buyer = get_object_or_404(Buyer, id=buyer_id)
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

class TransferToCashupOwingDeposit(APIView):
    def post(self, request, buyer_id):
        buyer = get_object_or_404(Buyer, id=buyer_id)
        serializer = TransferSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']

            if buyer.main_balance < amount:
                return Response({"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)

            buyer.main_balance -= amount
            buyer.save()

            CashupOwingDeposit.objects.create(
                cashup_owing_main_balance=amount,
                buyer=buyer,
            )

            return Response({"message": f"Transferred {amount} to Cashup Owing Deposit", "new_balance": buyer.main_balance}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .serializers import PurchaseSerializer

class PurchaseProduct(APIView):
    def post(self, request):
        serializer = PurchaseSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Purchase successful", "purchase": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)