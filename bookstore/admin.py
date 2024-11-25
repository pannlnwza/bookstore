from django.contrib import admin
from .models import Book, Genre, Customer, Order, OrderItem, Payment, Supplier, Stock


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'price', 'genre', 'get_stock')
    list_filter = ('genre', 'published_date')
    search_fields = ('title', 'author', 'isbn')

    def get_stock(self, obj):
        try:
            return obj.stock.quantity_in_stock
        except Stock.DoesNotExist:
            return 0

    get_stock.short_description = 'Stock'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('book', 'quantity_in_stock', 'supplier')
    list_filter = ('supplier',)
    search_fields = ('book__title',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total_amount', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


# Register remaining models
admin.site.register(Customer)
admin.site.register(OrderItem)
admin.site.register(Payment)
