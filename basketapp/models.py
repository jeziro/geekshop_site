from django.db import models
from django.conf import settings
from mainapp.models import Product
from django.utils.functional import cached_property



class BasketQuerySet(models.QuerySet):

    def delete(self):
        for item in self:
            item.product.quantity += item.quantity
            item.product.save()
        super().delete()


class Basket(models.Model):
    objects = BasketQuerySet.as_manager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='basket')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='количество', default=0)
    add_datetime = models.DateTimeField(verbose_name='время добавления', auto_now_add=True)

    def _get_product_cost(self):
        "return cost of all products this type"
        return self.product.price * self.quantity

    product_cost = property(_get_product_cost)

    @cached_property
    def get_items_cached(self):
        return  self.user.basket.select_related()

    def get_total_quantity(self):
        "return total quantity for user"
        # _items = Basket.objects.filter(user=self.user)
        _items = self.get_items_cached
        return sum(list(map(lambda x: x.quantity, _items)))
        # _totalquantity = sum(list(map(lambda x: x.quantity, _items)))
        # return _totalquantity
        #
        # total_quantity = property(_get_total_quantity)
        #
    
    def get_total_cost(self):
        "return total cost for user"
        _items = self.get_items_cached
        return sum(list(map(lambda x: x.product_cost, _items)))
        # _items = Basket.objects.filter(user=self.user)
        # _totalcost = sum(list(map(lambda x: x.product_cost, _items)))
        # return _totalcost
        #
        # total_cost = property(_get_total_cost)

    @staticmethod
    def get_items(user):
        return Basket.objects.filter(user=user).order_by('product__category')

    @staticmethod
    def get_product(user, product):
        return Basket.objects.filter(user=user, product=product)

    @classmethod
    def get_products_quantity(cls, user):
        basket_items = cls.get_items(user)
        basket_items_dic = {}
        [basket_items_dic.update({item.product: item.quantity}) for item in basket_items]

        return basket_items_dic

    @staticmethod
    def get_item(pk):
        return Basket.objects.get(pk=pk)

    @staticmethod
    def get_items(user):
        return Basket.objects.filter(user=user).order_by('product__category')

    # def delete(self, *args, **kwargs):
    #     self.product.quantity += self.quantity
    #     self.product.save()
    #     super().delete()
    #
    # def save(self, *args, **kwargs):
    #     if self.pk:
    #         self.product.quantity -= self.quantity - self.__class__.objects.get(pk=self.pk).quantity
    #     else:
    #         self.product.quantity -= self.quantity
    #
    #     super().save(*args, **kwargs)
