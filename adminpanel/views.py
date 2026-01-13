from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import FileResponse, Http404
from django.conf import settings
import os
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import *
# from account.models import FacebookMetadata
from django.conf import settings

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to dashboards/urls.py file for more pages.
"""


class DashboardsView(LoginRequiredMixin, TemplateView):

    def dispatch(self, request, *args, **kwargs):
        view_to_module_map = {
            "companies": "Companies"
        }

        view_name = request.path.split('/')[1]
        module_name = view_to_module_map.get(view_name)
        user = request.user
        user_role = getattr(user, 'role', None)

        if user_role and user_role.name.lower() == 'admin':
            return super().dispatch(request, *args, **kwargs)
        
        if not user_role:
            return super().dispatch(request, *args, **kwargs)

        # try:
        #     module = Module.objects.get(name=module_name)
        # except Module.DoesNotExist:
        #     print(f"Module '{module_name}' does not exist.")
        #     messages.warning(request, "Module configuration missing.")
        #     return redirect('index')

        # # First check permission by role
        # permission = UserModulePermission.objects.filter(
        #     role=user_role,
        #     module=module
        # ).first()

        # if not permission or not permission.can_read:
        #     messages.warning(request, "You are not authorized to access that page.")
        #     return redirect('index')

        return super().dispatch(request, *args, **kwargs)


    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        template = self.template_name
        import re
        match = re.search(r'/companies/detail/(\d+)/', self.request.path)
        company_id =  self.request.GET.get('company')
        detail_name = self.request.GET.get("type")

        # context['admin_company_id'] = FacebookMetadata.objects.filter(user__email="info@saubhagyam.com").first().id if FacebookMetadata.objects.filter(user__email="info@saubhagyam.com").exists() else None
        context['slug'] = kwargs.get('slug')
        context['sub_slug'] = kwargs.get('sub_slug')
        context['inquiry_id'] = kwargs.get('id')
        context['company_id'] = kwargs.get('company')
        context['detail_name'] = detail_name

        LABEL_MAP = {
            "parent": "Parents Management",
            "teacher": "Teachers Management"
        }

        company_label = LABEL_MAP.get(detail_name, "User Management")

        add_edit_label = ""

        if "add" in self.request.path.lower() and detail_name == "parent":
            add_edit_label = "Add Parent"
        elif "add" in self.request.path.lower() and detail_name == "teacher":
            add_edit_label = "Add Teacher"
        elif "edit" in self.request.path.lower() and detail_name == "parent":
            add_edit_label = "Edit Parent"
        elif "edit" in self.request.path.lower() and detail_name == "teacher":
            add_edit_label = "Edit Teacher"
        elif "/students/add/" in self.request.path.lower():
            add_edit_label = "Add Student"
        elif "/students/edit/" in self.request.path.lower():
            add_edit_label = "Edit Student"


        
        # context['ADMIN_IDS'] = settings.ADMIN_IDS

        context['request'] =  self.request

        # Common breadcrumb base
        breadcrumbs = [{"label": "Home", "url": reverse("index")}]  
        if template in ["admin_properties_list.html", "admin_properties_add_update.html","admin_premium_properties_list.html", "admin_imp_properties_list.html", "admin_properties_dashboard.html"]:
            breadcrumbs = [{"label": "Home", "url": reverse("admin-dashboard")}]

        def section(label, url=None):
            if url:
                breadcrumbs.append({"label": label, "url": url})
            else:
                breadcrumbs.append({"label": label})

        # Map templates to breadcrumbs
        route_map = {
            "companies_list.html": (company_label, None),
            "company_detail.html": (company_label, reverse('companies'), "Company Detail"),
            # "company_detail_table.html": ("Companies", reverse('companies'), reverse('company-detail', args=[company_id]),"In-Detail"),
            "add_company.html": (company_label, reverse('companies'), add_edit_label),
            "Students_list.html": ("Students Management", None),
            "students_add_update.html": ("Students Management", reverse('students'), add_edit_label),
            # "property_add.html": ("Properties", reverse("properties"), "Add Property"),
            # "property_edit.html": ("Properties", reverse("properties"), "Edit Property"),

            # "near_by_places_list.html": ("Nearby Places", None),
            # "near_by_places_add.html": ("Nearby Places", reverse("near-by-places"), "Add Nearby Place"),
            # "near_by_places_edit.html": ("Nearby Places", reverse("near-by-places"), "Edit Nearby Place"),

            # "Projects_list.html": ("Projects", None),
            # "Projects_add.html": ("Projects", reverse("get-projects"), "Add Project"),
            # "Projects_edit.html": ("Projects", reverse("get-projects"), "Edit Project"),

            # "city_list.html": ("Cities", None),
            # "city_add.html": ("Cities", reverse("cities"), "Add City"),
            # "city_edit.html": ("Cities", reverse("cities"), "Edit City"),

            # "states_list.html": ("States", None),
            # "state_add.html": ("States", reverse("states"), "Add State"),
            # "state_edit.html": ("States", reverse("states"), "Edit State"),

            # "property_types_list.html": ("Property Types", None),
            # "property_type_add.html": ("Property Types", reverse("property_type"), "Add Property Type"),
            # "property_type_edit.html": ("Property Types", reverse("property_type"), "Edit Property Type"),

            # "Amenities_list.html": ("Amenities", None),
            # "Amenities_add.html": ("Amenities", reverse("get-amenities"), "Add Amenity"),
            # "Amenities_edit.html": ("Amenities", reverse("get-amenities"), "Edit Amenity"),

            # "Developers_list.html": ("Developers", None),
            # "Developers_add.html": ("Developers", reverse("get-developers"), "Add Developer"),
            # "Developers_edit.html": ("Developers", reverse("get-developers"), "Edit Developer"),

            # "Inquiry_headers_list.html": ("Inquiry Headers", None),
            # "Promotional_images_list.html": ("Promotional Images", None),

            # "Locations_list.html": ("Locations", None),
            # "Locations_add.html": ("Locations", reverse("get-locations"), "Add Location"),
            # "Locations_edit.html": ("Locations", reverse("get-locations"), "Edit Location"),

            # "inquiries_list.html": ("Inquiries", None),
            # "Inquiry_details.html": ("Inquiries", reverse("inquiries"), "Inquiry Details"),
            # "Inquiry_details_by_status.html": ("Inquiries", 
            #                                    reverse("inquiries"),                
            #                                    "Inquiry Details",
            #                                    reverse("inquiry-group-detail", kwargs={"slug": self.kwargs.get("slug")}),
            #                                    "Inquiry Details by Status"),
            # "Inquiry_edit.html": (
            #     "Inquiries",
            #     reverse("inquiries"),
            #     "Inquiry Details",
            #     reverse("inquiry-group-detail", kwargs={"slug": self.kwargs.get("slug")}),
            #     "Inquiry Details by Status",
            #     reverse("inquiry-group-detail-by-status", kwargs={"slug": self.kwargs.get("slug"), "sub_slug": self.kwargs.get("sub_slug")}),                
            #     "Edit Inquiry"
            # ),
        
            # "Inquiry_follow_up_list.html": (
            #     "Inquiries",
            #     "DYNAMIC_GROUP_STATUS",
            #     "Inquiry Detail",
            #     reverse("inquiry-group-detail", kwargs={"slug": self.kwargs.get("slug")}),
            #     "Inquiry Details by Status",
            #     reverse("inquiry-group-detail-by-status", kwargs={"slug": self.kwargs.get("slug"), "sub_slug": self.kwargs.get("sub_slug")}),                                
            #     "Follow Up"
            # ),
        
            # "Inquiry_follow_up_add.html": (
            #     "Inquiries",
            #     "DYNAMIC_GROUP_STATUS",
            #     "Inquiry Detail",
            #     reverse("inquiry-group-detail", kwargs={"slug": self.kwargs.get("slug")}),
            #     "Inquiry Details by Status",
            #     reverse("inquiry-group-detail-by-status", kwargs={"slug": self.kwargs.get("slug"), "sub_slug": self.kwargs.get("sub_slug")}),                                
            #     "Add Follow Up"
            # ),
        
            # "Inquiry_follow_up_edit.html": (
            #      "Inquiries",
            #     "DYNAMIC_GROUP_STATUS",
            #     "Inquiry Detail",
            #     reverse("inquiry-group-detail", kwargs={"slug": self.kwargs.get("slug")}),
            #     "Inquiry Details by Status",
            #     reverse("inquiry-group-detail-by-status", kwargs={"slug": self.kwargs.get("slug"), "sub_slug": self.kwargs.get("sub_slug")}),
            #     "Edit Follow Up"
            # ),

            # "user_list.html": ("Users", None),
            # "user_add.html": ("Users", reverse("user-list"), "Add User"),
            # "user_edit.html": ("Users", reverse("user-list"), "Edit User"),

            # "FollowupNotification.html": ("Follow Up Notifications", None),
            
            # "appointments_list.html": ("Appointments", reverse("appointments")),

            # "admin_properties_list.html": ("All Properties", None),
            # "admin_properties_add_update.html": ("All Properties", reverse("admin-properties"), "Add - Edit Property"),
            # "admin_premium_properties_list.html": ("Premium Properties", None),
            # "admin_imp_properties_list.html": ("Important Properties", None),
            # "admin_properties_dashboard.html": ("Dashboard Details", None),

            # "property_filter.html": ("Advance Search", None),
        }

        if company_id:
            route_map["company_details_table.html"] = (
                "Companies",
                reverse('companies'), "Company Detail",
                reverse('company-detail', args=[company_id]),
                detail_name.title()
            )

        slug = self.kwargs.get("slug")
        sub_slug = self.kwargs.get("sub_slug")
        pk = self.kwargs.get("pk")
        followup_id = self.kwargs.get("id")
        company_id = self.kwargs.get('company')

        route = route_map.get(template)
        if route:
            def resolve_url(item):
                if item == "DYNAMIC_GROUP_STATUS" and slug and sub_slug:
                    return reverse("inquiry-group-detail-by-status", kwargs={"slug": slug, "sub_slug": sub_slug})
                elif item == "DYNAMIC_INQUIRY" and slug and sub_slug and followup_id:
                    return reverse("inquiry-follow-up-list", kwargs={"slug": slug, "sub_slug": sub_slug, "id": followup_id})
                elif item == "FOLLOWUP_URL_ADD" and slug and sub_slug and followup_id:
                    return reverse("inquiry-follow-up-add", kwargs={"slug": slug, "sub_slug": sub_slug, "id": followup_id})
                elif item == "FOLLOWUP_URL_EDIT" and slug and sub_slug and followup_id and pk:
                    return reverse("inquiry-follow-up-edit", kwargs={"slug": slug, "sub_slug": sub_slug, "id": followup_id, "pk": pk})
                return item if isinstance(item, str) else None
            i = 0
            while i < len(route):
                label = route[i]
                url = route[i + 1] if i + 1 < len(route) else None
                section(label, resolve_url(url))
                i += 2
        
            context["section_title"] = route[0]
            if len(route) >= 5:
                context["subsection_title"] = route[-1]
        
        context["slug"] = slug
        context["breadcrumbs"] = breadcrumbs
        # context['ADMIN_IDS'] = settings.ADMIN_IDS
        return context


def cors_media_serve(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    response = FileResponse(open(file_path, 'rb'))
    # response["Access-Control-Allow-Origin"] = "https://srproperty.co.in"
    response["Access-Control-Allow-Credentials"] = "true"
    return response


def csrf_failure(request, reason=""):
    return render(request, "403_csrf.html", status=403)