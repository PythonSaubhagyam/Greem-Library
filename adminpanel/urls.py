from django.urls import path,include
from adminpanel.View.CompanyView import *
from adminpanel.View.CountryStateCityView import *
from adminpanel.View.CompanyDetailView import *
from adminpanel.View.StudentsView import *
from adminpanel.View.EmployeeView import *
from adminpanel.View.CustomerView import *
from adminpanel.View.ParentChildView import *
from .views import DashboardsView
from adminpanel.View.LeadView import LeadAPI
from adminpanel.View.LeadFollowUpView import TabletLeadFollowUpAPI
from adminpanel.views import LeadCreateUpdateView, LeadFollowUpView, LeadFollowupDetailView
from adminpanel.MobileView.StudentView import MobileStudentsAPIView

from adminpanel.MobileView.ParentsView import *
from adminpanel.MobileView.TeachersView import *

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
    path("students/detail/<int:id>/",DashboardsView.as_view(template_name="student_details.html"),name="student-details"),
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
    path("customers/detail/<int:id>/",DashboardsView.as_view(template_name="customer_detail.html"),name='customers-view'),
    path("customers-api/", CustomerViewAPI.as_view(),name='customers-api'),
    path("customers-api/<int:pk>/", CustomerViewAPI.as_view(),name='customers-detail'),
    path("customers/summary/<int:id>/", CustomerSummaryAPIView.as_view(), name="customer-summary"),
    path("devices/", DashboardsView.as_view(template_name="Devices_list.html"),name='devices'),
    path("devices/add/", DashboardsView.as_view(template_name="customer_device_add_update.html"),name='devices-add-update'),
    path("devices/edit/<int:id>/", DashboardsView.as_view(template_name="customer_device_add_update.html"),name='devices-add-update'),
    path("customer-devices/", CustomerDeviceAPI.as_view(),name='customer-devices'),
    path("customer-devices/<int:pk>/", CustomerDeviceAPI.as_view(),name='customer-devices'),
    path("students-import/", StudentImportAPI.as_view(),name='student-import'),

    path("students/pdfs/<int:pk>/",pdfLibraryAPI.as_view(),name="students-pdfs"),
    path("students/pdfs-groups/",pdfGroupAPI.as_view(),name="students-pdfs-groups"),
    path("students/pdfs-groups/<int:pk>/",pdfGroupAPI.as_view(),name="students-pdfs-groups"),
    path("students/student-groups/",StudentGroupAPI.as_view(),name="students-groups"),
    path("students/student-groups/<int:pk>/",StudentGroupAPI.as_view(),name="students-groups-detail"),
    path("students/tests/<int:pk>/",StudentsTestResultView.as_view(),name="students-tests"),
    path("students/summary/<int:student_id>/",StudentSummaryAPIView.as_view(),name="student-summary"),

    path("parent-child/", ParentChildListAPI.as_view(), name="parent-child-list"),

    path('lead/', LeadAPI.as_view(), name='lead-list-create'),
    path('lead/<int:pk>/', LeadAPI.as_view(), name='lead-detail'),
    path('lead-management/', DashboardsView.as_view(template_name="leads_details.html"), name='lead-management'),
    path('leads/add/', LeadCreateUpdateView.as_view(template_name="lead_add.html"), name='lead-add'),
    path('leads/edit/<int:pk>/', LeadCreateUpdateView.as_view(template_name="lead_add.html"), name='lead-edit'),

    path("leadfollowup/", TabletLeadFollowUpAPI.as_view(), name="leadfollowup-list-create"),
    path("leadfollowup/<int:pk>/", TabletLeadFollowUpAPI.as_view(), name="leadfollowup-detail"),
    path("lead-followups/", LeadFollowUpView.as_view(template_name="lead_followup_details.html"), name="lead-followup-list"),
    path("lead-followups/add/", LeadFollowUpView.as_view(template_name="lead_followup_add.html"), name="lead-followup-add"),
    path("lead-followups/edit/<int:pk>/", LeadFollowUpView.as_view(template_name="lead_followup_add.html"),name="lead-followup-edit"),
    path("lead-followups/lead/<int:lead_id>/", LeadFollowupDetailView.as_view(), name="lead-followup-by-lead"),


    path('mobile-student/', MobileStudentsAPIView.as_view(), name='mobile-student-api'),

    path("analytics/learning-behaviour/<int:pk>/",LearningBehaviourAPI.as_view(),name="learning-behaviour"),
    path("analytics/risk/<int:pk>/", RiskDetectionAPI.as_view(),name='risk-behavioiur'),
    path("analytics/growth-report/<int:pk>/", GrowthEffortAPI.as_view(),name='growth-effort'),
    path("analytics/performance-trend/<int:pk>/", PerformanceTrendAPI.as_view(),name='performance-trend'),
    path("analytics/study-calendar/<int:student_id>/", StudyCalendarAPI.as_view(), name='study-calendar'),
    path("analytics/parent-insights/<int:pk>/", ParentAIInsightsAPI.as_view(), name='parent-insights'),

    # Teachers APIs
    path("teachers/dashboard/<int:teacher_id>/", TeacherDashboardAPI.as_view(), name='teacher-dashboard'),
    path("teachers/class-selection/<int:teacher_id>/", ClassSelectionAPI.as_view(), name='teacher-class-selection'),
    path("teachers/enhanced-overview/<int:teacher_id>/", EnhancedClassOverviewAPI.as_view(), name='teacher-enhanced-overview'),
    path("teachers/student-detail/<int:student_id>/", SubjectFilteredStudentDetailAPI.as_view(), name='teacher-student-detail'),
    path("teachers/groups/<int:teacher_id>/", StudentGroupAPI.as_view(), name='teacher-student-groups'),
    path("teachers/group-analytics/<int:group_id>/", GroupAnalyticsAPI.as_view(), name='teacher-group-analytics'),
    path("teachers/student-comparison/", StudentComparisonAPI.as_view(), name='teacher-student-comparison'),
    path("teachers/advanced-filter/<int:teacher_id>/", AdvancedFilterAPI.as_view(), name='teacher-advanced-filter'),
    path("teachers/cross-subject-overview/<int:teacher_id>/", CrossSubjectOverviewAPI.as_view(), name='teacher-cross-subject-overview'),
    path("teachers/class-overview/<int:teacher_id>/", ClassOverviewAPI.as_view(),name='teacher-class-overview'),
    path("teachers/create-test/", TestCreationAPI.as_view(),name='teacher-create-test'),
    path("teachers/class-analytics/<int:teacher_id>/", ClassPerformanceAnalyticsAPI.as_view(),name='teacher-class-analytics'),
    path('teachers/<int:teacher_id>/alerts/', HomeAlertsAPI.as_view(), name='home-alerts'),

    # ============================================================================
    # NEW APIs - Phase 2 Parents & Teachers
    # ============================================================================
    
    # Parent APIs - New
    path("analytics/academic-health/<int:pk>/", AcademicHealthScoreAPI.as_view(), name='academic-health-score'),
    path("analytics/family-dashboard/", FamilyDashboardAPI.as_view(), name='family-dashboard'),
    path("analytics/goals/", GoalSettingAPI.as_view(), name='goal-setting'),
    path("analytics/goals/<int:student_id>/", GoalSettingAPI.as_view(), name='goal-setting-student'),
    path("analytics/concept-confidence/<int:pk>/", ConceptConfidenceAPI.as_view(), name='concept-confidence'),
    path("analytics/exam-readiness/<int:pk>/", ExamReadinessAPI.as_view(), name='exam-readiness'),
    path("analytics/parent-teacher-sync/<int:pk>/", ParentTeacherSyncAPI.as_view(), name='parent-teacher-sync'),

    # Teacher APIs - New (Batch Management)
    path("teachers/batches/", BatchManagementAPI.as_view(), name='teacher-batches'),
    path("teachers/batches/<int:teacher_id>/", BatchManagementAPI.as_view(), name='teacher-batches-list'),
    path("teachers/batch-analytics/<int:batch_id>/", BatchAnalyticsAPI.as_view(), name='teacher-batch-analytics'),
    
    # Teacher APIs - New (Homework)
    path("teachers/homework/", HomeworkAPI.as_view(), name='teacher-homework'),
    path("teachers/homework/<int:teacher_id>/", HomeworkAPI.as_view(), name='teacher-homework-list'),
    path("teachers/homework-submissions/<int:homework_id>/", HomeworkSubmissionsAPI.as_view(), name='teacher-homework-submissions'),
    
    # Teacher APIs - New (Remarks)
    path("teachers/student-remark/", TeacherRemarkAPI.as_view(), name='teacher-student-remark'),
    path("teachers/student-remarks/<int:student_id>/", TeacherRemarkAPI.as_view(), name='teacher-student-remarks-list'),

    path('teachers/test-submissions/<int:teacher_id>/', TestSubmissionsAPI.as_view(),name="teacher-test-submissions"),
    path("teachers/class-comparison/<int:user_id>/", ClassComparisonAPI.as_view(), name='teacher-class-comparison'),
    path("teachers/live-monitoring/<int:teacher_id>/",LiveMonitoringAPI.as_view(),name="tearcher-live-monitoring"),
    path("teachers/reports/<int:teacher_id>/",ReportsAPI.as_view(),name="teachers-reports"),
    path("teachers/settings/<int:teacher_id>/",TeacherSettingsAPI.as_view(),name='teacher-settings'),

    # Parent APIs - New 
    path("analytics/learning-habit-score/<int:pk>/",LearningHabitScoreAPI.as_view(),name="learning-habit-score"),
    path("analytics/revision-tracker/<int:pk>/",RevisionFrequencyTrackerAPI.as_view(),name="revision-tracker"),
    path("analytics/homework-quality/<int:pk>/",HomeworkQualityAPI.as_view(),name="homework-quality"),
    path("analytics/drop-alert/<int:pk>/",SuddenDropAlertAPI.as_view(),name="drop-alert"),
    path("analytics/forgetting-curve/<int:pk>/",ForgettingCurveAlertAPI.as_view(),name="forgetting-curve"),
    path("analytics/mistake-patterns/<int:pk>/",MistakePatternAnalysisAPI.as_view(),name="mistake-patterns"),
    path("analytics/micro-progress/<int:pk>/",MicroProgressAlertsAPI.as_view(),name="Micro-progress"),
    
]