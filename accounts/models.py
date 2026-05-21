from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


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
    is_visible = models.BooleanField("商品一覧に表示", default=True)
    created_at = models.DateTimeField("登録日", auto_now_add=True)
    display_order = models.PositiveIntegerField("表示順", default=0)

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
    
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name
    

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ("pending", "受付中"),
        ("payment_waiting", "入金待ち"),
        ("preparing", "発送準備中"),
        ("shipped", "発送済み"),
        ("cancelled", "キャンセル"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    total_price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField("支払い方法", max_length=50, default="credit_card")

    delivery_name = models.CharField("配送先氏名", max_length=100, blank=True)
    delivery_phone_number = models.CharField("配送先電話番号", max_length=20, blank=True)
    delivery_postal_code = models.CharField("配送先郵便番号", max_length=20, blank=True)
    delivery_prefecture = models.CharField("配送先都道府県", max_length=50, blank=True)
    delivery_city = models.CharField("配送先市区町村", max_length=100, blank=True)
    delivery_address = models.CharField("配送先番地", max_length=200, blank=True)
    delivery_building = models.CharField("配送先建物名", max_length=200, blank=True)
    delivery_date = models.DateField("配送希望日", null=True, blank=True)
    delivery_time = models.CharField("配送希望時間",max_length=50,blank=True,null=True)
    delivery_address_id = models.IntegerField(null=True, blank=True)
    tracking_number = models.CharField("伝票番号", max_length=100, blank=True)

    def __str__(self):
        return f"注文ID:{self.id} / {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.IntegerField()

    def __str__(self):
        return self.product.name
    
class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    postal_code = models.CharField("郵便番号", max_length=10)
    prefecture = models.CharField("都道府県", max_length=50)
    city = models.CharField("市区町村", max_length=100)
    address = models.CharField("番地", max_length=200)
    building = models.CharField("建物名", max_length=200, blank=True)

    is_main = models.BooleanField("メイン住所", default=False)
    created_at = models.DateTimeField("登録日", auto_now_add=True)
    name = models.CharField("氏名", max_length=100)
    phone_number = models.CharField("電話番号", max_length=20)

    def __str__(self):
        main_label = "【メイン】" if self.is_main else ""
        return f"{main_label}{self.user.email} / {self.prefecture}{self.city}{self.address}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField("電話番号", max_length=20, blank=True)


    def __str__(self):
        return self.user.email