from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from ordersapp.models import Order
from django.db import transaction
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from basketapp.models import Basket
from ordersapp.models import Order, OrderItem
from ordersapp.forms import OrderItemForm
from mainapp.views import product, Product


class OrderList(ListView):
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_active=True)

    @method_decorator(login_required())
    def dispatch(self, *args, **kwargs):
        return super(ListView, self).dispatch(*args, **kwargs)

class OrderCreate(CreateView):
   model = Order
   success_url = reverse_lazy('order:list')
   fields = []

   def get_context_data(self, **kwargs):
       data = super().get_context_data(**kwargs)
       OrderFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
       if self.request.POST:
           formset = OrderFormSet(self.request.POST)
       else:
           basket_items = list(Basket.objects.filter(user=self.request.user))
           if len(basket_items):
               OrderFormSet = inlineformset_factory(
                   Order,
                   OrderItem,
                   form=OrderItemForm,
                   extra=len(basket_items)
               )
               formset = OrderFormSet()
               for num, form in enumerate(formset.forms):
                   form.initial['product'] = basket_items[num].product
                   form.initial['quantity'] = basket_items[num].quantity
                   form.initial['price'] = basket_items[num].product.price
               for basket_item in basket_items:
                   basket_item.delete()
           else:
               formset = OrderFormSet()
       data['orderitems'] = formset
       return data

   def form_valid(self, form):
       context = self.get_context_data()
       orderitems = context['orderitems']

       with transaction.atomic():
           Basket.get_items(self.request.user).delete()
           form.instance.user = self.request.user
           self.object = form.save()

           if orderitems.is_valid():
               orderitems.instance = self.object
               orderitems.save()

       if self.object.get_total_cost() == 0:
           self.object.delete()

       return super().form_valid(form)


class OrderUpdate(UpdateView):
    model = Order
    success_url = reverse_lazy('order:list')
    fields = []

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        OrderFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
        if self.request.POST:
            data['orderitems'] = OrderFormSet(self.request.POST, instance=self.object)
        else:
            # orderitems_formset = OrderFormSet(instance=self.object)
            queryset = self.object.orderitems.select_related()
            formset = OrderFormSet(instance=self.object, queryset=queryset)
            for form in formset.forms:
                if form.instance.pk:
                    form.initial['price'] = form.instance.product.price

        data['orderitems'] = orderitems_formset
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        orderitems = context['orderitems']

        with transaction.atomic():
            # form.instance.user = self.request.user
            self.object = form.save()

            if orderitems.is_valid():
                orderitems.instance = self.object
                orderitems.save()

        if self.object.get_total_cost() == 0:
            self.object.delete()

        return super().form_valid(form)


class OrderDelete(DeleteView):
    model = Order
    success_url = reverse_lazy('order:list')

class OrderRead(DetailView):
    model = Order


def forming_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = Order.SENT_TO_PROCEED
    order.save()

    return HttpResponseRedirect(reverse('order:list'))

@receiver(pre_save, sender=Basket)
@receiver(pre_save, sender=OrderItem)
def products_quantity_update_save(sender, update_fields, instance, **kwargs):
        if instance.pk:
            instance.product.quantity -= instance.quantity - instance.get_item(pk=instance.pk).quantity
        else:
            instance.product.quantity -= instance.quantity

        instance.product.save()

@receiver(pre_delete, sender=Basket)
@receiver(pre_delete, sender=OrderItem)
def products_quantity_update_delete(sender, instance, **kwargs):
        instance.product.quantity += instance.quantity
        instance.product.save()

def payment_result(request):
    # ik_co_id = 51237
    # daa8f2a2d8413000000 & ik_inv_id = 320477108 & \
     # ik_pm_no = ID1
    payment_status = request.GET.get('ik_inv_st')
    if payment_status == 'success':
        order_pk = request.GET.get('ik_pm_no').replace('ID', '')
        order_item = Order.objects.get(pk=order_pk)
        order_item.status = Order.PAID
        order_item.save()
    elif payment_status == 'fail':
        order_pk = request.GET.get('ik_pm_no').replace('ID', '')
        order_item = Order.objects.get(pk=order_pk)
        order_item.status = Order.UNPAID
        order_item.save()
    else:
        order_pk = request.GET.get('ik_pm_no').replace('ID', '')
        order_item = Order.objects.get(pk=order_pk)
        order_item.status = Order.PENDING
        order_item.save()
    return  HttpResponseRedirect(reverse('order:list'))

def get_product_price(request, pk):
    if request.is_ajax():
        product = Product.objects.filter(pk=pk).first()
        if product:
            return JsonResponse({'price': product.price})
        else:
            return JsonResponse({'price': 0})