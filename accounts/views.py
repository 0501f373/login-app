import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator

from .models import Product, Category, Manufacturer, StockHistory, ProductImage, Order, OrderItem, Address
from .forms import ProductForm
from django.urls import reverse
from django.contrib import messages

def validate_password_policy(password):
    errors = []

    if len(password) < 8:
        errors.append("パスワードは8文字以上で入力してください")

    if not re.search(r"[A-Za-z]", password):
        errors.append("パスワードにはアルファベットを含めてください")

    if not re.search(r"\d", password):
        errors.append("パスワードには数字を含めてください")

    return errors


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email:
            return render(request, "accounts/login.html", {
                "error": "メールアドレスを入力してください"
            })

        if not password:
            return render(request, "accounts/login.html", {
                "error": "パスワードを入力してください"
            })

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)

            pending = request.session.pop("pending_cart", None)

            if pending:
                cart = request.session.get("cart", {})
                product_id = str(pending["product_id"])
                quantity = pending["quantity"]

                cart[product_id] = cart.get(product_id, 0) + quantity

                request.session["cart"] = cart
                request.session.modified = True

                return redirect("cart")

            next_url = request.session.pop("next", "product_search")
            return redirect(next_url)

        return render(request, "accounts/login.html", {
            "error": "メールアドレスまたはパスワードが違います"
        })

    return render(request, "accounts/login.html")

