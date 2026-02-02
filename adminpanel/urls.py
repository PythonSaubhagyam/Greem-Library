from django.urls import path,include
from adminpanel.View.CompanyView import UserAPIView
from adminpanel.View.CountryStateCityView import *
from adminpanel.View.CompanyDetailView import *
from adminpanel.View.StudentsView import *
from adminpanel.View.EmployeeView import *
from adminpanel.View.CustomerView import *
from .views import DashboardsView

urlpatterns = [
    
    
    path('users-list/', UserAPIView.as_view(), name='companies-list'),
    path('users-list/<int:id>/', UserAPIView.as_view(), name='companies-list'),
    path("users/",DashboardsView.as_view(template_name="companies_list.html"),name="companies"),
    path('users/add/', DashboardsView.as_view(template_name="add_company.html"),name="company-add"),
    path('users/edit/<int:id>/', DashboardsView.as_view(template_name="add_company.html"),name="company-edit"),
    path("users/detail/<int:pk>/",DashboardsView.as_view(template_name="company_detail.html"),name="company-detail",),
    # path("company-details/",CompanyDetailAPI.as_view(),name="company-details",),
    # path("broadcast-details/",BroadcastDetailsView.as_view(),name="broadcast-details",),
    path("company-details-table/", DashboardsView.as_view(template_name="company_details_table.html"), name="company-details-table"),
    # path("broadcast-list/",BroadcastListView.as_view(),name='broadcast-list'),
    # path("contacts-list/",ContactListView.as_view(),name='contacts-list'),
    # path("users-list/",UserListView.as_view(),name='users-list'),
    # path("active-contacts-list/",ActiveContactList.as_view(),name='active-contacts-list'),
    # path("orders-list/",OrderListView.as_view(),name='orders-list'),
    # path("flows-list/",FlowListView.as_view(),name='flows-list'),
    path('countries/',CountriesAPI.as_view(),name='countries'),
    path('countries/<int:id>/',CountriesAPI.as_view(),name='countries'),
    path('states/',StatesAPI.as_view(),name='states'),
    path('states/<int:id>/',StatesAPI.as_view(),name='states'),
    path('cities/',CitiesAPI.as_view(),name='cities'),
    path('cities/<int:id>/',CitiesAPI.as_view(),name='cities'),

    path("students/",DashboardsView.as_view(template_name="Students_list.html"),name="students"),
    path("students-api/",StudentsAPIView.as_view(),name="students-api"),
    path("students-api/<int:id>/",StudentsAPIView.as_view(),name="students-api-id"),
    path("students/add/",DashboardsView.as_view(template_name="students_add_update.html"),name="Students_add_update"),
    path("students/edit/<int:id>/",DashboardsView.as_view(template_name="students_add_update.html"),name="Students_add_update"),
    path("employees/", DashboardsView.as_view(template_name="Employees_list.html"),name='employees_list'),
    path("employees/add/", DashboardsView.as_view(template_name="employees_add_update.html"),name='employees_add_update'),
    path("employees/edit/<int:id>/", DashboardsView.as_view(template_name="employees_add_update.html"),name='employees_add_update'),
    path("employees-api/", EmployeeAPIView.as_view(),name='employees'),
    path("employees-api/<int:pk>/", EmployeeAPIView.as_view(),name='employees-detail'),

    path("customers/",DashboardsView.as_view(template_name="Customer_list.html"),name='customers'),
    path("customers/add/",DashboardsView.as_view(template_name="customer_add_update.html"),name='customers-add-update'),
    path("customers/edit/<int:id>/",DashboardsView.as_view(template_name="customer_add_update.html"),name='customers-add-update'),
    path("customers-api/", CustomerViewAPI.as_view(),name='customers-api'),
    path("customers-api/<int:pk>/", CustomerViewAPI.as_view(),name='customers-detail'),
    path("devices/", DashboardsView.as_view(template_name="Devices_list.html"),name='devices'),
    path("devices/add/", DashboardsView.as_view(template_name="customer_device_add_update.html"),name='devices-add-update'),
    path("devices/edit/<int:id>/", DashboardsView.as_view(template_name="customer_device_add_update.html"),name='devices-add-update'),
    path("customer-devices/", CustomerDeviceAPI.as_view(),name='customer-devices'),
    path("customer-devices/<int:pk>/", CustomerDeviceAPI.as_view(),name='customer-devices'),
]
