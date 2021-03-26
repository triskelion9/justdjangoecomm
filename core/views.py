from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView, DetailView
from .models import Item, Order, OrderItem, Address, Refund, Coupon
from .forms import CheckoutForm, CouponForm, RefundForm
import json
import stripe
import random
import string
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

        shipping_address_qs = Address.objects.filter(
            user=self.request.user,
            address_type='S',
            default=True
        )

        if shipping_address_qs.exists():
            context.update({
                'default_shipping_address': shipping_address_qs[0]
            })

        billing_address_qs = Address.objects.filter(
            user=self.request.user,
            address_type='B',
            default=True
        )

        if billing_address_qs.exists():
            context.update({
                'default_billing_address': billing_address_qs[0]
            })

        return render(self.request, 'checkout-page.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    print('Using the default shipping address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, 'No default shipping address available')
                        return redirect('checkout')
                else:
                    print('User is entering a new shipping address')

                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address1,
                            appartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip,
                            address_type="S"
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, 'Please fill in the required shipping address fields')

                use_default_billing = form.cleaned_data.get('use_default_shipping')
                same_billing_address = form.cleaned_data.get('same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = "B"
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print('Using the default billing address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, 'No default billing address available')
                        return redirect('checkout')
                else:
                    print('User is entering a new billing address')

                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user = self.request.user,
                            street_address = billing_address1,
                            appartment_address = billing_address2,
                            country = billing_country,
                            zip = billing_zip,
                            address_type="B"
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, 'Please fill in the required billing address fields')

                payment_option = form.cleaned_data.get('payment_option')

                # Add redirect to the selected payment handler view
                if payment_option == 'S':
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'SI':
                    return redirect('payment-intent/')

            messages.warning(self.request, 'Failed checkout.')
            return redirect('checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('/')


class PaymentView(View):
    def get(self, *args, **kwargs):
        # order
        return render(self.request, "payment.html")

    def post(self, request, *args, **kwargs):
        YOUR_DOMAIN = 'http://127.0.0.1:8000'
        order = Order.objects.get(user=request.user, ordered=False)
        # construct the order items
        line_items = []
        products = []
        for item in order.items.all():
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(item.item.get_price() * 100),
                    'product_data': {
                        'name': item.item.title
                    },
                },
                'quantity': item.quantity
            })

            products.append(item.item.pk)
        # attach the order items to the order
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            metadata={
                'product_ids': json.dumps(products),
                'user': request.user
            },
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cancel/',
        )

        return JsonResponse({
            'id': checkout_session.id
        })


class SuccessView(View):
    def get(self, *args, **kwargs):
        return render(self.request, "payment-success.html")


class CanceledView(View):
    def get(self, *args, **kwargs):
        return render(self.request, "payment-canceled.html")


class RequestRefund(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request-refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')

            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reson = message
                refund.save()

                messages.info(self.request, 'Your request has reached us')
                return redirect('/')
            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect('request-refund')


class StripeIntentView(View):
    def get(self, *args, **kwargs):
        # order
        return render(self.request, "payment-intent.html")

    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        products = []
        for item in order.items.all():
            products.append({
                'name': item.item.title,
                'quantity': item.quantity
            })
        try:
            request_body = json.loads(request.body)
            customer = stripe.Customer.create(email=request_body['email'])
            intent = stripe.PaymentIntent.create(
                amount=int(order.get_total() * 100),
                currency='usd',
                customer = customer['id'],
                metadata={
                    'products': json.dumps(products)
                },
            )

            # Finish the order
            order.ordered = True
            order.save()

            return JsonResponse({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            print(str(e))
            return JsonResponse({'error': str(e)})


# Utility Functions


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


# @csrf_protect
# def create_payment(request):
#     intent = stripe.PaymentIntent.create(
#         amount=1400,
#         currency='usd'
#     )
#     return JsonResponse({
#         'clientSecret': intent['client_secret']
#     })


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


def create_refference_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # hook for complete purchase session
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_email = session['customer_details']['email']
        products = session['metadata']

        send_mail(
            subject="Here is your order infos",
            message="Thanks for your purchase",
            recipient_list=[customer_email],
            from_email="alin@jdecommerce.com"
        )

        # Fulfill the purchase...
        user = User.objects.get(username=session['metadata']['user'])
        order = Order.objects.get(user=user)
        order.ordered = True
        order.save()

    elif event['type'] == 'payment_intent.succeeded':
        session = event['data']['object']
        print(session)
        stripe_customer_id = session['customer']
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)
        stripe_customer_email = stripe_customer['email']

        products = session['metadata']['products']
        print(products)
        send_mail(
            subject="Here is your order infos",
            message="Thanks for your purchase, here's your ordered products" + json.load(products) + ".",
            recipient_list=[stripe_customer_email],
            from_email="alin@jdecommerce.com"
        )

    return HttpResponse(status=200)
