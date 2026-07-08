# adminpanel --->url

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
from adminpanel.View.school_view import *
# from adminpanel.views import CustomerDashboardView , CoordinatorDashboardView

from adminpanel.MobileView.ParentsView import *
from adminpanel.MobileView.TeachersView import *

from adminpanel.View.PrincipalFlowView import *
from adminpanel.View.HomeworkView import *
from adminpanel.View.ClassView import ClassAPIView
from adminpanel.View.TestsView import TestsAPI, StudentTestAttemptAPI, SubjectsAPI, TestDetailView
from adminpanel.View.AnalyticsAPI import (
    TeachersAnalyticsAPI, CoordinatorsAnalyticsAPI, SubjectsAnalyticsAPI,
    TestsAnalyticsAPI, HomeworkAnalyticsAPI
)
from adminpanel.Schoolwisestudentview import SchoolStudentsAPIView
from adminpanel.View.SubjectView import SubjectAPI, SubjectView
from rest_framework.views import APIView as _APIView
from rest_framework.response import Response as _Response
from django.urls import path
from adminpanel.View import coordinator_views as cv
from adminpanel.views import *
from adminpanel.MobileView.StudentView import *

class SidebarPermissionsAPI(_APIView):
    def get(self, request):
        return _Response([])

app_name = "adminpanel"
urlpatterns = [
    # Principal Flow APIs
    path('principal-flow/', PrincipalFlowAPI.as_view(), name='principal-flow'),
    path('principal-flow/coordinator/<int:coordinator_id>/', CoordinatorDetailAPI.as_view(), name='principal-coordinator-detail'),
    path('principal-flow/teacher/<int:teacher_id>/', TeacherDetailAPI.as_view(), name='principal-teacher-detail'),
    path('principal-flow/class/<int:class_id>/', ClassDetailAPI.as_view(), name='principal-class-detail'),

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
 
    #student api
    path("student/upload-pdf/",StudentUploadPDFAPIView.as_view(),name="student-upload-pdf"),
    
    path("students/",DashboardsView.as_view(template_name="Students_list.html"),name="students"),
    path("students/detail/<int:id>/",DashboardsView.as_view(template_name="student_details.html"),name="student-details"),
    path("students-api/",StudentsAPIView.as_view(),name="students-api"),
    path("students-api/<int:id>/",StudentsAPIView.as_view(),name="students-api-id"),
    path("school-students-api/", SchoolStudentsAPIView.as_view(), name='school-students-api'),
    path("school-students-api/<int:id>/", SchoolStudentsAPIView.as_view(), name='school-students-api-id'),
    path("students/add/",DashboardsView.as_view(template_name="students_add_update.html"),name="Students_add_update"),
    path("students/edit/<int:id>/",DashboardsView.as_view(template_name="students_add_update.html"),name="Students_add_update"),
    path("employees/", DashboardsView.as_view(template_name="Employees_list.html"),name='employees_list'),
    path("employees/add/", DashboardsView.as_view(template_name="employees_add_update.html"),name='employees_add_update'),
    path("employees/edit/<int:id>/", DashboardsView.as_view(template_name="employees_add_update.html"),name='employees_add_update'),
    path("employees-api/", EmployeeAPIView.as_view(),name='employees'),
    path("employees-api/<int:pk>/", EmployeeAPIView.as_view(),name='employees-detail'),
    # path("customer/dashboard/", CustomerDashboardView.as_view(), name="customer-dashboard"),
    # path("coordinator/dashboard/", CoordinatorDashboardView.as_view(), name="coordinator-dashboard"),

    path("customers-dash/",DashboardsView.as_view(template_name="Customer_list.html"),name='customers'),
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
    path("teachers/<int:teacher_id>/groups/",StudentGroupAPI.as_view(),name="teacher-groups"),

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
    # Classes API
    path('classes-api/', ClassAPIView.as_view(), name='classes-api'),
    path('classes-api/<int:pk>/', ClassAPIView.as_view(), name='classes-api-detail'),
    # Classes pages
    path('classes/', DashboardsView.as_view(template_name="Classes_list.html"), name='classes-list'),
    path('classes/add/', DashboardsView.as_view(template_name="classes_add_update.html"), name='classes-add'),
    path('classes/edit/<int:id>/', DashboardsView.as_view(template_name="classes_add_update.html"), name='classes-edit'),
    # Homework APIs
    # Homework pages
    path('homework/add/', DashboardsView.as_view(template_name="homework_add.html"), name='homework-add'),

    # Tests pages
    path('tests/', DashboardsView.as_view(template_name="tests_list.html"), name='tests-list'),
    path('tests/add/', DashboardsView.as_view(template_name="tests_add.html"), name='tests-add'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test-detail'),

    path('dashboard/subjects/', SubjectView.as_view(), name='subjects-page'),
    path('subjects-api/', SubjectsAPI.as_view(), name='old-subjects-api'),
    path('api/subjects/', SubjectAPI.as_view(), name='subjects-api'),           # ← આ ઉમેરો
    path('api/subjects/<int:pk>/', SubjectAPI.as_view(), name='subjects-api-detail'),
    path('api/sidebar-permissions/', SidebarPermissionsAPI.as_view(), name='sidebar-permissions'),
        # Analytics Dashboard
    path('analytics/', DashboardsView.as_view(template_name="principal_analytics.html"), name='principal-analytics'),

    # Tests APIs
    path('tests-api/', TestsAPI.as_view(), name='tests-api'),
    path('tests-api/<int:pk>/', TestsAPI.as_view(), name='tests-api-id'),
    path('test-attempts/', StudentTestAttemptAPI.as_view(), name='test-attempts-api'),
    path('test-attempts/<int:pk>/', StudentTestAttemptAPI.as_view(), name='test-attempts-api-id'),
    # path('subjects-api/', SubjectsAPI.as_view(), name='subjects-api'),
    
    path('homework/', HomeworkAPI.as_view(), name='homework-api'),
    path('homework/<int:pk>/', HomeworkAPI.as_view(), name='homework-api-id'),
    path('homework/submissions/', HomeworkSubmissionAPI.as_view(), name='homework-submissions-api'),
    path('homework/submissions/<int:pk>/', HomeworkSubmissionAPI.as_view(), name='homework-submissions-api-id'),
    path('homework/dashboard/', HomeworkDashboardAPI.as_view(), name='homework-dashboard-api'),

    # Analytics APIs
    path('analytics/teachers/', TeachersAnalyticsAPI.as_view(), name='teachers-analytics-api'),
    path('analytics/coordinators/', CoordinatorsAnalyticsAPI.as_view(), name='coordinators-analytics-api'),
    path('analytics/subjects/', SubjectsAnalyticsAPI.as_view(), name='subjects-analytics-api'),
    path('analytics/tests/', TestsAnalyticsAPI.as_view(), name='tests-analytics-api'),
    path('analytics/homework/', HomeworkAnalyticsAPI.as_view(), name='homework-analytics-api'),

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
    # path("teachers/group-analytics/<int:group_id>/", GroupAnalyticsAPI.as_view(), name='teacher-group-analytics'),
    path("teachers/groups/<int:group_id>/analytics/", GroupAnalyticsAPI.as_view(), name='teacher-group-analytics'),
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
    path("teachers/batch/<int:batch_id>/",BatchDetailAPI.as_view(),name="teacher-batch-detail"),
    path("teachers/batch-analytics/<int:batch_id>/", BatchAnalyticsAPI.as_view(), name='teacher-batch-analytics'),
    
    # Teacher APIs - New (Homework)
    path("teachers/homework/", HomeworkAPI.as_view(), name='teacher-homework'),
    path("teachers/homework/<int:teacher_id>/", HomeworkAPI.as_view(), name='teacher-homework-list'),
    path("teachers/homework-submissions/<int:homework_id>/", HomeworkSubmissionsAPI.as_view(), name='teacher-homework-submissions'),
    path("teachers/homework-submissions/grade/<int:submission_id>/",HomeworkSubmissionsAPI.as_view(),name="teacher-homework-submission-grade"),
    
    # Teacher APIs - New (Remarks)
    path("teachers/student-remark/", TeacherRemarkAPI.as_view(), name='teacher-student-remark'),
    path("teachers/student-remarks/<int:student_id>/", TeacherRemarkAPI.as_view(), name='teacher-student-remarks-list'),
    path("teachers/student-remarks/delete/<int:remark_id>/",TeacherRemarkAPI.as_view(),name="teacher-student-remark-delete"),

    path('teachers/test-submissions/<int:teacher_id>/', TestSubmissionsAPI.as_view(),name="teacher-test-submissions"),
    path("teachers/class-comparison/<int:user_id>/", ClassComparisonAPI.as_view(), name='teacher-class-comparison'),
    path("teachers/live-monitoring/<int:teacher_id>/",LiveMonitoringAPI.as_view(),name="tearcher-live-monitoring"),
    path("teachers/reports/<int:teacher_id>/",ReportsAPI.as_view(),name="teachers-reports"),
    path("teachers/settings/<int:teacher_id>/",TeacherSettingsAPI.as_view(),name='teacher-settings'),
  
    path('teachers/homework/create/',CreateHomeworkView.as_view(),name='homework-create'),
    path('teachers/homework/<int:homework_id>/assign-group/',AssignHomeworkToGroupView.as_view(),name='homework-assign-group'),
    path('teachers/groups/<int:group_id>/suggested-tests/',GroupSuggestedTestsView.as_view(),name='group-suggested-tests'),
    path('teachers/notifications/preferences/',NotificationPreferenceView.as_view(),name='notification-preferences'),
    path("teachers/groups/<int:group_id>/homework/",HomeworkAPI.as_view(),name="group-homework-list"),
    
    # new api teacher 
    path('teachers/classrooms/upload-pdf/', TeacherUploadPDFAPI.as_view(), name='teacher-upload-pdf'),
    path('teachers/create-class/', TeacherCreateClassAPI.as_view(), name='teacher-create-class'),
    path("teachers/class-list/",TeacherClassListAPI.as_view(),name="teacher-class-list",),
    path('teachers/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('teacher/students/add/', AddStudentView.as_view(), name='add-student'),
    path('teacher/classes/<int:class_id>/students/', ClassStudentListView.as_view(), name='class-students'),
    path("teacher/scan-qr/",TeacherScanQRAPIView.as_view(),name="teacher-scan-qr"),
    path("device/status/",DeviceStatusAPIView.as_view(),name="device-status"),


    # Parent APIs - New 
    path("analytics/learning-habit-score/<int:pk>/",LearningHabitScoreAPI.as_view(),name="learning-habit-score"),
    path("analytics/revision-tracker/<int:pk>/",RevisionFrequencyTrackerAPI.as_view(),name="revision-tracker"),
    path("analytics/homework-quality/<int:pk>/",HomeworkQualityAPI.as_view(),name="homework-quality"),
    path("analytics/drop-alert/<int:pk>/",SuddenDropAlertAPI.as_view(),name="drop-alert"),
    path("analytics/forgetting-curve/<int:pk>/",ForgettingCurveAlertAPI.as_view(),name="forgetting-curve"),
    path("analytics/mistake-patterns/<int:pk>/",MistakePatternAnalysisAPI.as_view(),name="mistake-patterns"),
    path("analytics/micro-progress/<int:pk>/",MicroProgressAlertsAPI.as_view(),name="Micro-progress"),
    #  budget list and force re-evaluate
    path("analytics/badges/<int:pk>/",AchievementBadgesAPI.as_view(),name="achievement-badges",),
    #    GET → detected style + tailored study tips
    path("analytics/learning-style/<int:pk>/",LearningStyleDetectionAPI.as_view(),name="learning-style",),
    # 3. Reward Suggestion System
    #    GET  → suggested rewards based on current avg score
    path("analytics/rewards/<int:pk>/",RewardSuggestionAPI.as_view(),name="reward-suggestion"),
    #    POST → assign a reward to a student
    path("analytics/rewards/<int:pk>/assign/",RewardAssignAPI.as_view(),name="reward-assign"),
    #    GET  → full reward history for a student
    path("analytics/rewards/<int:pk>/history/",RewardHistoryAPI.as_view(),name="reward-history"),
    # 4. Parent Coaching Tips (Gemini live)
    #    GET → AI-generated 3–4 sentence coaching guidance for parents
    path("analytics/parent-coaching-tips/<int:pk>/",ParentCoachingTipsAPI.as_view(),name="parent-coaching-tips"),
    # 5. Child Potential Indicator
    #    GET → trend direction + AI score projection + potential level label
    path("analytics/child-potential/<int:pk>/",ChildPotentialIndicatorAPI.as_view(),name="child-potential"),
    # 6. Goal Setting System — full CRUD
    #    GET  (with student_id) → all goals for one student
    path("analytics/goals/<int:student_id>/",GoalSettingAPI.as_view(),name="goals-list"),
    #    GET  (no id) → all goals for all children of the logged-in parent
    path("analytics/goals/",GoalSettingAPI.as_view(),name="goals-parent"),
    #    Body: { student_id, goal_type, target_value, subject_id?, deadline? }
    path("analytics/goals/create/",GoalSettingAPI.as_view(),name="goals-create"),
    #    PUT → update an existing goal
    #    Body: { goal_id, target_value?, deadline?, is_achieved? }
    path("analytics/goals/<int:goal_id>/update/",GoalSettingAPI.as_view(),name="goals-update"),
    #    DELETE → delete a goal
    path("analytics/goals/<int:goal_id>/delete/",GoalSettingAPI.as_view(),name="goals-delete"),
    #    GET → single goal detail by goal_id
    path("analytics/goals/detail/<int:goal_id>/",GoalDetailAPI.as_view(),name="goal-detail"),

    # customer(school)
    path("customer/dashboard/school-setup/",SchoolSetupView.as_view(),name='school-setup'),
    path("customer/api/school-setup/",SchoolProfileAPI.as_view(),name='school-profile-api'),
    path('api/onboarding/excel-import/', OnboardingExcelImportAPI.as_view(), name='excel-import-api'),
    # 2. Student Risk & Attention Lists
    path('api/students/risk-categories/', StudentRiskCategoriesAPI.as_view(), name='students-risk'),
    path('api/students/needs-attention/', StudentsImmediateAttentionAPI.as_view(), name='immediate-attention'),
    # 3. Class Performance Comparison
    path('api/classes/comparison-dashboard/', ClassComparisonDashboardAPI.as_view(), name='class-comparison-dashboard'),
    # 4. Teacher Rankings & Accountability
    path('api/teachers/rankings/', TeacherRankingsAPI.as_view(), name='teacher-rankings'),
    # 5. Coordinator Neglect Detection
    path('api/coordinators/neglect-report/', CoordinatorNeglectAPI.as_view(), name='coordinator-neglect'),
    # 6. Chapter Weakness & Heatmap Matrix
    path('api/subjects/chapters-weakness/', ChapterWeaknessAPI.as_view(), name='chapter-weakness'),
    path('api/subjects/chapter-heatmap/', ChapterHeatmapAPI.as_view(), name='chapter-heatmap'),
    # 7. Action Required console
    path('api/action-required/list/', ActionRequiredAPI.as_view(), name='action-required-list'),
    # 8. Automated Parent Meeting PDF Exporter
    path('api/reports/parent-meeting/<int:student_id>/', ParentMeetingPDFReportAPI.as_view(), name='parent-meeting-report'),

]