def signup_view(request):
    if request.method == "POST":
        display_name = request.POST.get("display_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        errors = []

        if not display_name:
            errors.append("ユーザー名を入力してください")
        elif re.search(r"\s", display_name):
            errors.append("ユーザー名に空白は使用できません")

        if not email:
            errors.append("メールアドレスを入力してください")
        elif User.objects.filter(email__iexact=email).exists():
            errors.append("このメールアドレスはすでに登録されています")

        if not password:
            errors.append("パスワードを入力してください")

        if password != password_confirm:
            errors.append("パスワードが一致しません")

        errors.extend(validate_password_policy(password))

        if errors:
            return render(request, "accounts/signup.html", {
                "errors": errors,
                "display_name": display_name,
                "email": email,
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=display_name,
        )

        login(request, user)
        next_url = request.POST.get("next") or request.GET.get("next") or "product_search"
        return redirect(next_url)

    return render(request, "accounts/signup.html")


def home_view(request):
    return HttpResponse("ログイン成功！")


def product_search(request):
    keyword = request.GET.get("keyword", "")
    category = request.GET.get("category", "")
    manufacturer = request.GET.get("manufacturer", "")
    page_number = request.GET.get("page")

    cart = request.session.get("cart", {})
    cart_count = sum(cart.values())

    products = Product.objects.select_related("category", "manufacturer")\
    .filter(is_visible=True)\
    .order_by("-created_at")

    if keyword:
        products = products.filter(name__icontains=keyword)

    if category:
        products = products.filter(category_id=category)

    if manufacturer:
        products = products.filter(manufacturer_id=manufacturer)

    paginator = Paginator(products, 10)  # 1ページ10件
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()

    return render(request, "accounts/product_search.html", {
        "keyword": keyword,
        "category": category,
        "manufacturer": manufacturer,
        "categories": categories,
        "manufacturers": manufacturers,
        "products": page_obj,
        "page_obj": page_obj,
        "cart_count": cart_count,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity_range = range(1, product.stock + 1) if product.stock > 0 else []
    next_page = request.GET.get("next", "")

    return render(request, "accounts/product_detail.html", {
        "product": product,
        "quantity_range": quantity_range,
        "next_page": next_page,
    })


from django.shortcuts import redirect, get_object_or_404

def add_to_cart(request, product_id):
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        if product.stock == 0:
            return redirect("product_detail", product_id=product.id)

        if quantity > product.stock:
            quantity = product.stock

        cart = request.session.get("cart", {})

        if not isinstance(cart, dict):
            cart = {}

        product_id_str = str(product_id)

        if product_id_str in cart:
            cart[product_id_str] += quantity
        else:
            cart[product_id_str] = quantity

        request.session["cart"] = cart
        request.session.modified = True

        return redirect("cart")

    return redirect("product_search")

def cart_view(request):
    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    cart_items = []
    total_price = 0
    valid_cart = {}

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        subtotal = product.price * quantity
        total_price += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

        valid_cart[str(product_id)] = quantity

    request.session["cart"] = valid_cart

    return render(request, "accounts/cart.html", {
        "cart_items": cart_items,
        "total_price": total_price,
    })

from django.contrib.auth.decorators import login_required

@login_required(login_url="login")
def mypage(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    cart_count = sum(cart.values())

    address = Address.objects.filter(user=request.user).first()

    return render(request, "accounts/mypage.html", {
        "orders": orders,
        "cart_count": cart_count,
        "address": address,
    })

def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    request.session["cart"] = cart
    return redirect("cart")


def update_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        product_id_str = str(product_id)

        if not isinstance(cart, dict):
            cart = {}

        if product_id_str in cart:
            quantity = int(request.POST.get("quantity", 0))
            product = get_object_or_404(Product, id=product_id)

            if quantity <= 0:
                del cart[product_id_str]
                request.session["cart"] = cart
                return redirect("cart")

            if quantity > product.stock:
                cart_items = []
                total_price = 0

                for pid, qty in cart.items():
                    item_product = get_object_or_404(Product, id=pid)
                    subtotal = item_product.price * qty
                    total_price += subtotal

                    cart_items.append({
                        "product": item_product,
                        "quantity": qty,
                        "subtotal": subtotal,
                    })

                return render(request, "accounts/cart.html", {
                    "cart_items": cart_items,
                    "total_price": total_price,
                    "error": f"{product.name} の在庫が不足しています。在庫は {product.stock} 点です。",
                })

            cart[product_id_str] = quantity
            request.session["cart"] = cart

    return redirect("cart")

def order_confirm(request):
    # 未ログインならログインへ
    if not request.user.is_authenticated:
        request.session["next"] = "order_confirm"
        return redirect("login")

    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    if not cart:
        return redirect("cart")
    
    if not Address.objects.filter(user=request.user).exists():
        return redirect("address_input")

    # 👇 GET → 確認画面
    if request.method == "GET":
        cart_items = []
        total_price = 0

        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            subtotal = product.price * quantity
            total_price += subtotal

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

        address = Address.objects.get(user=request.user)
        payment_method = request.session.get("payment_method", "credit_card")
        delivery_date = request.session.get("delivery_date")
        delivery_time = request.session.get("delivery_time")

        return render(request, "accounts/order_confirm.html", {
            "cart_items": cart_items,
            "total_price": total_price,
            "address": address,
            "payment_method": payment_method,
            "delivery_date": delivery_date,
            "delivery_time": delivery_time,
        })

    # 👇 POST → 注文確定
    total_price = 0

    # 在庫チェック
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)

        if product.stock < quantity:
            messages.error(request, f"{product.name} の在庫が不足しています")
            return redirect("cart")

    payment_method = request.session.get("payment_method", "credit_card")
    delivery_date = request.session.get("delivery_date")
    delivery_time = request.session.get("delivery_time")

    address = Address.objects.get(user=request.user)
    # 注文作成
    order = Order.objects.create(
    user=request.user,
    total_price=0,
    payment_method=payment_method,
    delivery_date=delivery_date if delivery_date else None,
    delivery_time=delivery_time if delivery_time else None,
)

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        total_price += subtotal

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        product.stock -= quantity
        product.save()

    order.total_price = total_price
    order.save()

    request.session["cart"] = {}
    request.session.modified = True

    return redirect("order_complete")

def order_complete(request):
    return render(request, "accounts/order_complete.html")

def logout_view(request):
    cart = request.session.get("cart", {})

    logout(request)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("product_search")

from django.urls import reverse

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

@staff_member_required(login_url="staff_login")
def product_create(request):
    next_page = request.GET.get("next") or request.POST.get("next", "")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        images = request.FILES.getlist("images")

        if len(images) > 5:
            form.add_error(None, "画像は最大5枚まで登録できます。")

        if form.is_valid():
            product = form.save()

            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )

            messages.success(request, "商品を登録しました")
            return redirect(f"{reverse('product_detail', args=[product.id])}?next=product_create")
    else:
        form = ProductForm()

    return render(request, "accounts/product_form.html", {
        "form": form,
        "page_title": "商品登録",
        "next_page": next_page,
    })


@staff_member_required(login_url="staff_login")
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    next_page = request.GET.get("next") or request.POST.get("next", "")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        images = request.FILES.getlist("images")

        current_image_count = product.images.count()

        if current_image_count + len(images) > 5:
            form.add_error(None, "画像は最大5枚まで登録できます。")

        if form.is_valid():
            product = form.save()

            for image in images:
                ProductImage.objects.create(product=product, image=image)

            messages.success(request, "商品を保存しました")
            return redirect(f"{reverse('product_detail', args=[product.id])}?next=management_product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "accounts/product_form.html", {
        "form": form,
        "product": product,
        "page_title": "商品編集",
        "next_page": next_page,
    })

@staff_member_required(login_url="staff_login")
def category_create(request):
    message = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if name:
            Category.objects.get_or_create(name=name)
            message = "カテゴリを登録しました"

    categories = Category.objects.all().order_by("name")

    return render(request, "accounts/category_form.html", {
        "message": message,
        "categories": categories,
    })

@staff_member_required(login_url="staff_login")
def management_menu(request):
    return render(request, "accounts/management_menu.html")

@staff_member_required(login_url="staff_login")
def product_edit_menu(request):
    categories = Category.objects.prefetch_related("product_set").all().order_by("name")
    uncategorized_products = Product.objects.filter(category__isnull=True)

    return render(request, "accounts/product_edit_menu.html", {
        "categories": categories,
        "uncategorized_products": uncategorized_products,
    })

@staff_member_required(login_url="staff_login")
def management_product_list(request):
    keyword = request.GET.get("keyword", "")
    category = request.GET.get("category", "")
    manufacturer = request.GET.get("manufacturer", "")
    page_number = request.GET.get("page")

    products = Product.objects.select_related("category", "manufacturer").all()

    if keyword:
        products = products.filter(name__icontains=keyword)

    if category:
        products = products.filter(category_id=category)

    if manufacturer:
        products = products.filter(manufacturer_id=manufacturer)

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all().order_by("name")
    manufacturers = Manufacturer.objects.all().order_by("name")

    return render(request, "accounts/management_product_list.html", {
        "products": page_obj,
        "page_obj": page_obj,
        "keyword": keyword,
        "category": category,
        "manufacturer": manufacturer,
        "categories": categories,
        "manufacturers": manufacturers,
    })

@staff_member_required(login_url="staff_login")
def manufacturer_create(request):
    message = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if name:
            Manufacturer.objects.get_or_create(name=name)
            message = "メーカーを登録しました"

    manufacturers = Manufacturer.objects.all().order_by("name")

    return render(request, "accounts/manufacturer_form.html", {
        "message": message,
        "manufacturers": manufacturers,
    })

@staff_member_required(login_url="staff_login")
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    next_page = request.GET.get("next") or request.POST.get("next", "")

    if request.method == "POST":
        product.delete()

        if next_page == "management_product_list":
            return redirect("management_product_list")

        if next_page == "product_edit":
            return redirect("management_product_list")

        return redirect("management_menu")

    return render(request, "accounts/product_confirm_delete.html", {
        "product": product,
        "next_page": next_page,
    })

def staff_login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email:
            return render(request, "accounts/staff_login.html", {
                "error": "メールアドレスを入力してください"
            })

        if not password:
            return render(request, "accounts/staff_login.html", {
                "error": "パスワードを入力してください"
            })

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("management_menu")

        return render(request, "accounts/staff_login.html", {
            "error": "管理者アカウントでログインしてください"
        })

    return render(request, "accounts/staff_login.html")

def staff_logout_view(request):
    logout(request)
    return redirect("staff_login")

@staff_member_required(login_url="staff_login")
def staff_signup_view(request):
    if request.method == "POST":
        display_name = request.POST.get("display_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        errors = []

        if not display_name:
            errors.append("ユーザー名を入力してください")

        if not email:
            errors.append("メールアドレスを入力してください")
        elif User.objects.filter(email__iexact=email).exists():
            errors.append("このメールアドレスはすでに登録されています")

        if not password:
            errors.append("パスワードを入力してください")

        if password != password_confirm:
            errors.append("パスワードが一致しません")

        errors.extend(validate_password_policy(password))

        if errors:
            return render(request, "accounts/staff_signup.html", {
                "errors": errors,
                "display_name": display_name,
                "email": email,
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=display_name,
        )
        user.is_staff = True
        user.save()

        messages.success(request, "管理者を登録しました")
        return redirect("staff_signup")

    return render(request, "accounts/staff_signup.html")

@staff_member_required(login_url="staff_login")
def staff_list_view(request):
    staff_users = User.objects.filter(is_staff=True).order_by("id")

    return render(request, "accounts/staff_list.html", {
        "staff_users": staff_users,
    })

@staff_member_required(login_url="staff_login")
def staff_delete_view(request, user_id):
    staff_user = get_object_or_404(User, id=user_id, is_staff=True)

    if request.method == "POST":
        staff_user.delete()
        messages.success(request, "管理者を削除しました")
        return redirect("staff_list")

    return render(request, "accounts/staff_confirm_delete.html", {
        "staff_user": staff_user,
    })

@staff_member_required(login_url="staff_login")
def stock_history_list(request):
    product_id = request.GET.get("product")
    page_number = request.GET.get("page")

    histories = StockHistory.objects.select_related("product", "updated_by").order_by("-created_at")
    products = Product.objects.all().order_by("name")

    if product_id:
        histories = histories.filter(product_id=product_id)

    paginator = Paginator(histories, 10)   # 1ページ10件
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/stock_history_list.html", {
        "histories": page_obj,
        "page_obj": page_obj,
        "products": products,
        "selected_product": product_id,
    })

@staff_member_required(login_url="staff_login")
def stock_management(request):
    keyword = request.GET.get("keyword", "")
    category = request.GET.get("category", "")
    manufacturer = request.GET.get("manufacturer", "")
    page_number = request.GET.get("page")

    products = Product.objects.select_related("category", "manufacturer").all().order_by("id")

    if keyword:
        products = products.filter(name__icontains=keyword)

    if category:
        products = products.filter(category_id=category)

    if manufacturer:
        products = products.filter(manufacturer_id=manufacturer)

    paginator = Paginator(products, 10)   # 1ページ10件
    page_obj = paginator.get_page(page_number)

    for p in page_obj:
        p.profit = p.price - p.cost

    categories = Category.objects.all().order_by("name")
    manufacturers = Manufacturer.objects.all().order_by("name")

    return render(request, "accounts/stock_management.html", {
        "products": page_obj,
        "page_obj": page_obj,
        "keyword": keyword,
        "category": category,
        "manufacturer": manufacturer,
        "categories": categories,
        "manufacturers": manufacturers,
    })


@staff_member_required(login_url="staff_login")
def stock_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        stock_type = request.POST.get("stock_type")
        quantity_str = request.POST.get("quantity", "0").strip()

        if not quantity_str.isdigit():
            messages.error(request, "数量は数字で入力してください")
            return redirect("stock_management")

        quantity = int(quantity_str)

        if quantity <= 0:
            messages.error(request, "数量は1以上で入力してください")
            return redirect("stock_management")

        before_stock = product.stock

        if stock_type == "in":
            after_stock = before_stock + quantity
        elif stock_type == "out":
            if quantity > before_stock:
                messages.error(request, f"{product.name} の在庫が不足しています")
                return redirect("stock_management")
            after_stock = before_stock - quantity
        else:
            messages.error(request, "更新種別が不正です")
            return redirect("stock_management")

        product.stock = after_stock
        product.save()

        StockHistory.objects.create(
            product=product,
            stock_type=stock_type,
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            updated_by=request.user,
        )

        messages.success(request, f"{product.name} の在庫を更新しました")

    return redirect("stock_management")

@staff_member_required(login_url="staff_login")
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.delete()
        messages.success(request, "カテゴリを削除しました")
        return redirect("category_create")

    # 👇ここがポイント（確認画面を表示）
    return render(request, "accounts/category_confirm_delete.html", {
        "category": category,
    })

@staff_member_required(login_url="staff_login")
def manufacturer_delete(request, manufacturer_id):
    manufacturer = get_object_or_404(Manufacturer, id=manufacturer_id)

    if request.method == "POST":
        manufacturer.delete()
        messages.success(request, "メーカーを削除しました")
        return redirect("manufacturer_create")

    return render(request, "accounts/manufacturer_confirm_delete.html", {
        "manufacturer": manufacturer,
    })

@staff_member_required(login_url="staff_login")
def product_image_delete(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id

    if request.method == "POST":
        image.delete()
        messages.success(request, "画像を削除しました")

    return redirect("product_edit", product_id=product_id)

@staff_member_required(login_url="staff_login")
def management_order_list(request):
    orders = Order.objects.select_related("user").order_by("-created_at")

    return render(request, "accounts/management_order_list.html", {
        "orders": orders,
    })

@login_required(login_url="login")
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, "accounts/order_detail.html", {
        "order": order,
    })

@staff_member_required(login_url="staff_login")
def management_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related("user"), id=order_id)

    return render(request, "accounts/management_order_detail.html", {
        "order": order,
    })

@login_required(login_url="login")
def address_input(request):
    address = Address.objects.filter(user=request.user).first()

    if request.method == "POST":
        address_type = request.POST.get("address_type")

        if address_type == "registered":
            saved_address = Address.objects.filter(user=request.user).first()

            postal_code = saved_address.postal_code
            prefecture = saved_address.prefecture
            city = saved_address.city
            addr = saved_address.address
            building = saved_address.building

        else:
            postal_code = request.POST.get("postal_code")
            prefecture = request.POST.get("prefecture")
            city = request.POST.get("city")
            addr = request.POST.get("address")
            building = request.POST.get("building")
            
            if not postal_code or not prefecture or not city or not addr:
                return render(request, "accounts/address_form.html", {
                    "address": address,
                    "error": "配送先住所を入力してください。",
                })

            if request.POST.get("save_to_mypage") == "1":
                Address.objects.update_or_create(
                    user=request.user,
                    defaults={
                        "postal_code": postal_code,
                        "prefecture": prefecture,
                        "city": city,
                        "address": addr,
                        "building": building,
                    }
                )

        delivery_date = request.POST.get("delivery_date")
        delivery_time = request.POST.get("delivery_time")
        payment_method = request.POST.get("payment_method", "credit_card")

        request.session["delivery_date"] = delivery_date
        request.session["delivery_time"] = delivery_time
        request.session["payment_method"] = payment_method
        request.session.modified = True

        return redirect("order_confirm")

    return render(request, "accounts/address_form.html", {
        "address": address
    })

from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from django.db.models import Count

@login_required(login_url="login")
def order_address_edit(request):
    address = Address.objects.filter(user=request.user).first()

    if request.method == "POST":
        postal_code = request.POST.get("postal_code")
        prefecture = request.POST.get("prefecture")
        city = request.POST.get("city")
        addr = request.POST.get("address")
        building = request.POST.get("building")

        if not postal_code or not prefecture or not city or not addr:
            return render(request, "accounts/order_address_edit.html", {
                "address": address,
                "error": "配送先住所を入力してください。",
            })

        Address.objects.update_or_create(
            user=request.user,
            defaults={
                "postal_code": postal_code,
                "prefecture": prefecture,
                "city": city,
                "address": addr,
                "building": building,
            }
        )

        return redirect("order_confirm")

    return render(request, "accounts/order_address_edit.html", {
        "address": address,
    })


@login_required(login_url="login")
def order_payment_edit(request):
    if request.method == "POST":
        request.session["payment_method"] = request.POST.get("payment_method", "credit_card")
        request.session.modified = True
        return redirect("order_confirm")

    return render(request, "accounts/order_payment_edit.html")


@login_required(login_url="login")
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    # 👇 月検索
    month = request.GET.get("month")

    if month:
        year, month_num = month.split("-")
        orders = orders.filter(created_at__year=year, created_at__month=month_num)

    # 👇 月リスト作成（ドロップダウン用）
    months = (
        Order.objects.filter(user=request.user)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("-month")
    )

    # 👇 ページネーション
    paginator = Paginator(orders, 5)  # 1ページ5件
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/order_list.html", {
        "page_obj": page_obj,
        "months": months,
        "selected_month": month,
    })

