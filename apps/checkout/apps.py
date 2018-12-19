import oscar.apps.checkout.apps as apps


class CheckoutConfig(apps.CheckoutConfig):
    label = 'checkout'
    name = 'apps.checkout'
    verbose_name = 'Checkout'

