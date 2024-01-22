from django.dispatch import Signal

sample_frozen = Signal(providing_args=["sample", "request"])
