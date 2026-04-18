from django import forms
from .models import Product, Category, Manufacturer


class ProductForm(forms.ModelForm):
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
        fields = ["name", "category", "manufacturer", "price", "cost", "description", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "cost": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        value = self.cleaned_data.get("name", "")
        value = value.strip()

        if not value:
            raise forms.ValidationError("商品名を入力してください")

        return value

    def clean_description(self):
        value = self.cleaned_data.get("description", "")
        return value.strip()