from django.contrib import admin
from .models import Purchase, Buyer , Category ,Item ,CashupOwingDeposit , CashupDeposit , BuyerTransaction
from .models import User

# Register your models here.
class BuyerAdmin(admin.ModelAdmin):
    search_fields=['phone_number']
class ItemAdmin(admin.ModelAdmin):
    search_fields=['name']
class PurchaseAdmin(admin.ModelAdmin):
    search_fields=['phone_number']
    readonly_fields = ['total_price']
class CashupOwingAdmin(admin.ModelAdmin):
    search_fields=['phone_number']
class CashupAdmin(admin.ModelAdmin):
    search_fields=['phone_number']
class CategoryAdmin(admin.ModelAdmin):
    search_fields=['name']
class BuyerTransactionAdmin(admin.ModelAdmin):
    search_fields=['phone_number']


admin.site.register(Purchase,PurchaseAdmin)
admin.site.register(Buyer,BuyerAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Item,ItemAdmin)
admin.site.register(CashupOwingDeposit,CashupOwingAdmin)
admin.site.register(CashupDeposit,CashupAdmin)
admin.site.register(BuyerTransaction,BuyerTransactionAdmin)




