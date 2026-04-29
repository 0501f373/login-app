from django import forms
from .models import Product, Category, Manufacturer


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="カテゴリを選択してください"
    )

    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        empty_label="メーカーを選択してください"
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "manufacturer",
            "price",
            "cost",
            "description",
            "is_visible",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "cost": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].error_messages["required"] = "商品名を入力してください"
        self.fields["price"].error_messages["required"] = "価格を入力してください"
        self.fields["cost"].error_messages["required"] = "仕入れ単価を入力してください"

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        value = value.strip()

        if not value:
            raise forms.ValidationError("商品名を入力してください")

        return value

    def clean_description(self):
        value = self.cleaned_data.get("description", "")
        return value.strip()

    def clean_price(self):
        value = self.cleaned_data.get("price")

        if value is not None and value < 0:
            raise forms.ValidationError("価格は0円以上で入力してください")

        return value

    def clean_cost(self):
        value = self.cleaned_data.get("cost")

        if value is not None and value < 0:
            raise forms.ValidationError("仕入れ単価は0円以上で入力してください")

        return value