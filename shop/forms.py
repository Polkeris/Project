from __future__ import annotations

from beartype import beartype
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from shop.models import Product


class CheckoutForm(forms.Form):
    first_name = forms.CharField(label="Имя", max_length=100)
    last_name = forms.CharField(label="Фамилия", max_length=100)
    email = forms.EmailField(label="Эл. почта")
    address = forms.CharField(label="Адрес", widget=forms.Textarea(attrs={"rows": 3}))


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="Эл. почта", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "category",
            "name",
            "description",
            "price",
        )


@beartype
def as_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

