from django.contrib import admin

from .models import Category, Order, OrderItem, Product, Profile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_featured", "updated_at")
    list_filter = ("category", "is_featured", "visual")
    list_editable = ("price", "is_featured")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "tagline", "category__name")
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("category__order", "name")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "code_attempts", "code_created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "activation_code", "code_attempts", "code_created_at")
    list_select_related = ("user",)

    @admin.display(description="Email")
    def email(self, profile):
        return profile.user.email


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "product_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "email",
        "phone",
        "total_price",
        "payment_method",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    list_editable = ("status",)
    search_fields = ("email", "first_name", "last_name", "phone")
    readonly_fields = ("user", "total_price", "created_at", "updated_at")
    inlines = (OrderItemInline,)
    ordering = ("-created_at",)
