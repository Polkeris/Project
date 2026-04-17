from django.contrib import admin

from shop.models import Category, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "author", "category", "price", "created_at"]
    list_filter = ["category"]
    list_select_related = ["category"]
    search_fields = ["name", "description"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email", "created_at"]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
