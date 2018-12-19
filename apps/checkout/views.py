from django.dispatch import receiver
from django.conf import settings
from django.views.generic import FormView
from django.utils.translation import ugettext as _
from django.urls import reverse, reverse_lazy

from oscar.apps.order.signals import order_placed
from oscar.apps.checkout import exceptions
from oscar.apps.checkout.signals import post_checkout
from oscar_invoices.utils import InvoiceCreator
from oscar_invoices.models import Invoice
from oscar.core.loading import get_model, get_class


from . import forms
from .forms import OSCAR_PAYMENT_METHODS


Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")
OscarPaymentMethodView = get_class("checkout.views", "PaymentMethodView")
OscarPaymentDetailsView = get_class("checkout.views", "PaymentDetailsView")
Order = get_model('order', 'Order')
OscarThankYouView = get_class("checkout.views", "ThankYouView")


class PaymentMethodView(OscarPaymentMethodView, FormView):
    form_class = forms.PaymentMethodForm
    template_name = "checkout/payment_method.html"
    step = 'payment-method'
    success_url = reverse_lazy('checkout:payment-details')

    skip_conditions = ['skip_unless_payment_is_required']

    def get(self, request, *args, **kwargs):
        if len(OSCAR_PAYMENT_METHODS) == 1:
            self.checkout_session.pay_by(OSCAR_PAYMENT_METHODS[0][0])
            return redirect(self.get_success_url())
        else:
            return FormView.get(self, request, *args, **kwargs)

    def get_initial(self):
        return {'payment_method': self.checkout_session.payment_method(),}

    def get_success_url(self, *args, **kwargs):
        return reverse_lazy('checkout:preview')

    def form_valid(self, form):
        self.checkout_session.pay_by(form.cleaned_data['payment_method'])
        return super().form_valid(form)


class PaymentDetailsView(OscarPaymentDetailsView):

    def handle_payment(self, order_number, order_total, **kwargs):
        method = self.checkout_session.payment_method()
        if method == 'invoice':
            source_type, _ = SourceType.objects.get_or_create(name=method)
            source = Source(source_type=source_type,
                currency=order_total.currency,
                amount_allocated=order_total.excl_tax
            )
            self.add_payment_source(source)

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)
        ctx.update({'payment_method': self.checkout_session.payment_method()})
        return ctx


class ThankYouView(OscarThankYouView):
    def get_context_data(self, **kwargs):
        ctx = super(ThankYouView, self).get_context_data(**kwargs)
        try:
            f = self.object.invoice.document
            f.open(mode='rb')
            lines = f.read()
            f.close()
            ctx.update({'invoice': lines.decode('utf-8')})
        except Invoice.DoesNotExist:
            pass
        return ctx


@receiver(post_checkout)
def create_invoice(sender, order, user, **kwargs):
    for source in order.sources.all():
        if source.source_type.name == 'invoice':
            invoice = InvoiceCreator()
            invoice.create_invoice(order=order)

