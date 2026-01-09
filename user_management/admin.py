from django.contrib import admin
# from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
# Register your models here.



class UserAdmin(BaseUserAdmin):
    model = UserModel
    list_display = ("id","mobile_no","email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "role")
    search_fields = ("email", "first_name", "last_name", "mobile_no")
    ordering = ("-id",)
    filter_horizontal = ("address",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "mobile_no", "address","firm_name","token")}),
        ("Role & Status", {"fields": ("role", "approved_status")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )
    
@admin.register(RoleModel)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id","name","type")
    search_fields = ("name",)


@admin.register(CountryModel)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("country_name", "country_code", "currency", "calling_code")
    search_fields = ("country_name", "country_code")


@admin.register(CountryGroupModel)
class CountryGroupAdmin(admin.ModelAdmin):
    list_display = ("group_name",)
    filter_horizontal = ("countries",)


@admin.register(StatesModel)
class StatesAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name",)
    list_filter = ("country",)


@admin.register(CitiesModel)
class CitiesAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "country", "is_active")
    list_filter = ("is_active", "country", "state")
    search_fields = ("name",)


@admin.register(AddressModel)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id","full_name", "address_tags", "city", "state", "country","pincode", "is_default")
    search_fields = ("full_name", "street", "address", "landmark")
    list_filter = ("is_default", "country", "state", "city")

admin.site.register(UserModel, UserAdmin)


@admin.register(StudentModel)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id","student_id", "parent", "student_name", "email", "student_class",)
    search_fields = ("parent__email", "email", "student_id", "student_class",)
    list_filter = ("email", "student_id",)