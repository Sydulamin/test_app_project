from django.contrib import admin
from .models import Purchase, Buyer , Category ,Item ,CashupOwingDeposit , CashupDeposit , BuyerTransaction
from .models import User

# Register your models here.


admin.site.register(Purchase)
admin.site.register(Buyer)
admin.site.register(Category)
admin.site.register(Item)
admin.site.register(CashupOwingDeposit)
admin.site.register(CashupDeposit)
admin.site.register(BuyerTransaction)




