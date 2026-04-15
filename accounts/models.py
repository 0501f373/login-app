from django.db import models


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
    description = models.TextField("説明", blank=True)
    stock = models.PositiveIntegerField("在庫数", default=0)
    image = models.ImageField("商品画像", upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name