from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView
from .models import Item, Order, OrderItem
# Create your views here.


class Home(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home-page.html'


class Product(DetailView):
    model = Item
    template_name = 'product-page.html'


def checkout(request):
    context = {
    }

    return render(request, 'checkout-page.html', context)


# Utils

def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item\'s quantity was updated.')

        else:
            messages.info(request, 'This item was added to your cart.')
            order.items.add(order_item)

    else:
        order = Order.objects.create(
            user=request.user,
            ordered_date=timezone.now()
        )
        messages.info(request, 'This item was added to your cart.')
        order.items.add(order_item)

    return redirect('product', slug=slug)


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )

    if order_qs.exists():
        order = order_qs[0]

        if order.items.filter(item__slug=item.slug).exists():
            order_item, created = OrderItem.objects.get_or_create(
                item=item,
                user=request.user,
                ordered=False
            )
            messages.info(request, 'This item was removed to your cart.')
            order.items.remove(order_item)
        else:
            messages.info(request, 'This item was not found in your cart.')

    else:
        messages.info(request, 'No active order found.')

    return redirect('product', slug=slug)