@login_required(login_url="login")
def mypage_address_edit(request):
    address = Address.objects.filter(user=request.user).first()

    if request.method == "POST":
        postal_code = request.POST.get("postal_code")
        prefecture = request.POST.get("prefecture")
        city = request.POST.get("city")
        addr = request.POST.get("address")
        building = request.POST.get("building")

        Address.objects.update_or_create(
    user=request.user,
    defaults={
        "postal_code": postal_code,
        "prefecture": prefecture,
        "city": city,
        "address": addr,
        "building": building,
    }
)

        return redirect("mypage")

    return render(request, "accounts/mypage_address_edit.html", {
        "address": address,
    })

@login_required(login_url="login")
def order_address_edit(request):
    address = Address.objects.filter(user=request.user).first()

    if request.method == "POST":
        Address.objects.update_or_create(
            user=request.user,
            defaults={
                "postal_code": request.POST.get("postal_code"),
                "prefecture": request.POST.get("prefecture"),
                "city": request.POST.get("city"),
                "address": request.POST.get("address"),
                "building": request.POST.get("building"),
            }
        )
        return redirect("order_confirm")

    return render(request, "accounts/order_address_edit.html", {
        "address": address,
    })


@login_required(login_url="login")
def order_payment_edit(request):
    if request.method == "POST":
        request.session["payment_method"] = request.POST.get("payment_method", "credit_card")
        request.session.modified = True
        return redirect("order_confirm")

    return render(request, "accounts/order_payment_edit.html")