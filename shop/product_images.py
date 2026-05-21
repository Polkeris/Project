from __future__ import annotations

from beartype import beartype
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Max

from shop.models import Product, ProductImage


@beartype
def save_product_images(product: Product, files: list[UploadedFile]) -> None:
    if not files:
        return

    start = (
        product.images.aggregate(max_pos=Max("position")).get("max_pos") or 0
    )
    created = False
    for index, file in enumerate(files):
        if not file:
            continue
        ProductImage.objects.create(
            product=product,
            image=file,
            position=start + index + 1,
        )
        created = True
    if created:
        _sync_legacy_image(product)


@beartype
def delete_product_images(product: Product, image_ids: list[int]) -> None:
    if not image_ids:
        return
    product.images.filter(id__in=image_ids).delete()
    _sync_legacy_image(product)


@beartype
def _sync_legacy_image(product: Product) -> None:
    first = product.images.order_by("position", "id").first()
    if first:
        product.image = first.image
    else:
        product.image = ""
    product.save(update_fields=["image"])
