# coordinator_urls.py — COMPLETE, CLEANED VERSION

from django.urls import path
from adminpanel.View import coordinator_views as cv
from django.http import JsonResponse
from django.views import View


class SidebarPermissionsStub(View):
    def get(self, request):
        return JsonResponse({'permissions': []})


urlpatterns = [

    path('api/sidebar-permissions/', SidebarPermissionsStub.as_view()),

    # ── Page Views ────────────────────────────────────────────────────────────
    path('dashboard/',           cv.CoordinatorDashboardView.as_view(),       name='coordinator-dashboard'),
    path('classes/',             cv.CoordinatorClassListView.as_view(),        name='coordinator-classes'),
    path('classes/<int:pk>/',    cv.CoordinatorClassDetailView.as_view(),      name='coordinator-class-detail'),
    path('teachers/',            cv.CoordinatorTeacherListView.as_view(),      name='coordinator-teachers'),
    path('teacher-neglect/',     cv.CoordinatorTeacherNeglectView.as_view(),   name='coordinator-teacher-neglect'),
    path('students/',            cv.CoordinatorStudentListView.as_view(),      name='coordinator-students'),
    # FIXED: was JSON-only; now renders template
    path('students/<int:pk>/',   cv.CoordinatorStudentDetailView.as_view(),    name='coordinator-student-detail'),
    path('api/students/<int:pk>/', cv.CoordinatorStudentDetailAPI.as_view(),   name='coordinator-student-detail-api'),
    path('subjects/',            cv.CoordinatorSubjectView.as_view(),          name='coordinator-subjects'),
    path('tests/',               cv.CoordinatorTestListView.as_view(),         name='coordinator-tests'),
    path('homework/',            cv.CoordinatorHomeworkView.as_view(),         name='coordinator-homework'),
    path('study-time/',          cv.CoordinatorStudyTimeView.as_view(),        name='coordinator-study-time'),
    path('weakness/',            cv.CoordinatorWeaknessView.as_view(),         name='coordinator-weakness'),
    path('actions/',             cv.CoordinatorActionView.as_view(),           name='coordinator-actions'),
    path('alerts/',              cv.CoordinatorAlertView.as_view(),            name='coordinator-alerts'),
    path('reports/',             cv.CoordinatorReportsView.as_view(),          name='coordinator-reports'),
    path('devices/',             cv.CoordinatorDeviceView.as_view(),           name='coordinator-devices'),
    path('escalations/',         cv.CoordinatorEscalationView.as_view(),       name='coordinator-escalations'),
    path('profile/',             cv.CoordinatorProfileView.as_view(),          name='coordinator-profile'),
    path('settings/',            cv.CoordinatorSettingsView.as_view(),         name='coordinator-settings'),

    # ── Action Update ─────────────────────────────────────────────────────────
    path('actions/<int:pk>/update/', cv.CoordinatorActionUpdateAPI.as_view(),  name='coordinator-action-update'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('dashboard-stats/',     cv.CoordinatorDashboardStatsAPI.as_view(),    name='coordinator-dashboard-stats'),

    # ── Core Data APIs ────────────────────────────────────────────────────────
    path('api/flow/',                    cv.CoordinatorFlowAPI.as_view(),                name='coordinator-flow-api'),
    path('api/weak-students/',           cv.CoordinatorWeakStudentsAPI.as_view(),        name='coordinator-weak-students-api'),
    path('api/teacher-activity/',        cv.CoordinatorTeacherActivityAPI.as_view(),     name='coordinator-teacher-activity-api'),
    path('api/teacher-neglect/',         cv.CoordinatorTeacherNeglectAPI.as_view(),      name='coordinator-teacher-neglect-api'),
    path('api/class-comparison/',        cv.CoordinatorClassComparisonAPI.as_view(),     name='coordinator-class-comparison-api'),
    path('api/homework-stats/',          cv.CoordinatorHomeworkStatsAPI.as_view(),       name='coordinator-homework-stats-api'),
    path('api/device-stats/',            cv.CoordinatorDeviceStatsAPI.as_view(),         name='coordinator-device-stats-api'),
    path('api/study-time/',              cv.CoordinatorStudyTimeAPI.as_view(),           name='coordinator-study-time-api'),
    path('api/profile/',                 cv.CoordinatorProfileAPI.as_view(),             name='coordinator-profile-api'),
    path('api/change-password/',         cv.CoordinatorChangePasswordAPI.as_view(),      name='coordinator-change-password'),

    # ── Student APIs (FIXED: page view + JSON API separated) ──────────────────
    # path('api/students/<int:pk>/',       cv.CoordinatorStudentDetailAPI.as_view(),       name='coordinator-student-detail-api'),
    path('api/students/filter/',         cv.CoordinatorStudentFilterAPI.as_view(),       name='coordinator-student-filter-api'),

    # ── Test APIs ─────────────────────────────────────────────────────────────
    path('api/test-stats/',              cv.CoordinatorTestStatsAPI.as_view(),           name='coordinator-test-stats-api'),
    path('api/test/<int:pk>/',           cv.CoordinatorTestDetailAPI.as_view(),          name='coordinator-test-detail-api'),
    path('api/tests/filter/',            cv.CoordinatorTestFilterAPI.as_view(),          name='coordinator-test-filter-api'),
    path('api/tests/missed/',            cv.CoordinatorTestMissedAPI.as_view(),          name='coordinator-test-missed-api'),

    # ── Homework APIs ─────────────────────────────────────────────────────────
    path('api/homework/',                cv.CoordinatorHomeworkAPI.as_view(),            name='coordinator-homework-api'),
    path('api/homework/<int:pk>/',       cv.CoordinatorHomeworkDetailAPI.as_view(),      name='coordinator-homework-detail-api'),
    path('api/homework-late/',           cv.CoordinatorHomeworkLateAPI.as_view(),        name='coordinator-homework-late-api'),

    # ── Class APIs ────────────────────────────────────────────────────────────
    path('api/classes/<int:pk>/',        cv.CoordinatorClassDetailAPI.as_view(),         name='coordinator-class-detail-api'),

    # ── Subject APIs ──────────────────────────────────────────────────────────
    path('api/subjects/',                cv.CoordinatorSubjectAPI.as_view(),             name='coordinator-subject-api'),
    path('api/subjects/<int:pk>/',       cv.CoordinatorSubjectDetailAPI.as_view(),       name='coordinator-subject-detail-api'),

    # ── Weakness ──────────────────────────────────────────────────────────────
    path('api/weakness/',                cv.CoordinatorWeaknessAPI.as_view(),            name='coordinator-weakness-api'),

    # ── Teacher APIs ──────────────────────────────────────────────────────────
    path('api/teacher-comparison/',      cv.CoordinatorTeacherComparisonAPI.as_view(),   name='coordinator-teacher-comparison-api'),
    path('api/teacher-comment/<int:teacher_id>/',
         cv.CoordinatorTeacherCommentAPI.as_view(),
         name='coordinator-teacher-comment-api'),
    # FIXED: added DELETE endpoint for comment
    path('api/teacher-comment/<int:teacher_id>/<int:comment_id>/',
         cv.CoordinatorTeacherCommentAPI.as_view(),
         name='coordinator-teacher-comment-delete-api'),

    # ── Action APIs ───────────────────────────────────────────────────────────
    path('api/actions/assign/',          cv.CoordinatorActionAssignAPI.as_view(),        name='coordinator-action-assign-api'),

    # ── Alerts ────────────────────────────────────────────────────────────────
    path('api/alerts/',                  cv.CoordinatorAlertsAPI.as_view(),              name='coordinator-alerts-api'),
    path('api/alerts/all/',              cv.CoordinatorAllAlertsAPI.as_view(),           name='coordinator-alerts-all-api'),

    # ── Escalation APIs ───────────────────────────────────────────────────────
    path('api/escalations/',             cv.CoordinatorEscalationAPI.as_view(),          name='coordinator-escalation-api'),
    path('api/escalations/<int:pk>/',    cv.CoordinatorEscalationDetailAPI.as_view(),    name='coordinator-escalation-detail-api'),

    # ── Report APIs ───────────────────────────────────────────────────────────
    path('api/reports/class/',           cv.CoordinatorClassReportAPI.as_view(),         name='coordinator-report-class'),
    path('api/reports/teacher/',         cv.CoordinatorTeacherReportAPI.as_view(),       name='coordinator-report-teacher'),
    path('api/reports/student/',         cv.CoordinatorStudentReportAPI.as_view(),       name='coordinator-report-student'),
    path('api/reports/homework/',        cv.CoordinatorHomeworkReportAPI.as_view(),      name='coordinator-report-homework'),
    path('api/reports/test/',            cv.CoordinatorTestReportAPI.as_view(),          name='coordinator-report-test'),
    path('api/reports/device/',          cv.CoordinatorDeviceReportAPI.as_view(),        name='coordinator-report-device'),
    path('api/reports/weak-students/',   cv.CoordinatorWeakStudentReportAPI.as_view(),   name='coordinator-report-weak'),
    path('api/reports/subject/',         cv.CoordinatorSubjectReportAPI.as_view(),       name='coordinator-report-subject'),
    path('api/reports/actions/',         cv.CoordinatorActionReportAPI.as_view(),        name='coordinator-report-actions'),

    # ── NEW: Global Search ────────────────────────────────────────────────────
    path('api/search/',                  cv.CoordinatorGlobalSearchAPI.as_view(),        name='coordinator-search-api'),

    # ── Excel Exports ─────────────────────────────────────────────────────────
    path('export/classes/',              cv.ExportClassExcelAPI.as_view(),               name='coordinator-export-class-excel'),
    path('export/teachers/',             cv.ExportTeacherExcelAPI.as_view(),             name='coordinator-export-teacher-excel'),
    path('export/students/',             cv.ExportStudentExcelAPI.as_view(),             name='coordinator-export-student-excel'),
    path('export/subjects/',             cv.ExportSubjectExcelAPI.as_view(),             name='coordinator-export-subject-excel'),
    path('export/actions/',              cv.ExportActionExcelAPI.as_view(),              name='coordinator-export-action-excel'),

    # ── PDF Exports ───────────────────────────────────────────────────────────
    path('export/pdf/classes/',          cv.ExportClassPDFAPI.as_view(),                name='coordinator-export-class-pdf'),
    path('export/pdf/teachers/',         cv.ExportTeacherPDFAPI.as_view(),              name='coordinator-export-teacher-pdf'),
    path('export/pdf/students/',         cv.ExportStudentPDFAPI.as_view(),              name='coordinator-export-student-pdf'),
    path('export/pdf/subjects/',         cv.ExportSubjectPDFAPI.as_view(),              name='coordinator-export-subject-pdf'),
    path('export/pdf/escalations/',      cv.ExportEscalationPDFAPI.as_view(),           name='coordinator-export-escalation-pdf'),
]