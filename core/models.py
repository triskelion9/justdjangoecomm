from django.conf import settings
from django.urls import reverse
from django.db import models
# Create your models here.


CATEGORIES = [
    ('S', 'Shirt'),
    ('SW', 'SportsWear'),
    ('OW', 'Outwear')
]

LABELS = [
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
]


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(null=True)
    category = models.CharField(choices=CATEGORIES, default='S', max_length=100)
    label = models.CharField(choices=LABELS, default='P', max_length=100)
    slug = models.SlugField(null=True)
    description = models.TextField()
    quantity = models.IntegerField(null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('add-to-cart', kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('remove-from-cart', kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
