from django.contrib import admin
from .models import Item, OrderItem, Order, Coupon, Address, Refund

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
        'shipping_address',
        'payment',
        'coupon'
    ]
    list_display_links = [
        'user',
        'shipping_address',
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


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'appartment_address',
        'country',
        'zip',
        'address_type',
        'default',
    ]

    list_filter = [
        'country',
        'default',
        'address_type'
    ]

    search_fields = [
        'user',
        'street_address',
        'appartment_address',
        'country',
        'zip',
        'address_type',
        'default',
    ]


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
