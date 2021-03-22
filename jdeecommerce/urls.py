from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from core.views import (
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    Home,
    Product,
    OrderSummaryView,
    Checkout,
    PaymentView,
    add_coupon,
    RequestRefund,
    SuccessView,
    CanceledView,
    stripe_webhook_view
)

app_name = 'core'

urlpatterns = [
    path('', Home.as_view(), name="home"),
    path('checkout/', Checkout.as_view(), name="checkout"),
    path('products/<slug:slug>/', Product.as_view(), name="product"),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # for real?
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', add_coupon, name="add-coupon"),
    path('remove-from-cart/<slug>/', remove_from_cart, name="remove-from-cart"),
    path(
        'remove_single_item_from_cart/<slug>/',
        remove_single_item_from_cart,
        name="remove-single-item-from-cart"
    ),
    path('create-payment-intent/', PaymentView.as_view(), name="create-payment"),
    path('success/', SuccessView.as_view(), name="success"),
    path('cancel/', CanceledView.as_view(), name="canceled"),
    # shop
    path('order-summary/', OrderSummaryView.as_view(), name="order-summary"),
    path('checkout/payment/<payment_option>/', PaymentView.as_view(), name="payment"),
    path('request-refund/', RequestRefund.as_view(), name="request-refund"),

    # stripe webhooks
    path('stripe/webhook/', stripe_webhook_view, name="stripe-webhook")
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
