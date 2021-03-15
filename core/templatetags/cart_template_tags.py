from django import template
from core.models import Order

register = template.Library()


# creating a custom filter for getting # items from order, on a per-user basis
@register.filter
def cart_item_count(user):
    # this counts the order items of an order
    # if you have two products alike they count as one order item
    if user.is_authenticated:
        query_set = Order.objects.filter(user=user, ordered=False)

        if query_set.exists():
            return query_set[0].items.count()

    return 0
