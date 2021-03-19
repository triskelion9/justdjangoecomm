from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.views.generic import View, ListView, DetailView
from .models import Item, Order, OrderItem, BillingAddress, Payment
from .forms import CheckoutForm, CouponForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
import stripe
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY


class Home(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home-page.html'


class Product(DetailView):
    model = Item
    template_name = 'product-page.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('/')


class Checkout(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form,
            'couponForm': CouponForm(),
            'order': Order.objects.get(user=self.request.user, ordered=False)
        }
        return render(self.request, 'checkout-page.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                appartment_address = form.cleaned_data.get('appartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: Add functionality for these two
                # same_shipping_address_as_billing = form.cleaned_data.get('same_shipping_address_as_billing')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    appartment_address = appartment_address,
                    country = country,
                    zip = zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                # Add redirect to the selected payment handler view
                if payment_option == 'S':
                    print(self.request)
                    return redirect('payment', payment_option='stripe')

            messages.warning(self.request, 'Failed checkout.')
            return redirect('checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('/')


class PaymentView(View):
    def get(self, *args, **kwargs):
        # order
        return render(self.request, "payment.html")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.user, ordered=False)
        token = self.request.POST.get('stripeToken')  # None
        ammount = order.get_total()
        charge = stripe.Charge.create(
            amount=int(order.get_total() * 100),
            currency="usd",
            source=token,
        )

        # create payment
        payment = Payment()
        payment.stripe_charge_id = charge['id']
        payment.user = self.request.user
        payment.ammount = ammount
        payment.save()

        # assign payment to order
        order.ordered = True
        order.payment = payment
        order.save()

        messages.success(self.request, 'Your order has been placed')
        return redirect("/")


@csrf_protect
def create_payment(request):
    intent = stripe.PaymentIntent.create(
        amount=1400,
        currency='usd'
    )
    return JsonResponse({
        'clientSecret': intent['client_secret']
    })


# Utils


@login_required
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

    return redirect('order-summary')


@login_required
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

    return redirect('order-summary')


@login_required
def remove_single_item_from_cart(request, slug):
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
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                messages.info(request, 'This item was removed to your cart.')
                order.items.remove(order_item)
        else:
            messages.info(request, 'This item was not found in your cart.')

    else:
        messages.info(request, 'No active order found.')

    return redirect('order-summary')


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
    except ObjectDoesNotExist:
        messages.info(request, "This coupon is not valid.")
        return redirect('checkout')

    return coupon


def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST or None)
        if form.is_valid():
            try:
                order = Order.objects.get(
                    user = request.user,
                    ordered = False
                )

                code = form.cleaned_data.get('code')
                order.coupon = get_coupon(request, code)
                order.save()
                messages.info(request, 'Successfully added coupon')
                return redirect('checkout')
            except ObjectDoesNotExist:
                messages.info(request, 'Could not use that coupon.')
                return redirect('checkout')
    return None
