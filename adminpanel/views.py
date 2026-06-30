from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper
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
from user_management.models import *
from django.views import View   
from django.shortcuts import get_object_or_404, render
from user_management.models import TabletLeadModel, UserModel, TabletLeadFollowUpModel
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render


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


    def get_template_names(self):
        user = self.request.user
        user_role = getattr(user.role, 'type', None) if user.role else None
        # If this view is explicitly serving the customer dashboard template
        # and the user is a Customer, return the adminpanel namespaced dashboard.
        # Do NOT override other templates (eg. add/edit pages) for Customer users.
        if user_role == 'Customer' and (self.template_name is None or self.template_name == 'customer_dashboard.html'):
            return ["adminpanel/customer_dashboard.html"]
        return [self.template_name]

    # Predefined function
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        #  Define template FIRST
        template = self.template_name
        
        import re
        match = re.search(r'/companies/detail/(\d+)/', self.request.path)
        company_id = self.request.GET.get('company')
        detail_name = self.request.GET.get("type")

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

        if "/leads/add/" in self.request.path.lower():
            add_edit_label = "Add Lead"
        elif "/leads/edit/" in self.request.path.lower():
            add_edit_label = "Edit Lead"

        student_name = ''
        customer_name = ''

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
        elif "/employees/add/" in self.request.path.lower():
            add_edit_label = "Add Employee"
        elif "/employees/edit/" in self.request.path.lower():
            add_edit_label = "Edit Employee"
        elif "/customers/add/" in self.request.path.lower():
            add_edit_label = "Add Customer"
        elif "/customers/edit/" in self.request.path.lower():
            add_edit_label = "Edit Customer"
        elif "/devices/add/" in self.request.path.lower():
            add_edit_label = "Add Device"
        elif "/devices/edit/" in self.request.path.lower():
            add_edit_label = "Edit Device"

        if "administrator/students/detail/" in self.request.path.lower():
            student_id = self.kwargs.get("id")
            student_name = StudentModel.objects.filter(id=student_id).first().student_name
        elif "administrator/customers/detail/" in self.request.path.lower():
            user_id = self.kwargs.get("id")
            customer = UserModel.objects.filter(id=user_id).first()
            customer_name = customer.first_name + " " + customer.last_name if customer else ""

        context['request'] = self.request

        # ✅ Role-based breadcrumb — defined ONCE here, no overwrite below
        user = self.request.user
        user_role = getattr(getattr(user, 'role', None), 'type', None)

        if user_role == 'Coordinator':
            breadcrumbs = [{"label": "Home", "url": reverse("coordinator-dashboard")}]
        elif template in ["admin_properties_list.html", "admin_properties_add_update.html",
                        "admin_premium_properties_list.html", "admin_imp_properties_list.html",
                        "admin_properties_dashboard.html"]:
            breadcrumbs = [{"label": "Home", "url": reverse("admin-dashboard")}]
        else:
            breadcrumbs = [{"label": "Home", "url": reverse("index")}]

        def section(label, url=None):
            if url:
                breadcrumbs.append({"label": label, "url": url})
            else:
                breadcrumbs.append({"label": label})

        if template == "school_teacher_add.html":
            if "/teachers/add/" in self.request.path.lower():
                add_edit_label = "Add Teacher"
            elif "/teachers/edit/" in self.request.path.lower():
                add_edit_label = "Edit Teacher"
        # Map templates to breadcrumbs
        route_map = {
            "companies_list.html": (company_label, None),
            "company_detail.html": (company_label, reverse('companies'), "Company Detail"),
            # "company_detail_table.html": ("Companies", reverse('companies'), reverse('company-detail', args=[company_id]),"In-Detail"),
            "add_company.html": (company_label, reverse('companies'), add_edit_label),
            "Students_list.html": ("Students Management", None),
            "students_add_update.html": ("Students Management", reverse('students'), add_edit_label),
            "student_details.html":("Students Management", reverse('students'),student_name),
            "Employees_list.html": ("Employees Management", None),
            "employees_add_update.html": ("Employees Management", reverse('employees'), add_edit_label),
            "Customer_list.html": ("Customers Management", None),
            "customer_add_update.html": ("Customers Management", reverse('customers'), add_edit_label),
            "Devices_list.html": ("Devices Management", None),
            "customer_device_add_update.html": ("Devices Management", reverse('devices'), add_edit_label),
            "customer_detail.html": ("Customers Management", reverse('customers'), customer_name),
            "school_setup.html":("School Setup",None),
            "class_comparison.html":("Class Comparison",None),
            "onboarding_upload.html":("Onboarding",None),
            "action_required.html":("Actions",None),
            "alerts.html":("Alert",None),
            "Classes_list.html":("Class",None),
            "homework_reports.html":("Homework",None),
            "homework_add.html":("Homework", reverse('homework-add')),
            "tests_list.html":("Test",None),
            "school_teachers_list.html":("Teacher",None),
            "school_teacher_add.html": ("Teacher",reverse("customer-teachers"),add_edit_label),

            # "leads_details.html": ("Lead Management", None),
            # "lead_add.html": ("Lead Management", reverse('lead-management'), "Add Tablet Lead"),
            # "lead_detail.html": ("Lead Management", reverse('lead-management'), "Lead Detail"),
            "leads_details.html": ("Lead Management", None),
            "lead_add.html": ("Lead Management", reverse("lead-management"), add_edit_label),

            "lead_followup_details.html": ("Lead Management", reverse("lead-management"), "Follow-Ups"),
            "lead_followup_add.html": ("Lead Management", reverse("lead-management"), "Add Follow-Up" ),
            "subjects_list.html": ("Subjects", None),
            "study_time.html": ("Study Time", None),
            "weakness_analysis.html": ("Weakness Analysis", None),
            "reports.html":("Reports",None),
            "device_management.html": ("Device Management", None),
            "settings.html": ("Settings", None),
            "coordinators_list.html": ("Coordinators", None),

            # "coordinator/coordinator_dashboard.html": ("", None),
            "coordinator/coordinator_classes.html": ("Classes Management", None),
            "coordinator/coordinator_class_detail.html": ("Classes Management", reverse('coordinator-classes'), "Class Details"),
            "coordinator/coordinator_teachers.html": ("Teachers Management", None),
            "coordinator/coordinator_teacher_neglect.html": ("Teacher Neglect", None),
            "coordinator/coordinator_students.html": ("Students", None),
            "coordinator/coordinator_subjects.html": ("Subjects", None),
            "coordinator/coordinator_tests.html": ("Tests Management", None),
            "coordinator/coordinator_homework.html": ("Homework Management", None),
            "coordinator/coordinator_study_time.html": ("Study Time", None),
            "coordinator/coordinator_weakness.html": ("Weakness Analysis", None),
            "coordinator/coordinator_actions.html": ("Actions", None),
            "coordinator/coordinator_alerts.html": ("Alerts Management", None),
            "coordinator/coordinator_reports.html": ("Reports Management", None),
            "coordinator/coordinator_devices.html": ("Device Management", None),
            "coordinator/coordinator_escalations.html": ("Escalations", None),
            "coordinator/coordinator_profile.html": ("My Profile", None),
            "coordinator/coordinator_settings.html": ("Settings", None),
            "coordinator/coordinator_student_detail.html": ("Students", reverse('coordinator-students'), "Student Detail"),
            "coordinator/coordinator_teacher_neglect.html": ("Teacher Neglect Detection", None),
        # }

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


@method_decorator(login_required, name='dispatch')
class CustomerDashboardView(DashboardsView):
    template_name = "customer_dashboard.html"

    def get(self, request):
        context = self.get_context_data()
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorDashboardView(DashboardsView):
    template_name = "coordinator/coordinator_dashboard.html"

    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = self.get_context_data()
        context["user"] = request.user
        return render(request, self.template_name, context)


class LeadCreateUpdateView(DashboardsView):
    template_name = "lead_add.html"

    def get(self, request, pk=None):
        context = self.get_context_data()
        context["customer_types"] = ["Student", "School", "College", "Institute", "Individual"]
        context["payment_statuses"] = ["Pending", "Partial", "Paid"]
        context["lead_stages"] = ["New", "Contacted", "Demo Scheduled", "Demo Done", "Negotiation",
                                  "Order Confirmed", "Delivered", "Lost"]
        context["employees"] = EmployeeModel.objects.all()
        context["is_edit"] = False
        context["lead"] = None

        if pk:
            lead = get_object_or_404(TabletLeadModel, pk=pk)
            context["lead"] = lead
            context["is_edit"] = True

        return render(request, self.template_name, context)


    def post(self, request, pk=None):
        data = request.POST
        lead = TabletLeadModel(created_by=request.user)
        if pk and pk != "null":
            lead = get_object_or_404(TabletLeadModel, pk=pk)


        try:
            lead.name = data.get("name")
            lead.mobile = data.get("mobile")
            lead.email = data.get("email") or None
            lead.customer_type = data.get("customer_type")
            lead.school_name = data.get("school_name") or None
            lead.tablet_model = data.get("tablet_model")
            lead.tablet_variant = data.get("tablet_variant")
            lead.quantity = int(data.get("quantity") or 1)
            lead.price_per_unit = float(data.get("price_per_unit") or 0)
            lead.total_price = float(data.get("total_price") or 0)
            lead.stage = data.get("stage")
            lead.payment_status = data.get("payment_status")
            lead.comment = data.get("comment")
            lead.demo_required = data.get("demo_required") == "true"
            lead.demo_done = data.get("demo_done") == "true"
            lead.demo_date = data.get("demo_date") or None
            lead.delivery_date = data.get("delivery_date") or None

            assigned_to = data.get("assigned_to_id")
            lead.assigned_to_id = assigned_to if assigned_to else None

            lead.save()

            return JsonResponse({
                "success": True,
                "message": "Lead updated successfully" if pk else "Lead created successfully"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=400)
    


class LeadFollowUpView(DashboardsView):
    template_name = "lead_followup_add.html"
    list_template = "lead_followup_details.html"

    def get(self, request, pk=None):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        followup = get_object_or_404(TabletLeadFollowUpModel, pk=pk) if pk else None

        context = self.get_context_data()

        context = TemplateLayout.init(self, {
            "is_edit": bool(pk),
            "followup": followup,
            "leads": TabletLeadModel.objects.all(),
            "followup_types": ["call", "visit", "whatsapp", "email"],

        })

        return render(request, self.template_name, context)



    def post(self, request, pk=None):
        followup = None
        if pk:
            followup = get_object_or_404(TabletLeadFollowUpModel, pk=pk)
        else:
            followup = TabletLeadFollowUpModel(followup_by=request.user)

        try:
            followup.tablet_lead_id = request.POST.get("tablet_lead_id")
            followup.followup_type = request.POST.get("followup_type")
            followup.followup_date = parse_datetime(request.POST.get("followup_date"))
            followup.next_followup_date = parse_datetime(request.POST.get("next_followup_date"))
            followup.comment = request.POST.get("comment", "")
            followup.save()

            return JsonResponse({
                "success": True,
                "message": "Follow-up updated successfully" if pk else "Follow-up added successfully",
                "redirect_url": reverse("lead-management") 
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)



class LeadFollowupDetailView(DashboardsView):
    template_name = "lead_followup_details.html"

    def get(self, request, lead_id):

        if not lead_id:
            return JsonResponse(
                {"status": "error", "message": "Invalid lead id"},
                status=400
            )

        try:
            lead = TabletLeadModel.objects.get(id=lead_id)
        except TabletLeadModel.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "status": "not_found",
                    "message": "Lead not found"
                }, status=404)

            return render(request, self.template_name, {
                "lead": None,
                "not_found": True
            })

        followups = TabletLeadFollowUpModel.objects.filter(
            tablet_lead=lead
        ).order_by("-followup_date")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            data = [{
                "id": f.id,
                "tablet_lead": lead.name,
                "followup_type": f.followup_type,
                "followup_date": f.followup_date.strftime("%Y-%m-%d %H:%M") if f.followup_date else "",
                "next_followup_date": f.next_followup_date.strftime("%Y-%m-%d %H:%M") if f.next_followup_date else "",
                "stage_update": getattr(f, "stage_update", ""),
                "comment": f.comment or "",
                "followup_by": (
                    f"{f.followup_by.first_name} {f.followup_by.last_name}".strip()
                    if f.followup_by else ""
                )

            } for f in followups]

            return JsonResponse({
                "status": "ok",
                "data": data
            })

        context = self.get_context_data()
        context["lead"] = lead
        context["lead_id"] = lead.id
        context["has_followups"] = followups.exists()

        return render(request, self.template_name, context)




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


class SchoolSetupView(TemplateView):
    template_name = "school_setup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['layout_path'] = "layout/master.html"
        return context
