from __future__ import annotations

from beartype import beartype
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch, Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from shop.cart import cart_add, cart_clear, cart_lines, cart_remove, cart_total
from shop.forms import CheckoutForm, ProductForm, SignUpForm, as_int
from shop.models import Category, Order, OrderItem, Product
from shop.product_images import delete_product_images, save_product_images


@beartype
def index(request: HttpRequest) -> HttpResponse:
    categories: QuerySet[Category] = Category.objects.all()
    products: QuerySet[Product] = (
        Product.objects.all().select_related("category").prefetch_related("images")
    )

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    context = {
        "categories": categories,
        "products": products,
        "selected_category": category_slug,
        "cart_total": cart_total(request),
    }
    return render(request, "index.html", context)


@beartype
def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        id=product_id,
    )
    context = {"product": product, "cart_total": cart_total(request)}
    return render(request, "product_detail.html", context)


@beartype
def signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(reverse("index"))

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("index"))
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


class ProductOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        obj = self.get_object()
        return getattr(obj, "author_id", None) == self.request.user.id


class ProductImageFormMixin:
    def _handle_product_images(self, product: Product) -> None:
        delete_ids = [
            int(pk)
            for pk in self.request.POST.getlist("delete_images")
            if pk.isdigit()
        ]
        delete_product_images(product, delete_ids)
        save_product_images(product, self.request.FILES.getlist("images"))


class ProductCreateView(ProductImageFormMixin, LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_form.html"

    def form_valid(self, form: ProductForm) -> HttpResponse:
        form.instance.author = self.request.user
        response = super().form_valid(form)
        self._handle_product_images(self.object)
        return response

    def get_success_url(self) -> str:
        return reverse("product_detail", kwargs={"product_id": self.object.id})


class ProductUpdateView(ProductImageFormMixin, ProductOwnerMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_form.html"

    def get_queryset(self) -> QuerySet[Product]:
        return super().get_queryset().prefetch_related("images")

    def form_valid(self, form: ProductForm) -> HttpResponse:
        response = super().form_valid(form)
        self._handle_product_images(self.object)
        return response

    def get_success_url(self) -> str:
        return reverse("product_detail", kwargs={"product_id": self.object.id})


class ProductDeleteView(ProductOwnerMixin, DeleteView):
    model = Product
    template_name = "product_confirm_delete.html"

    def get_success_url(self) -> str:
        return reverse("index")


@beartype
def cart_detail(request: HttpRequest) -> HttpResponse:
    context = {"lines": cart_lines(request), "total": cart_total(request)}
    return render(request, "cart.html", context)


@beartype
def cart_add_view(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    quantity = as_int(request.POST.get("quantity", "1"), default=1)
    if quantity <= 0:
        quantity = 1
    cart_add(request, product, quantity=quantity)

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(reverse("cart"))


@beartype
def cart_remove_view(request: HttpRequest, product_id: int) -> HttpResponse:
    cart_remove(request, product_id=product_id)
    return redirect(reverse("cart"))


@beartype
def checkout(request: HttpRequest) -> HttpResponse:
    lines = cart_lines(request)
    if not lines:
        return redirect(reverse("index"))

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                address=form.cleaned_data["address"],
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=line.product,
                        price=line.unit_price,
                        quantity=line.quantity,
                    )
                    for line in lines
                ]
            )
            cart_clear(request)
            return redirect(reverse("checkout_success", kwargs={"order_id": order.id}))
    else:
        initial: dict[str, str] = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
        form = CheckoutForm(initial=initial)

    context = {"form": form, "lines": lines, "total": cart_total(request)}
    return render(request, "checkout.html", context)


@beartype
def checkout_success(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)
    context = {"order": order}
    return render(request, "checkout_success.html", context)


@beartype
def _user_orders(user) -> QuerySet[Order]:
    return (
        Order.objects.filter(Q(user=user) | Q(email=user.email))
        .distinct()
        .prefetch_related(
            Prefetch(
                "items",
                queryset=OrderItem.objects.select_related("product"),
            )
        )
    )


@login_required
def order_list(request: HttpRequest) -> HttpResponse:
    orders = _user_orders(request.user)
    context = {"orders": orders}
    return render(request, "order_list.html", context)


@login_required
def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(
        _user_orders(request.user),
        id=order_id,
    )
    context = {"order": order}
    return render(request, "order_detail.html", context)
