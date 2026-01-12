from django.urls import path,include
from adminpanel.View.CompanyView import UserAPIView
from adminpanel.View.CountryStateCityView import *
from adminpanel.View.CompanyDetailView import *
from .views import DashboardsView

urlpatterns = [
    
    
    path('companies-list/', UserAPIView.as_view(), name='companies-list'),
    path('companies-list/<int:id>/', UserAPIView.as_view(), name='companies-list'),
    path("companies/",DashboardsView.as_view(template_name="companies_list.html"),name="companies"),
    path('companies/add/', DashboardsView.as_view(template_name="add_company.html"),name="company-add"),
    path('companies/edit/<int:id>/', DashboardsView.as_view(template_name="add_company.html"),name="company-edit"),
    path("companies/detail/<int:pk>/",DashboardsView.as_view(template_name="company_detail.html"),name="company-detail",),
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
]
