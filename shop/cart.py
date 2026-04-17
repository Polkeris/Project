from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from beartype import beartype
from django.http import HttpRequest

from shop.models import Product


CartSession = dict[str, dict[str, str]]


@dataclass(frozen=True, slots=True)
class CartLine:
    product: Product
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity


@beartype
def _get_session_cart(request: HttpRequest) -> CartSession:
    cart = request.session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
        request.session["cart"] = cart
    return cart


@beartype
def cart_add(request: HttpRequest, product: Product, quantity: int = 1) -> None:
    cart = _get_session_cart(request)
    key = str(product.pk)
    if key not in cart:
        cart[key] = {"quantity": "0", "price": str(product.price)}
    cart[key]["quantity"] = str(int(cart[key]["quantity"]) + int(quantity))
    request.session.modified = True


@beartype
def cart_remove(request: HttpRequest, product_id: int) -> None:
    cart = _get_session_cart(request)
    key = str(product_id)
    if key in cart:
        del cart[key]
        request.session.modified = True


@beartype
def cart_clear(request: HttpRequest) -> None:
    request.session["cart"] = {}
    request.session.modified = True


@beartype
def cart_lines(request: HttpRequest) -> list[CartLine]:
    cart = _get_session_cart(request)
    product_ids: list[int] = [int(k) for k in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    product_map = {p.id: p for p in products}

    lines: list[CartLine] = []
    for k, row in cart.items():
        pid = int(k)
        product = product_map.get(pid)
        if product is None:
            continue
        qty = int(row.get("quantity", "0"))
        unit_price = Decimal(row.get("price", str(product.price)))
        if qty <= 0:
            continue
        lines.append(CartLine(product=product, quantity=qty, unit_price=unit_price))
    return lines


@beartype
def cart_total(request: HttpRequest) -> Decimal:
    total = Decimal("0")
    for line in cart_lines(request):
        total += line.total_price
    return total

