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
)

urlpatterns = [
    path('', Home.as_view(), name="home"),
    path('checkout/', Checkout.as_view(), name="checkout"),
    path('products/<slug:slug>/', Product.as_view(), name="product"),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # for real?
    path('add-to-cart/<slug>', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>', remove_from_cart, name="remove-from-cart"),
    path('remove_single_item_from_cart/<slug>',
        remove_single_item_from_cart,
        name="remove-single-item-from-cart"
    ),

    # shop
    path('order-summary/', OrderSummaryView.as_view(), name="order-summary")
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
