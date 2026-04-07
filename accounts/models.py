from django.db import models

class Product(models.Model):
    name = models.CharField("商品名", max_length=100)
    category = models.CharField("カテゴリ", max_length=50, blank=True)
    price = models.IntegerField("価格")
    description = models.TextField("説明", blank=True)

    def __str__(self):
        return self.name