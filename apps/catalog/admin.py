from django.contrib import admin

from apps.accounts.models import User
from apps.core.services import audit, notify

from .models import Category, Favorite, Order, OrderStatusHistory, Review, Service, ServiceImage
from .services import recalc_provider_rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["icon", "name", "slug", "image", "order", "is_active"]
    list_editable = ["order", "is_active"]
    list_display_links = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title", "provider", "category", "price", "price_type", "service_mode", "district", "status", "created_at"]
    list_filter = ["status", "category", "service_mode", "region"]
    search_fields = ["title", "description", "provider__phone", "provider__profile__first_name"]
    inlines = [ServiceImageInline]
    actions = ["block", "unblock"]
    raw_id_fields = ["provider"]

    @admin.action(description="Moderatsiya: bloklash")
    def block(self, request, queryset):
        for s in queryset:
            s.status = Service.Status.BLOCKED
            s.save(update_fields=["status"])
            notify(s.provider, f"Xizmatingiz moderatsiya tomonidan bloklandi: {s.title}")
            audit(request.user, "service.block", s, request)

    @admin.action(description="Moderatsiya: faollashtirish")
    def unblock(self, request, queryset):
        queryset.update(status=Service.Status.ACTIVE)


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ["from_status", "to_status", "changed_by", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "service", "customer", "provider", "price", "service_date", "status", "created_at"]
    list_filter = ["status", "service__category"]
    search_fields = ["service__title", "customer__phone", "provider__phone"]
    inlines = [OrderStatusHistoryInline]
    readonly_fields = ["customer", "provider", "service", "started_at", "completed_at", "created_at"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["order", "provider", "customer", "rating", "is_hidden", "created_at"]
    list_filter = ["rating", "is_hidden"]
    readonly_fields = ["order", "customer", "provider"]
    actions = ["hide", "unhide"]

    @admin.action(description="Moderatsiya: yashirish")
    def hide(self, request, queryset):
        queryset.update(is_hidden=True)
        for provider_id in set(queryset.values_list("provider", flat=True)):
            recalc_provider_rating(User.objects.get(pk=provider_id))

    @admin.action(description="Ko‘rsatish")
    def unhide(self, request, queryset):
        queryset.update(is_hidden=False)
        for provider_id in set(queryset.values_list("provider", flat=True)):
            recalc_provider_rating(User.objects.get(pk=provider_id))


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "service", "created_at"]
