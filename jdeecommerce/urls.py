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
    stripe_webhook_view,
    StripeIntentView
)

app_name = 'core'

urlpatterns = [
    path('', Home.as_view(), name="home"),
    path('checkout/', Checkout.as_view(), name="checkout"),
    path('products/<slug:slug>/', Product.as_view(), name="product"),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # for real?
    # this is how you have to do stuff like this? Through view functions?
    # seems unnatural
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', add_coupon, name="add-coupon"),
    path('remove-from-cart/<slug>/', remove_from_cart, name="remove-from-cart"),
    path(
        'remove_single_item_from_cart/<slug>/',
        remove_single_item_from_cart,
        name="remove-single-item-from-cart"
    ),
    # shop
    path('order-summary/', OrderSummaryView.as_view(), name="order-summary"),
    # these I messed up, I done the Stripe inclusion on Monday and Stripe payment intent Saturday...
    # It might make no sense to include two payment options both from Stripe
    # I wanted to implement both for the sake of practice
    # Them both work, but this set-up is not at all ment to go to production
    # Not that it was at all since the beggining
    path('checkout/payment/<payment_option>/', PaymentView.as_view(), name="payment"),
    path('create-payment-intent/', PaymentView.as_view(), name='payment-intent'),
    path('checkout/payment-intent/', StripeIntentView.as_view(), name="create-payment-intent"),
    # post payment views
    path('success/', SuccessView.as_view(), name="success"),
    path('cancel/', CanceledView.as_view(), name="canceled"),
    path('request-refund/', RequestRefund.as_view(), name="request-refund"),
    # stripe webhooks
    # for some reason those don't fire anymore
    path('stripe/webhook/', stripe_webhook_view, name="stripe-webhook")
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
