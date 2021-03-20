from django.contrib import admin
from .models import Item, OrderItem, Order, Coupon

# Register your models here.


def mark_order_delivered(modeladmin, request, queryset):
    queryset.update(delivered=True)


def mark_order_received(modeladmin, request, queryset):
    if queryset.get().delivered is False:
        queryset.update(delivered = True, received=True)
    else:
        queryset.update(received=True)


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'
mark_order_delivered.short_description = 'Update order as delivered'
mark_order_received.short_description = 'Update order as received'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ordered',
        'delivered',
        'received',
        'refund_requested',
        'refund_granted',
        'user',
        'billing_address',
        'payment',
        'coupon'
    ]
    list_display_links = [
        'user',
        'billing_address',
        'payment',
        'coupon'
    ]
    list_filter = [
        'ordered',
        'delivered',
        'received',
        'refund_requested',
        'refund_granted'
    ]
    actions = [
        make_refund_accepted,
        mark_order_received,
        mark_order_delivered
    ]


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon)
