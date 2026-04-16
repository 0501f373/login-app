from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField("カテゴリ名", max_length=50, unique=True)

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField("メーカー名", max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("商品名", max_length=100)
    category = models.ForeignKey(
        Category,
        verbose_name="カテゴリ",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name="メーカー名",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    price = models.IntegerField("価格")
    cost = models.IntegerField("仕入れ単価", default=0)
    description = models.TextField("説明", blank=True)
    stock = models.PositiveIntegerField("在庫数", default=0)
    image = models.ImageField("商品画像", upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name


class StockHistory(models.Model):
    STOCK_TYPE_CHOICES = [
        ("in", "入庫"),
        ("out", "出庫"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_histories")
    stock_type = models.CharField(max_length=10, choices=STOCK_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    before_stock = models.PositiveIntegerField()
    after_stock = models.PositiveIntegerField()
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} / {self.get_stock_type_display()} / {self.quantity}"