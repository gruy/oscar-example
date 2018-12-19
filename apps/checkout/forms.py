from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


OSCAR_PAYMENT_METHODS = (
    ('invoice', _('Invoice')),
    ('yandex_money', _('Yandex.Money')),
)


class PaymentMethodForm(forms.Form):
    payment_method = forms.ChoiceField(
        label=_("Select a payment method"),
        choices=OSCAR_PAYMENT_METHODS,
        widget=forms.RadioSelect()
    )


def get_payment_method_display(payment_method):
    return dict(OSCAR_PAYMENT_METHODS).get(payment_method)

