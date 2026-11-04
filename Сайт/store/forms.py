from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import Order, Profile, get_profile_for_user

User = get_user_model()


def _format_price(value):
    return f"{int(value):,}".replace(",", " ")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email manzili",
        widget=forms.EmailInput(
            attrs={"class": "auth-input", "autocomplete": "email"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "auth-input", "autocomplete": "username"}
            ),
        }
        labels = {"username": "Foydalanuvchi nomi"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = (
            "150 belgigacha. Harf, raqam va @/./+/-/_ belgilaridan foydalaning."
        )
        self.fields["password1"].label = "Parol"
        self.fields["password1"].help_text = (
            "Kamida 8 belgi bo‘lsin; shaxsiy ma’lumotlaringizga o‘xshamasin, "
            "keng tarqalgan yoki faqat raqamdan iborat parol bo‘lmasin."
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "auth-input", "autocomplete": "new-password"}
        )
        self.fields["password2"].label = "Parolni takrorlang"
        self.fields["password2"].help_text = "Tasdiqlash uchun parolni yana kiriting."
        self.fields["password2"].widget.attrs.update(
            {"class": "auth-input", "autocomplete": "new-password"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email manzili allaqachon ro‘yxatdan o‘tgan.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
            get_profile_for_user(user)
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email yoki foydalanuvchi nomi",
        widget=forms.TextInput(
            attrs={"class": "auth-input", "autocomplete": "username"}
        ),
    )
    password = forms.CharField(
        label="Parol",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "auth-input", "autocomplete": "current-password"}
        ),
    )

    def clean(self):
        identifier = self.cleaned_data.get("username")
        if identifier and "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user is not None:
                self.cleaned_data["username"] = user.get_username()
        return super().clean()


class ProfileAvatarForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Ism",
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="Familiya",
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "family-name"}),
    )
    phone = forms.CharField(
        label="Telefon raqami",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "tel", "placeholder": "+998 90 123 45 67"}),
    )
    bio = forms.CharField(
        label="Bio",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"class": "auth-input", "rows": 4, "placeholder": "O'zingiz haqida qisqa ma'lumot..."}),
    )

    class Meta:
        model = Profile
        fields = ("avatar",)
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "auth-input"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.first_name
            self.fields["last_name"].initial = self.instance.last_name
            self.fields["phone"].initial = self.instance.phone
            self.fields["bio"].initial = self.instance.bio

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.first_name = self.cleaned_data.get("first_name", "").strip()
        profile.last_name = self.cleaned_data.get("last_name", "").strip()
        profile.phone = self.cleaned_data.get("phone", "").strip()
        profile.bio = self.cleaned_data.get("bio", "").strip()
        if commit:
            profile.save()
        return profile


class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        label="Ism",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="Familiya",
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="Email manzili",
        widget=forms.EmailInput(attrs={"class": "auth-input", "autocomplete": "email"}),
    )
    phone = forms.CharField(
        label="Telefon raqami",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "auth-input", "autocomplete": "tel", "placeholder": "+998 90 123 45 67"}),
    )
    address = forms.CharField(
        label="Yetkazib berish manzili",
        required=False,
        max_length=300,
        widget=forms.Textarea(attrs={"class": "auth-input", "rows": 3, "placeholder": "Shahar, ko'cha, uy raqami"}),
    )
    payment_method = forms.ChoiceField(
        label="To‘lov usuli",
        choices=Order.PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "payment-option-input"}),
    )
    notes = forms.CharField(
        label="Izoh (ixtiyoriy)",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"class": "auth-input", "rows": 2, "placeholder": "Buyurtma haqida qo'shimcha ma'lumot"}),
    )


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        label="Yangi email manzili",
        widget=forms.EmailInput(
            attrs={"class": "auth-input", "autocomplete": "email"}
        ),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if email.casefold() == (self.user.email or "").casefold():
            raise forms.ValidationError("Bu email manzili profilingizda allaqachon ishlatilmoqda.")
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Bu email manzili allaqachon ro‘yxatdan o‘tgan.")
        return email


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Hisobingiz email manzili",
        widget=forms.EmailInput(
            attrs={"class": "auth-input", "autocomplete": "email"}
        ),
    )


class VerificationResendForm(forms.Form):
    email = forms.EmailField(
        label="Ro‘yxatdan o‘tgan email manzili",
        widget=forms.EmailInput(
            attrs={"class": "auth-input", "autocomplete": "email"}
        ),
    )


class PasswordResetCodeForm(forms.Form):
    code = forms.RegexField(
        regex=r"^\d{6}$",
        label="6 xonali email kodi",
        error_messages={"invalid": "Kod 6 ta raqamdan iborat bo‘lishi kerak."},
        widget=forms.TextInput(
            attrs={
                "class": "auth-input auth-input-code",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "maxlength": "6",
                "placeholder": "000000",
            }
        ),
    )
    new_password1 = forms.CharField(
        label="Yangi parol",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "auth-input", "autocomplete": "new-password"}
        ),
    )
    new_password2 = forms.CharField(
        label="Yangi parolni takrorlang",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "auth-input", "autocomplete": "new-password"}
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data["new_password1"]
        validate_password(password, user=self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            self.add_error("new_password2", "Parollar bir xil emas.")
        return cleaned_data


class VerificationCodeForm(forms.Form):
    code = forms.RegexField(
        regex=r"^\d{6}$",
        label="6 xonali tasdiqlash kodi",
        error_messages={"invalid": "Kod 6 ta raqamdan iborat bo‘lishi kerak."},
        widget=forms.TextInput(
            attrs={
                "class": "auth-input auth-input-code",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "maxlength": "6",
                "placeholder": "000000",
            }
        ),
    )


