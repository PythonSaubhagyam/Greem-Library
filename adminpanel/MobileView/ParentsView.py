from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from tablet_app.models import *
from user_management.models import *
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import os
import json

# Optional: Google Generative AI (only needed for AI tips generation)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class LearningBehaviourAPI(APIView):

    def get(self, request, pk):

        end = timezone.now()
        start = end - timedelta(days=21)

        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__range=(start, end)
        )

        print(sessions,'sessions')

        # ---------- DAILY STUDY TIME ----------
        daily = {}

        for s in sessions:
            day = s.start_time.date()
            print(day,'date')
            daily.setdefault(str(day), 0)
            print(daily[str(day)])
            daily[str(day)] += s.duration
            print(daily,'daily')
        print(daily)

        avg_daily = (
            sum(daily.values()) / 7
            if daily else 0
        )

        # ---------- CONSISTENCY ----------
        studied_days = len(daily)
        consistency = round((studied_days / 7) * 100, 2)

        # ---------- BEST STUDY PERIOD ----------
        buckets = {
            "morning": 0,
            "afternoon": 0,
            "evening": 0,
            "night": 0
        }

        for s in sessions:
            h = s.start_time.hour

            if h < 12:
                buckets["morning"] += s.duration
            elif h < 16:
                buckets["afternoon"] += s.duration
            elif h < 20:
                buckets["evening"] += s.duration
            else:
                buckets["night"] += s.duration

        best_period = max(buckets, key=buckets.get) if sessions else None

        # ---------- MESSAGE GENERATION ----------
        if best_period:
            message = f"Student studies most during {best_period}"
        else:
            message = "No study pattern detected"

        # ---------- EXTRA METRICS ----------
        total_minutes = sum(s.duration for s in sessions)
        avg_session = (
            total_minutes / sessions.count()
            if sessions else 0
        )

        return Response({

            "daily_hours": {k: round(v/60, 2) for k, v in daily.items()},
            "avg_daily_hours": round(avg_daily/60, 2),

            "consistency_percent": consistency,

            "best_period": best_period,
            "period_distribution": {k: round(v/60, 2) for k, v in buckets.items()},
            "message": message,

            "total_weekly_hours": round(total_minutes/60, 2),
            "avg_session_length": round(avg_session/60, 2),
            "session_count": sessions.count()
        })

class RiskDetectionAPI(APIView):

    def get(self, request, pk):

        now = timezone.now()

        week1 = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=now - timedelta(days=7)
        )

        week2 = StudySession.objects.filter(
            student_id=pk,
            start_time__range=(
                now - timedelta(days=14),
                now - timedelta(days=7)
            )
        )

        total1 = sum(s.duration for s in week1)
        total2 = sum(s.duration for s in week2)

        long_sessions = week1.filter(duration__gt=120).count()
        late_night = week1.filter(start_time__hour__gte=23).count()

        engagement_drop = total1 < total2 * 0.6 if total2 else False

        risk = "LOW"

        if long_sessions > 3 or late_night > 3:
            risk = "MEDIUM"

        if engagement_drop:
            risk = "HIGH"

        return Response({
            "burnout_risk": risk,
            "long_sessions": long_sessions,
            "late_night_sessions": late_night,
            "engagement_drop": engagement_drop,
            "weekly_hours": round(total1/60,2)
        })
    

class GrowthEffortAPI(APIView):

    def get(self, request, pk):

        now = timezone.now()
        data = []

        for i in range(4):

            end = now - timedelta(days=i*7)
            print(end,'end')
            start = end - timedelta(days=7)
            print(start,'start')

            sessions = StudySession.objects.filter(
                student_id=pk,
                start_time__range=(start, end)
            )

            attempts = StudentTestAttemptModel.objects.filter(
                student_id=pk,
                started_at__range=(start, end)
            )

            effort = sum(s.duration for s in sessions)

            # ⭐ Percentage normalization
            percentages = []

            for a in attempts:
                if a.test.total_marks > 0:
                    percent = (a.score / a.test.total_marks) * 100

                    # filter invalid data
                    if percent > 100:
                        continue

                    percentages.append(round(percent, 1))
            avg_pct = (
                sum(percentages) / len(percentages)
                if percentages else 0
            )

            data.append({
                "week": f"{i+1}",
                "effort_hours": round(effort/60, 2),
                "avg_percentage": round(avg_pct,2)
            })

        return Response(data[::-1])

class PerformanceTrendAPI(APIView):

    def get(self, request, pk):

        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).order_by("started_at")

        percentages = []

        for a in attempts:
            total = a.test.total_marks
            if total > 0:
                pct = (a.score / total) * 100
                percentages.append(round(pct, 2))


        trend = "STABLE"
        if len(percentages) >= 3:

            mid = len(percentages) // 2

            first_half = percentages[:mid]
            second_half = percentages[mid:]
            print(first_half,'first')
            print(second_half,'second')

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            print(first_avg,'first avg')
            print(second_avg,'second avg')

            if second_avg > first_avg + 3:
                trend = "IMPROVING"
            elif second_avg < first_avg - 3:
                trend = "DECLINING"

        return Response({
            "percentages": percentages,
            "trend": trend,
            "attempt_count": len(percentages)
        })
    

class StudyCalendarAPI(APIView):

    def get(self, request, student_id):

        days = int(request.GET.get("days", 30))  # default last 30 days

        end = timezone.now().date()
        start = end - timedelta(days=days-1)

        sessions = StudySession.objects.filter(
            student_id=student_id,
            start_time__date__range=(start, end)
        )

        # aggregate minutes per day
        daily_minutes = {}

        for s in sessions:
            day = s.start_time.date()
            daily_minutes.setdefault(day, 0)
            daily_minutes[day] += s.duration or 0

        calendar = {}

        for i in range(days):
            day = start + timedelta(days=i)
            minutes = daily_minutes.get(day, 0)

            if minutes >= 30:
                status = "green"
            elif minutes > 0:
                status = "yellow"
            else:
                status = "red"

            calendar[str(day)] = {
                "hours": round(minutes/60, 2),
                "status": status
            }

        return Response({
            "calendar": calendar
        })


def generate_parent_tips(llm_input: dict) -> list:
    """
    Generate personalized parent coaching tips
    using Gemini 2.5 Flash (latest SDK)
    """
    if not GENAI_AVAILABLE:
        return "AI tips generation is not available. Please install google-generativeai package."

    client = genai.Client(
        api_key=settings.GOOGLE_GEN_API_KEY
    )

    prompt = f"""
You are an expert academic parent coach.

Analyze the student learning profile and write a concise parent guidance summary.

STRICT RULES:
• Write ONLY 3 to 4 sentences total (not paragraphs, not bullet points)
• Cover strengths, weak areas, study habits, and academic performance
• Mention subject strengths and subject areas needing attention if available
• Include habit observations (consistency, effort, engagement, study timing)
• Provide practical and supportive guidance for parents
• Use simple, warm, parent-friendly language
• Avoid generic advice
• Do NOT repeat data numbers unless necessary
• Do NOT use bullet points or headings

Student Profile Data:
{json.dumps(llm_input, indent=2)}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=3000
        )
    )

    text = response.text.strip()

    # Convert bullet text → list
    tips = []
    for line in text.split("\n"):
        line = line.strip().lstrip("•- ").strip()
        if line:
            tips.append(line)

    return text

class ParentAIInsightsAPI(APIView):

    def get(self, request, pk):

        now = timezone.now()
        last14 = now - timedelta(days=30)

        # =========================
        # STUDY SESSIONS
        # =========================
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last14
        )

        session_count = sessions.count()

        daily_minutes = defaultdict(int)
        subject_minutes = defaultdict(int)
        interaction_total = 0

        for s in sessions:
            day = s.start_time.date()
            daily_minutes[day] += s.duration or 0

            if s.subject:
                subject_minutes[s.subject.name] += s.duration or 0

            interaction_total += s.interaction_count or 0

        studied_days = len(daily_minutes)
        total_minutes = sum(daily_minutes.values())
        avg_daily_hours = round((total_minutes / 14) / 60, 2)
        effort_hours = round(total_minutes / 60, 2)

        consistency_pct = round((studied_days / 14) * 100, 2)

        # Study streak
        streak = 0
        for i in range(14):
            d = (now.date() - timedelta(days=i))
            if d in daily_minutes:
                streak += 1
            else:
                break

        # Best study period
        buckets = {"morning":0,"afternoon":0,"evening":0,"night":0}
        for s in sessions:
            h = s.start_time.hour
            if h < 12: buckets["morning"] += s.duration
            elif h < 16: buckets["afternoon"] += s.duration
            elif h < 20: buckets["evening"] += s.duration
            else: buckets["night"] += s.duration

        best_period = max(buckets, key=buckets.get) if sessions else None

        avg_session_minutes = round(total_minutes / session_count, 2) if session_count else 0

        # Study intensity
        if avg_session_minutes >= 90:
            intensity_level = "high"
        elif avg_session_minutes >= 40:
            intensity_level = "balanced"
        else:
            intensity_level = "low"

        # Sessions per study day
        sessions_per_day = round(session_count / studied_days, 2) if studied_days else 0

        # Discipline level
        if consistency_pct >= 75 and streak >= 5:
            discipline_level = "strong"
        elif consistency_pct >= 40:
            discipline_level = "moderate"
        else:
            discipline_level = "weak"

        # Risk signals
        long_sessions = sessions.filter(duration__gt=120).count()
        late_night_sessions = sessions.filter(start_time__hour__gte=23).count()

        # =========================
        # TEST PERFORMANCE
        # =========================
        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).order_by("started_at")

        percentages = []
        subject_scores = defaultdict(list)

        for a in attempts:
            total = a.test.total_marks
            if total > 0:
                pct = (a.score / total) * 100
                percentages.append(pct)

                # If Test has subject
                if hasattr(a.test, "subject") and a.test.subject:
                    subject_scores[a.test.subject.name].append(pct)

        avg_pct = round(sum(percentages)/len(percentages),2) if percentages else 0

        trend = "stable"
        if len(percentages) >= 3:
            mid = len(percentages)//2
            first_avg = sum(percentages[:mid])/len(percentages[:mid])
            second_avg = sum(percentages[mid:])/len(percentages[mid:])
            if second_avg > first_avg + 3:
                trend = "improving"
            elif second_avg < first_avg - 3:
                trend = "declining"

        # Subject performance averages
        subject_perf = {
            sub: round(sum(vals)/len(vals),2)
            for sub, vals in subject_scores.items()
        }
        print(subject_scores,'subject scores')
        print(subject_perf,'subject performance')

        # =========================
        # Strengths & Weakness
        # =========================
        strong_subjects = [
            s for s,v in subject_perf.items() if v >= 75
        ]

        weak_subjects = [
            s for s,v in subject_perf.items() if v < 60
        ]

        # =========================
        # BUILD LLM INPUT
        # =========================
        llm_input = {
            "learning_habits": {
                "consistency_percent": consistency_pct,
                "avg_daily_study_hours": avg_daily_hours,
                "total_effort_hours_14d": effort_hours,
                "study_streak_days": streak,
                "best_study_period": best_period
            },
            "study_quality": {
                "avg_session_minutes": avg_session_minutes,
                "intensity_level": intensity_level,
                "sessions_per_study_day": sessions_per_day,
                "discipline_level": discipline_level
            },
            "risk_signals": {
                "long_sessions": long_sessions,
                "late_night_sessions": late_night_sessions
            },
            "academic_performance": {
                "average_percentage": avg_pct,
                "performance_trend": trend,
                "tests_taken": len(percentages)
            },
            "subject_wise_effort_hours": {
                k: round(v/60,2) for k,v in subject_minutes.items()
            },
            "subject_wise_performance": subject_perf,
            "strengths": {
                "strong_subjects": strong_subjects,
                "high_avg_performance": avg_pct >= 75,
                "good_consistency": consistency_pct >= 70,
                "improving_performance": trend == "improving"
            },
            "attention_areas": {
                "weak_subjects": weak_subjects,
                "low_avg_performance": avg_pct < 60,
                "poor_consistency": consistency_pct < 40,
                "burnout_risk": long_sessions > 3,
                "late_night_habit": late_night_sessions > 3,
                "declining_performance": trend == "declining"
            }
        }

        # =========================
        # SEND TO LLM (pseudo)
        # =========================
        # tips = generate_parent_tips(llm_input)

        # Add helpful message if subject data is limited
        subject_data_note = None
        if not subject_minutes or len(subject_minutes) == 0:
            subject_data_note = "Subject-wise study data not available. Students are studying but subjects are not being tracked during study sessions."

        return Response({
            "llm_input": llm_input,
            "subject_data_note": subject_data_note,
            # "parent_coaching_tips": tips
        })


# ============================================================================
# NEW PARENT APIs - Phase 2
# ============================================================================

class AcademicHealthScoreAPI(APIView):
    """
    Monthly Academic Health Score (0-100)
    Combines: Test performance (30%), Consistency (20%), Improvement (15%),
              Homework quality (15%), Engagement (10%), Revision frequency (10%)
    """

    def get(self, request, pk):
        now = timezone.now()
        last30 = now - timedelta(days=30)

        # ========== TEST PERFORMANCE (30%) ==========
        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk,
            started_at__gte=last30
        )

        percentages = []
        for a in attempts:
            total = a.test.total_marks
            if total > 0:
                pct = (a.score / total) * 100
                percentages.append(pct)

        test_performance = sum(percentages) / len(percentages) if percentages else 50

        # ========== CONSISTENCY (20%) ==========
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last30
        )

        daily_minutes = {}
        for s in sessions:
            day = s.start_time.date()
            daily_minutes.setdefault(day, 0)
            daily_minutes[day] += s.duration or 0

        studied_days = len(daily_minutes)
        consistency = (studied_days / 30) * 100

        # ========== IMPROVEMENT TREND (15%) ==========
        improvement_score = 50  # neutral
        if len(percentages) >= 4:
            mid = len(percentages) // 2
            first_avg = sum(percentages[:mid]) / len(percentages[:mid])
            second_avg = sum(percentages[mid:]) / len(percentages[mid:])
            
            diff = second_avg - first_avg
            if diff > 10:
                improvement_score = 100
            elif diff > 5:
                improvement_score = 80
            elif diff > 0:
                improvement_score = 60
            elif diff > -5:
                improvement_score = 40
            else:
                improvement_score = 20

        # ========== HOMEWORK QUALITY (15%) ==========
        # Check if HomeworkSubmissionModel exists, otherwise use test data
        try:
            from user_management.models import HomeworkSubmissionModel
            homework_subs = HomeworkSubmissionModel.objects.filter(
                student_id=pk,
                submitted_at__gte=last30
            )
            if homework_subs.exists():
                scored = homework_subs.exclude(score__isnull=True)
                if scored.exists():
                    hw_scores = [s.score for s in scored if s.score is not None]
                    homework_quality = sum(hw_scores) / len(hw_scores) if hw_scores else 50
                else:
                    homework_quality = 50
            else:
                homework_quality = 50
        except:
            homework_quality = test_performance * 0.9  # fallback to test performance

        # ========== ENGAGEMENT (10%) ==========
        total_interactions = sum(s.interaction_count or 0 for s in sessions)
        avg_interactions_per_day = total_interactions / 30
        
        if avg_interactions_per_day >= 50:
            engagement = 100
        elif avg_interactions_per_day >= 30:
            engagement = 80
        elif avg_interactions_per_day >= 15:
            engagement = 60
        elif avg_interactions_per_day >= 5:
            engagement = 40
        else:
            engagement = 20

        # ========== REVISION FREQUENCY (10%) ==========
        total_study_minutes = sum(daily_minutes.values())
        avg_daily_minutes = total_study_minutes / 30
        
        if avg_daily_minutes >= 60:
            revision_frequency = 100
        elif avg_daily_minutes >= 45:
            revision_frequency = 80
        elif avg_daily_minutes >= 30:
            revision_frequency = 60
        elif avg_daily_minutes >= 15:
            revision_frequency = 40
        else:
            revision_frequency = 20

        # ========== CALCULATE HEALTH SCORE ==========
        health_score = (
            test_performance * 0.30 +
            consistency * 0.20 +
            improvement_score * 0.15 +
            homework_quality * 0.15 +
            engagement * 0.10 +
            revision_frequency * 0.10
        )
        health_score = round(min(100, max(0, health_score)), 1)

        # ========== DETERMINE STATUS ==========
        if health_score >= 85:
            status = "Excellent"
            status_emoji = "🟢"
        elif health_score >= 70:
            status = "Improving"
            status_emoji = "🟡"
        elif health_score >= 50:
            status = "Attention Needed"
            status_emoji = "🟠"
        else:
            status = "Immediate Focus"
            status_emoji = "🔴"

        # ========== WEEK CHANGE ==========
        # Compare with previous week
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        this_week_sessions = sessions.filter(start_time__gte=week_ago)
        last_week_sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__range=(two_weeks_ago, week_ago)
        )
        
        this_week_minutes = sum(s.duration or 0 for s in this_week_sessions)
        last_week_minutes = sum(s.duration or 0 for s in last_week_sessions)
        
        if last_week_minutes > 0:
            week_change = round(((this_week_minutes - last_week_minutes) / last_week_minutes) * 100, 1)
        else:
            week_change = 0

        return Response({
            "health_score": health_score,
            "status": status,
            "status_emoji": status_emoji,
            "breakdown": {
                "test_performance": round(test_performance, 1),
                "consistency": round(consistency, 1),
                "improvement_trend": round(improvement_score, 1),
                "homework_quality": round(homework_quality, 1),
                "engagement": round(engagement, 1),
                "revision_frequency": round(revision_frequency, 1)
            },
            "this_week_change": week_change,
            "tests_taken": len(percentages),
            "study_days": studied_days
        })


class FamilyDashboardAPI(APIView):
    """
    Multi-Child Dashboard for parents with multiple kids
    Returns all children with their academic health summary
    """

    def get(self, request):
        user = request.user
        
        # Get all students assigned to this parent
        students = StudentModel.objects.filter(parent=user)
        
        if not students.exists():
            return Response({
                "children": [],
                "message": "No children found for this parent"
            })

        children_data = []
        now = timezone.now()
        last30 = now - timedelta(days=30)

        for student in students:
            # Get academic health score components
            sessions = StudySession.objects.filter(
                student_id=student.id,
                start_time__gte=last30
            )

            attempts = StudentTestAttemptModel.objects.filter(
                student_id=student.id,
                started_at__gte=last30
            )

            # Test performance
            percentages = []
            subject_scores = defaultdict(list)
            for a in attempts:
                total = a.test.total_marks
                if total > 0:
                    pct = (a.score / total) * 100
                    percentages.append(pct)
                    if hasattr(a.test, "subject") and a.test.subject:
                        subject_scores[a.test.subject.name].append(pct)

            test_performance = sum(percentages) / len(percentages) if percentages else 50

            # Consistency
            daily_minutes = {}
            for s in sessions:
                day = s.start_time.date()
                daily_minutes.setdefault(day, 0)
                daily_minutes[day] += s.duration or 0
            
            studied_days = len(daily_minutes)
            consistency = (studied_days / 30) * 100

            # Calculate simple health score
            health_score = round((test_performance * 0.6 + consistency * 0.4), 1)
            health_score = min(100, max(0, health_score))

            # Determine status
            if health_score >= 85:
                status = "Excellent"
            elif health_score >= 70:
                status = "Improving"
            elif health_score >= 50:
                status = "Attention Needed"
            else:
                status = "Immediate Focus"

            # Week change
            week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)
            
            this_week_sessions = sessions.filter(start_time__gte=week_ago)
            last_week_sessions = StudySession.objects.filter(
                student_id=student.id,
                start_time__range=(two_weeks_ago, week_ago)
            )
            
            this_week_minutes = sum(s.duration or 0 for s in this_week_sessions)
            last_week_minutes = sum(s.duration or 0 for s in last_week_sessions)
            
            if last_week_minutes > 0:
                week_change = round(((this_week_minutes - last_week_minutes) / last_week_minutes) * 100, 1)
            else:
                week_change = 0

            # Find weak topic (lowest scoring subject)
            weak_topic = None
            if subject_scores:
                subject_avgs = {
                    sub: sum(vals)/len(vals) for sub, vals in subject_scores.items()
                }
                weak_topic = min(subject_avgs, key=subject_avgs.get)

            # Add note if no subject data
            subject_note = None if subject_scores else "Subject data not tracked during study"

            children_data.append({
                "student_id": student.id,
                "name": student.student_name,
                "class": student.student_class.get_display_name() if student.student_class else None,
                "academic_health_score": health_score,
                "this_week_change": week_change,
                "weak_topic": weak_topic,
                "subject_note": subject_note,
                "status": status,
                "tests_taken": len(percentages),
                "study_days": studied_days
            })

        return Response({
            "children": children_data,
            "total_children": len(children_data)
        })


class GoalSettingAPI(APIView):
    """
    Goal Setting System for students
    CRUD operations for student goals with AI predictions
    """

    def get(self, request, student_id=None):
        """Get goals for a student"""
        try:
            from user_management.models import StudentGoalModel
        except ImportError:
            return Response({
                "error": "Goal model not yet migrated. Please run migrations."
            }, status=400)

        if student_id:
            goals = StudentGoalModel.objects.filter(student_id=student_id)
        else:
            # Get goals for all children of this parent
            user = request.user
            students = StudentModel.objects.filter(parent=user)
            goals = StudentGoalModel.objects.filter(student__in=students)

        goals_data = []
        now = timezone.now()

        for goal in goals:
            # Calculate current progress
            current_value = self._calculate_current_value(goal)
            
            # Calculate progress percentage
            if goal.target_value > 0:
                progress = (current_value / goal.target_value) * 100
            else:
                progress = 0
            
            # AI prediction
            ai_prediction = self._generate_prediction(goal, current_value)

            goals_data.append({
                "id": goal.id,
                "student_id": goal.student.id,
                "student_name": goal.student.student_name,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "current_value": round(current_value, 2),
                "progress_percentage": round(min(100, progress), 1),
                "subject": goal.subject.name if goal.subject else None,
                "deadline": goal.deadline,
                "is_achieved": goal.is_achieved or progress >= 100,
                "ai_prediction": ai_prediction,
                "created_at": goal.created_at
            })

        return Response({"goals": goals_data})

    def post(self, request):
        """Create a new goal"""
        try:
            from user_management.models import StudentGoalModel
        except ImportError:
            return Response({
                "error": "Goal model not yet migrated. Please run migrations."
            }, status=400)

        data = request.data
        
        required_fields = ['student_id', 'goal_type', 'target_value']
        for field in required_fields:
            if field not in data:
                return Response({
                    "error": f"Missing required field: {field}"
                }, status=400)

        try:
            student = StudentModel.objects.get(id=data['student_id'])
        except StudentModel.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        # Get subject if provided
        subject = None
        if 'subject_id' in data:
            try:
                subject = Subject.objects.get(id=data['subject_id'])
            except Subject.DoesNotExist:
                pass

        goal = StudentGoalModel.objects.create(
            student=student,
            goal_type=data['goal_type'],
            target_value=data['target_value'],
            subject=subject,
            deadline=data.get('deadline'),
            created_by=request.user
        )

        return Response({
            "message": "Goal created successfully",
            "goal_id": goal.id
        }, status=201)

    def put(self, request, goal_id=None):
        """Update a goal"""
        try:
            from user_management.models import StudentGoalModel
        except ImportError:
            return Response({
                "error": "Goal model not yet migrated."
            }, status=400)

        if not goal_id:
            goal_id = request.data.get('goal_id')

        try:
            goal = StudentGoalModel.objects.get(id=goal_id)
        except StudentGoalModel.DoesNotExist:
            return Response({"error": "Goal not found"}, status=404)

        data = request.data
        
        if 'target_value' in data:
            goal.target_value = data['target_value']
        if 'deadline' in data:
            goal.deadline = data['deadline']
        if 'is_achieved' in data:
            goal.is_achieved = data['is_achieved']

        goal.save()

        return Response({"message": "Goal updated successfully"})

    def delete(self, request, goal_id=None):
        """Delete a goal"""
        try:
            from user_management.models import StudentGoalModel
        except ImportError:
            return Response({
                "error": "Goal model not yet migrated."
            }, status=400)

        if not goal_id:
            goal_id = request.data.get('goal_id')

        try:
            goal = StudentGoalModel.objects.get(id=goal_id)
            goal.delete()
            return Response({"message": "Goal deleted successfully"})
        except StudentGoalModel.DoesNotExist:
            return Response({"error": "Goal not found"}, status=404)

    def _calculate_current_value(self, goal):
        """Calculate current progress based on goal type"""
        now = timezone.now()
        last30 = now - timedelta(days=30)
        student_id = goal.student.id

        if goal.goal_type == 'score':
            # Average test score
            attempts = StudentTestAttemptModel.objects.filter(
                student_id=student_id,
                started_at__gte=last30
            )
            if goal.subject:
                attempts = attempts.filter(test__subject=goal.subject)
            
            percentages = []
            for a in attempts:
                if a.test.total_marks > 0:
                    percentages.append((a.score / a.test.total_marks) * 100)
            
            return sum(percentages) / len(percentages) if percentages else 0

        elif goal.goal_type == 'consistency':
            # Days studied in last week
            sessions = StudySession.objects.filter(
                student_id=student_id,
                start_time__gte=now - timedelta(days=7)
            )
            studied_days = len(set(s.start_time.date() for s in sessions))
            return studied_days

        elif goal.goal_type == 'study_time':
            # Average daily study hours
            sessions = StudySession.objects.filter(
                student_id=student_id,
                start_time__gte=now - timedelta(days=7)
            )
            total_minutes = sum(s.duration or 0 for s in sessions)
            return round(total_minutes / (7 * 60), 2)  # hours per day

        elif goal.goal_type == 'improvement':
            # Score improvement percentage
            attempts = StudentTestAttemptModel.objects.filter(
                student_id=student_id
            ).order_by('started_at')
            
            if goal.subject:
                attempts = attempts.filter(test__subject=goal.subject)

            percentages = []
            for a in attempts:
                if a.test.total_marks > 0:
                    percentages.append((a.score / a.test.total_marks) * 100)

            if len(percentages) >= 4:
                mid = len(percentages) // 2
                first_avg = sum(percentages[:mid]) / len(percentages[:mid])
                second_avg = sum(percentages[mid:]) / len(percentages[mid:])
                return round(second_avg - first_avg, 2)
            return 0

        return 0

    def _generate_prediction(self, goal, current_value):
        """Generate AI prediction based on current progress"""
        if goal.is_achieved or current_value >= goal.target_value:
            return "Goal achieved! 🎉"

        progress_rate = current_value / goal.target_value if goal.target_value > 0 else 0

        if progress_rate >= 0.9:
            return "Almost there! Goal achievable within days."
        elif progress_rate >= 0.7:
            return "Good progress. On track to achieve goal."
        elif progress_rate >= 0.5:
            return "Moderate progress. Increase effort to meet deadline."
        elif progress_rate >= 0.3:
            return "Needs more focus. Consider additional study time."
        else:
            return "Requires significant improvement. Set smaller milestones."


class ConceptConfidenceAPI(APIView):
    """
    Concept Confidence Meter - Chapter/topic-wise mastery levels
    Shows: Mastered / Improving / Needs Practice / Critical
    """

    def get(self, request, pk):
        # Get all test attempts for this student
        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).select_related('test', 'test__subject')

        # Group by subject
        subject_data = defaultdict(lambda: {"attempts": [], "total_score": 0, "total_marks": 0})
         
        

        for a in attempts:
            if a.test.subject:
                subject_name = a.test.subject.name
                subject_data[subject_name]["attempts"].append({
                    "score": a.score,
                    "total_marks": a.test.total_marks,
                    "date": timezone.localtime(a.started_at).strftime("%Y-%m-%d %H:%M:%S")
                })
                subject_data[subject_name]["total_score"] += a.score
                subject_data[subject_name]["total_marks"] += a.test.total_marks
        print(subject_data,'subject data')
        confidence_data = []

        for subject, data in subject_data.items():
            percentages = []

            for a in data["attempts"]:
                total = a["total_marks"]
                score = a["score"]
                if total > 0:
                    percentages.append((score / total) * 100)

            if percentages:
                avg_percentage = sum(percentages) / len(percentages)
            else:
                avg_percentage = 0

            # Determine confidence level
            if avg_percentage >= 85:
                level = "Mastered"
                level_emoji = "🟢"
            elif avg_percentage >= 70:
                level = "Improving"
                level_emoji = "🟡"
            elif avg_percentage >= 50:
                level = "Needs Practice"
                level_emoji = "🟠"
            else:
                level = "Critical"
                level_emoji = "🔴"

            # Calculate trend (improving/declining)
            recent_attempts = sorted(data["attempts"], key=lambda x: x["date"])[-5:]
            if len(recent_attempts) >= 3:
                first_half = recent_attempts[:len(recent_attempts)//2]
                second_half = recent_attempts[len(recent_attempts)//2:]
                
                first_avg = sum(a["score"]/a["total_marks"]*100 for a in first_half if a["total_marks"] > 0) / len(first_half)
                second_avg = sum(a["score"]/a["total_marks"]*100 for a in second_half if a["total_marks"] > 0) / len(second_half)
                
                if second_avg > first_avg + 5:
                    trend = "improving"
                elif second_avg < first_avg - 5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "not_enough_data"

            confidence_data.append({
                "subject": subject,
                "confidence_level": level,
                "level_emoji": level_emoji,
                "average_percentage": round(avg_percentage, 1),
                "attempts_count": len(data["attempts"]),
                "trend": trend
            })

        # Sort by average percentage (weakest first)
        confidence_data.sort(key=lambda x: x["average_percentage"])

        # Add helpful message
        data_note = "Concept confidence is based on test performance data by subject." if confidence_data else "No subject-wise test data available yet. Confidence meter will show data once tests with subjects are completed."

        return Response({
            "confidence_data": confidence_data,
            "total_subjects": len(confidence_data),
            "note": data_note
        })


class ExamReadinessAPI(APIView):
    """
    Exam Readiness Meter
    Simple status: 🔴 Not Ready / 🟡 Improving / 🟢 Exam Ready
    Based on: recent performance, consistency, topic coverage
    """

    def get(self, request, pk):
        now = timezone.now()
        last14 = now - timedelta(days=14)

        # ========== Recent Test Performance ==========
        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk,
            started_at__gte=last14
        )

        recent_percentages = []
        for a in attempts:
            if a.test.total_marks > 0:
                recent_percentages.append((a.score / a.test.total_marks) * 100)

        avg_recent = sum(recent_percentages) / len(recent_percentages) if recent_percentages else 0

        # ========== Consistency (Study Days) ==========
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last14
        )

        studied_days = len(set(s.start_time.date() for s in sessions))
        consistency_rate = studied_days / 14

        # ========== Performance Trend ==========
        all_attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).order_by('started_at')

        all_percentages = []
        for a in all_attempts:
            if a.test.total_marks > 0:
                all_percentages.append((a.score / a.test.total_marks) * 100)

        is_improving = False
        if len(all_percentages) >= 4:
            mid = len(all_percentages) // 2
            first_avg = sum(all_percentages[:mid]) / len(all_percentages[:mid])
            second_avg = sum(all_percentages[mid:]) / len(all_percentages[mid:])
            is_improving = second_avg > first_avg

        # ========== Calculate Readiness Score ==========
        readiness_score = (
            avg_recent * 0.5 +
            (consistency_rate * 100) * 0.3 +
            (50 if is_improving else 30) * 0.2
        )

        # ========== Determine Status ==========
        if readiness_score >= 75 and avg_recent >= 70:
            status = "Exam Ready"
            status_emoji = "🟢"
            message = "Great preparation! Ready for the exam."
        elif readiness_score >= 50 or is_improving:
            status = "Improving"
            status_emoji = "🟡"
            message = "Good progress, but continue practicing."
        else:
            status = "Not Ready"
            status_emoji = "🔴"
            message = "More preparation needed. Focus on weak areas."

        return Response({
            "status": status,
            "status_emoji": status_emoji,
            "readiness_score": round(readiness_score, 1),
            "message": message,
            "details": {
                "recent_average": round(avg_recent, 1),
                "study_consistency": round(consistency_rate * 100, 1),
                "is_improving": is_improving,
                "tests_taken_14d": len(recent_percentages),
                "study_days_14d": studied_days
            }
        })


class ParentTeacherSyncAPI(APIView):
    """
    Parent-Teacher Sync Section
    Shows: Teacher remarks, upcoming tests, suggested practice
    """

    def get(self, request, pk):
        try:
            from user_management.models import TeacherRemarkModel
            remarks_available = True
        except ImportError:
            remarks_available = False

        now = timezone.now()

        # ========== Teacher Remarks ==========
        remarks_data = []
        if remarks_available:
            remarks = TeacherRemarkModel.objects.filter(
                student_id=pk,
                is_visible_to_parent=True
            ).order_by('-created_at')[:10]

            for r in remarks:
                remarks_data.append({
                    "id": r.id,
                    "teacher_name": f"{r.teacher.first_name} {r.teacher.last_name}" if r.teacher else "Unknown",
                    "remark": r.remark,
                    "remark_type": r.remark_type,
                    "created_at": r.created_at
                })

        # ========== Upcoming Tests ==========
        student = StudentModel.objects.get(id=pk)

        tests = TestModel.objects.filter(student=student).select_related('subject')

        pending_tests_data = []

        for t in tests:
            attempted = StudentTestAttemptModel.objects.filter(
                student_id=pk,
                test=t
            ).exists()

            if not attempted:
                # Determine status
                if t.scheduled_at and t.scheduled_at > now:
                    status = "upcoming"
                elif t.scheduled_at and t.scheduled_at <= now:
                    status = "missed"
                else:
                    status = "unscheduled"

                pending_tests_data.append({
                    "id": t.id,
                    "title": t.title,
                    "subject": t.subject.name if t.subject else None,
                    "total_marks": t.total_marks,
                    "duration_minutes": t.duration_minutes,
                    "scheduled_at": t.scheduled_at,
                    "status": status
                })

        # Sort: upcoming first, then missed
        pending_tests_data.sort(
            key=lambda x: (
                0 if x["status"] == "upcoming" else 1,
                x["scheduled_at"] or now
            )
        )

        pending_tests_data = pending_tests_data[:5]

        # ========== Suggested Practice ==========
        # Find weak subjects
        attempts = StudentTestAttemptModel.objects.filter(student_id=pk)
        subject_scores = defaultdict(list)
        
        for a in attempts:
            if a.test.subject and a.test.total_marks > 0:
                subject_scores[a.test.subject.name].append(
                    (a.score / a.test.total_marks) * 100
                )
        print(subject_scores,'subject scores for practice')
        weak_subjects = []
        for subject, scores in subject_scores.items():
            avg = sum(scores) / len(scores)
            if avg < 60:
                weak_subjects.append({
                    "subject": subject,
                    "average": round(avg, 1),
                    "suggestion": f"Practice more {subject} questions"
                })

        weak_subjects.sort(key=lambda x: x["average"])

        # Add helpful message if no subject data
        subject_data_available = len(subject_scores) > 0

        return Response({
            "teacher_remarks": remarks_data,
            "pending_tests": pending_tests_data,
            "suggested_practice": weak_subjects[:3],
            "has_remarks": len(remarks_data) > 0,
            "pending_tests_count": len(pending_tests_data),
            "subject_data_available": subject_data_available,
            "note": "Subject-wise practice suggestions are based on test performance data." if subject_data_available else "Subject-wise data not available for practice suggestions."
        })
# ============================================================================
# 1. LEARNING HABIT SCORE (0-100)
# Combines: daily study time + consistency + homework + revision frequency
# ============================================================================
 
class LearningHabitScoreAPI(APIView):
 
    def get(self, request, pk):
        now = timezone.now()
        last30 = now - timedelta(days=30)
        last7  = now - timedelta(days=7)
 
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last30
        )
 
        # ---------- DAILY STUDY TIME SCORE (25%) ----------
        daily_minutes = defaultdict(int)
        for s in sessions:
            daily_minutes[s.start_time.date()] += s.duration or 0
 
        total_minutes  = sum(daily_minutes.values())
        avg_daily_mins = total_minutes / 30
 
        if avg_daily_mins >= 60:
            study_time_score = 100
        elif avg_daily_mins >= 45:
            study_time_score = 80
        elif avg_daily_mins >= 30:
            study_time_score = 60
        elif avg_daily_mins >= 15:
            study_time_score = 40
        else:
            study_time_score = 20
 
        # ---------- CONSISTENCY SCORE (25%) ----------
        studied_days      = len(daily_minutes)
        consistency_pct   = (studied_days / 30) * 100
        consistency_score = min(100, consistency_pct)
 
        # ---------- HOMEWORK SCORE (25%) ----------
        homework_score = 50  # neutral default
        try:
            from user_management.models import HomeworkSubmissionModel
            subs = HomeworkSubmissionModel.objects.filter(
                student_id=pk,
                submitted_at__gte=last30
            )
            if subs.exists():
                scored = subs.exclude(score__isnull=True)
                if scored.exists():
                    hw_vals = [s.score for s in scored if s.score is not None]
                    homework_score = sum(hw_vals) / len(hw_vals) if hw_vals else 50
        except Exception:
            # Fallback: estimate from test performance
            attempts = StudentTestAttemptModel.objects.filter(
                student_id=pk,
                started_at__gte=last30
            )
            pcts = []
            for a in attempts:
                if a.test.total_marks > 0:
                    pcts.append((a.score / a.test.total_marks) * 100)
            homework_score = (sum(pcts) / len(pcts) * 0.9) if pcts else 50
 
        # ---------- REVISION FREQUENCY SCORE (25%) ----------
        # Count unique study days in last 7 days as a revision proxy
        recent_sessions = sessions.filter(start_time__gte=last7)
        recent_days     = len(set(s.start_time.date() for s in recent_sessions))
 
        if recent_days >= 6:
            revision_score = 100
        elif recent_days >= 5:
            revision_score = 85
        elif recent_days >= 4:
            revision_score = 70
        elif recent_days >= 3:
            revision_score = 55
        elif recent_days >= 2:
            revision_score = 40
        elif recent_days >= 1:
            revision_score = 25
        else:
            revision_score = 0
 
        # ---------- COMBINED HABIT SCORE ----------
        habit_score = (
            study_time_score  * 0.25 +
            consistency_score * 0.25 +
            homework_score    * 0.25 +
            revision_score    * 0.25
        )
        habit_score = round(min(100, max(0, habit_score)), 1)
 
        # ---------- STATUS ----------
        if habit_score >= 85:
            status = "Excellent"
        elif habit_score >= 70:
            status = "Good"
        elif habit_score >= 50:
            status = "Needs Improvement"
        else:
            status = "Poor"
 
        # ---------- STREAK ----------
        streak = 0
        for i in range(30):
            d = now.date() - timedelta(days=i)
            if d in daily_minutes:
                streak += 1
            else:
                break
 
        return Response({
            "habit_score": habit_score,
            "status": status,
            "streak_days": streak,
            "breakdown": {
                "study_time_score":   round(study_time_score, 1),
                "consistency_score":  round(consistency_score, 1),
                "homework_score":     round(homework_score, 1),
                "revision_score":     round(revision_score, 1),
            },
            "meta": {
                "avg_daily_minutes": round(avg_daily_mins, 1),
                "studied_days_30d":  studied_days,
                "study_days_last7":  recent_days,
            }
        })
 
# ============================================================================
# 2. REVISION FREQUENCY TRACKER
# GET /analytics/revision-tracker/<pk>/
# Tracks: chapter revisit count, last revision date, spaced repetition score
# ============================================================================
 
class RevisionFrequencyTrackerAPI(APIView):
 
    def get(self, request, pk):
        now    = timezone.now()
        last30 = now - timedelta(days=30)
 
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last30
        ).select_related('subject')
 
        # Group sessions by subject
        subject_sessions = defaultdict(list)
        for s in sessions:
            name = s.subject.name if s.subject else "General"
            subject_sessions[name].append(s)
 
        revision_data = []
 
        for subject, sess_list in subject_sessions.items():
            sorted_sessions = sorted(sess_list, key=lambda x: x.start_time)
 
            visit_count   = len(sorted_sessions)
            last_revision = sorted_sessions[-1].start_time if sorted_sessions else None
            days_since    = (now - last_revision).days if last_revision else 999
 
            # Spaced repetition score: higher = more overdue for revision
            if days_since <= 1:
                spaced_rep_score = 100
                recommendation   = "Revised recently. Keep it up."
            elif days_since <= 3:
                spaced_rep_score = 80
                recommendation   = "Good. Revise again in 2 days."
            elif days_since <= 7:
                spaced_rep_score = 60
                recommendation   = "Revision due soon."
            elif days_since <= 10:
                spaced_rep_score = 40
                recommendation   = "Revision recommended today."
            elif days_since <= 14:
                spaced_rep_score = 20
                recommendation   = "Overdue! High forgetting risk."
            else:
                spaced_rep_score = 0
                recommendation   = "Critical: Likely forgotten. Revise immediately."
 
            # Revision frequency: sessions per week
            total_hours = sum(s.duration or 0 for s in sess_list) / 60
 
            revision_data.append({
                "subject":           subject,
                "visit_count_30d":   visit_count,
                "last_revision":     last_revision,
                "days_since_revision": days_since,
                "spaced_rep_score":  spaced_rep_score,
                "recommendation":    recommendation,
                "total_hours_30d":   round(total_hours, 2),
            })
 
        # Sort: most overdue first
        revision_data.sort(key=lambda x: x["spaced_rep_score"])
 
        # Overall revision health
        if revision_data:
            avg_score = sum(r["spaced_rep_score"] for r in revision_data) / len(revision_data)
        else:
            avg_score = 0
 
        overdue_subjects = [r["subject"] for r in revision_data if r["days_since_revision"] >= 10]
 
        return Response({
            "revision_data":      revision_data,
            "overall_score":      round(avg_score, 1),
            "overdue_subjects":   overdue_subjects,
            "total_subjects":     len(revision_data),
            "alert": len(overdue_subjects) > 0
        })
 
#============================================================================
# 3. HOMEWORK QUALITY SCORE
# GET /analytics/homework-quality/<pk>/
# Accuracy %, time taken, reattempt behaviour
# ============================================================================
 
class HomeworkQualityAPI(APIView):
 
    def get(self, request, pk):
        now    = timezone.now()
        last30 = now - timedelta(days=30)
 
        try:
            from user_management.models import HomeworkSubmissionModel
            subs = HomeworkSubmissionModel.objects.filter(
                student_id=pk,
                submitted_at__gte=last30
            ).select_related('homework')
 
            if not subs.exists():
                return Response({
                    "message": "No homework submissions found in the last 30 days.",
                    "quality_score": None,
                    "submissions": []
                })
 
            submission_data = []
            accuracy_list   = []
            time_list       = []
            reattempt_count = 0
 
            for sub in subs:
                accuracy  = None
                time_mins = None
 
                if sub.score is not None and hasattr(sub, 'homework') and sub.homework.total_marks > 0:
                    accuracy = round((sub.score / sub.homework.total_marks) * 100, 1)
                    accuracy_list.append(accuracy)
 
                if hasattr(sub, 'time_taken_minutes') and sub.time_taken_minutes:
                    time_mins = sub.time_taken_minutes
                    time_list.append(time_mins)
 
                if hasattr(sub, 'attempt_number') and sub.attempt_number > 1:
                    reattempt_count += 1
 
                # Quality tag per submission
                if accuracy is not None:
                    if accuracy >= 85:
                        quality_tag = "Excellent"
                    elif accuracy >= 70:
                        quality_tag = "Good"
                    elif accuracy >= 50:
                        quality_tag = "Average"
                    else:
                        quality_tag = "Needs Practice"
                else:
                    quality_tag = "Submitted"
 
                submission_data.append({
                    "homework_title": sub.homework.title if hasattr(sub, 'homework') else "Unknown",
                    "submitted_at":   sub.submitted_at,
                    "accuracy":       accuracy,
                    "time_minutes":   time_mins,
                    "quality_tag":    quality_tag,
                })
 
            avg_accuracy  = sum(accuracy_list) / len(accuracy_list) if accuracy_list else None
            avg_time      = sum(time_list) / len(time_list) if time_list else None
            reattempt_pct = round((reattempt_count / len(subs)) * 100, 1)
 
            # Overall quality score
            quality_score = avg_accuracy if avg_accuracy is not None else 50
 
            return Response({
                "quality_score":       round(quality_score, 1),
                "avg_accuracy":        round(avg_accuracy, 1) if avg_accuracy else None,
                "avg_time_minutes":    round(avg_time, 1) if avg_time else None,
                "reattempt_percent":   reattempt_pct,
                "total_submissions":   len(subs),
                "submissions":         submission_data,
            })
 
        except ImportError:
            return Response({
                "error": "HomeworkSubmissionModel not found. Please run migrations.",
                "quality_score": None
            }, status=400)
 
# ============================================================================
# 4. SUDDEN DROP ALERT SYSTEM
# GET /analytics/drop-alert/<pk>/
# Detects: 2-test drop, engagement drop, study time reduction
# ============================================================================
 
class SuddenDropAlertAPI(APIView):
 
    def get(self, request, pk):
        now    = timezone.now()
        last7  = now - timedelta(days=7)
        prev7  = now - timedelta(days=14)
 
        alerts = []
 
        # ---------- TEST SCORE DROP ----------
        recent_attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).order_by('-started_at')[:5]
 
        percentages = []
        for a in recent_attempts:
            if a.test.total_marks > 0:
                percentages.append(round((a.score / a.test.total_marks) * 100, 1))
 
        consecutive_drops = 0
        max_drop_streak = 0

        if len(percentages) >= 3:
            for i in range(len(percentages) - 1):
                # since latest is first, compare with previous
                if percentages[i] < percentages[i + 1]:
                    drop = percentages[i + 1] - percentages[i]
                    if drop >= 5:
                        consecutive_drops += 1
                        max_drop_streak = max(max_drop_streak, consecutive_drops)
                    else:
                        consecutive_drops = 0
                else:
                    consecutive_drops = 0
 
        if max_drop_streak >= 2:
            alerts.append({
                "type":     "score_drop",
                "severity": "HIGH",
                "message":  f"Score dropped in last {max_drop_streak + 1} consecutive tests.",
                "data":     {"recent_scores": percentages[:5]},
            })
 
        # ---------- ENGAGEMENT / STUDY TIME DROP ----------
        this_week_sessions = StudySession.objects.filter(
            student_id=pk, start_time__gte=last7
        )
        prev_week_sessions = StudySession.objects.filter(
            student_id=pk, start_time__range=(prev7, last7)
        )
 
        this_mins = sum(s.duration or 0 for s in this_week_sessions)
        prev_mins = sum(s.duration or 0 for s in prev_week_sessions)
 
        if prev_mins > 0:
            drop_pct = round(((prev_mins - this_mins) / prev_mins) * 100, 1)
            if drop_pct >= 40:
                alerts.append({
                    "type":     "study_time_drop",
                    "severity": "HIGH",
                    "message":  f"Study time dropped by {drop_pct}% this week.",
                    "data": {
                        "this_week_hours": round(this_mins / 60, 2),
                        "prev_week_hours": round(prev_mins / 60, 2),
                        "drop_percent":    drop_pct,
                    },
                })
            elif drop_pct >= 25:
                alerts.append({
                    "type":     "study_time_drop",
                    "severity": "MEDIUM",
                    "message":  f"Study time reduced by {drop_pct}% this week.",
                    "data": {
                        "this_week_hours": round(this_mins / 60, 2),
                        "prev_week_hours": round(prev_mins / 60, 2),
                        "drop_percent":    drop_pct,
                    },
                })
 
        # ---------- INTERACTION / ENGAGEMENT DROP ----------
        this_interactions = sum(s.interaction_count or 0 for s in this_week_sessions)
        prev_interactions = sum(s.interaction_count or 0 for s in prev_week_sessions)
 
        if prev_interactions > 0:
            eng_drop = round(((prev_interactions - this_interactions) / prev_interactions) * 100, 1)
            if eng_drop >= 50:
                alerts.append({
                    "type":     "engagement_drop",
                    "severity": "MEDIUM",
                    "message":  f"Engagement dropped by {eng_drop}% this week.",
                    "data": {
                        "this_week_interactions": this_interactions,
                        "prev_week_interactions": prev_interactions,
                        "drop_percent":           eng_drop,
                    },
                })
 
        # ---------- SUMMARY ----------
        high_alerts   = [a for a in alerts if a["severity"] == "HIGH"]
        overall_level = "HIGH" if high_alerts else ("MEDIUM" if alerts else "NORMAL")
 
        parent_message = None
        if overall_level == "HIGH":
            parent_message = "Performance dropped this week. Suggested revision and check-in recommended."
        elif overall_level == "MEDIUM":
            parent_message = "Slight dip observed. Encourage consistent study this week."
 
        return Response({
            "alert_level":     overall_level,
            "parent_message":  parent_message,
            "alerts":          alerts,
            "alert_count":     len(alerts),
            "recent_scores":   percentages[:5],
        })
# ============================================================================
# 5. FORGETTING CURVE ALERT
# GET /analytics/forgetting-curve/<pk>/
# Flags topics not revised in 10+ days
# ============================================================================
 
class ForgettingCurveAlertAPI(APIView):
 
    def get(self, request, pk):
        now    = timezone.now()
        last60 = now - timedelta(days=60)
 
        sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=last60
        ).select_related('subject')
 
        # Last study date per subject
        last_studied = {}
        for s in sessions:
            name = s.subject.name if s.subject else "General"
            if name not in last_studied or s.start_time > last_studied[name]:
                last_studied[name] = s.start_time
 
        curve_data   = []
        critical_now = []
 
        for subject, last_time in last_studied.items():
            days_since = (now - last_time).days
 
            # Forgetting curve thresholds (Ebbinghaus-inspired)
            if days_since <= 1:
                retention_pct = 100
                urgency       = "Fresh"
            elif days_since <= 3:
                retention_pct = 80
                urgency       = "Good"
            elif days_since <= 7:
                retention_pct = 60
                urgency       = "Review Soon"
            elif days_since <= 10:
                retention_pct = 40
                urgency       = "Review Now"
            elif days_since <= 14:
                retention_pct = 25
                urgency       = "High Risk"
            elif days_since <= 21:
                retention_pct = 15
                urgency       = "Critical"
            else:
                retention_pct = 5
                urgency       = "Likely Forgotten"
 
            needs_alert = days_since >= 10
 
            if needs_alert:
                critical_now.append(subject)
 
            curve_data.append({
                "subject":        subject,
                "last_studied":   last_time,
                "days_since":     days_since,
                "retention_pct":  retention_pct,
                "urgency":        urgency,
                "needs_revision": needs_alert,
            })
 
        # Sort: most urgent first
        curve_data.sort(key=lambda x: x["retention_pct"])
 
        return Response({
            "curve_data":      curve_data,
            "critical_topics": critical_now,
            "alert":           len(critical_now) > 0,
            "alert_message":   (
                f"Revision recommended for: {', '.join(critical_now)}"
                if critical_now else "All topics recently revised. Good job!"
            ),
            "total_subjects":  len(curve_data),
        })
 
  
# ============================================================================
# 7. MISTAKE PATTERN ANALYSIS
# GET /analytics/mistake-patterns/<pk>/
# Categories: concept / calculation / careless / time-pressure mistakes
# ============================================================================
 
class MistakePatternAnalysisAPI(APIView):
 
    def get(self, request, pk):
        now    = timezone.now()
        last30 = now - timedelta(days=30)
 
        attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk,
            started_at__gte=last30
        ).select_related('test', 'test__subject')
 
        mistake_buckets = {
            "concept":       0,
            "calculation":   0,
            "careless":      0,
            "time_pressure": 0,
        }
 
        subject_mistakes = defaultdict(lambda: defaultdict(int))
        total_questions  = 0
        total_wrong      = 0
 
        for a in attempts:
            wrong = a.test.total_marks - a.score
            if wrong < 0:
                wrong = 0
 
            total_questions += a.test.total_marks
            total_wrong     += wrong
 
            subject_name = a.test.subject.name if a.test.subject else "General"
            score_pct    = (a.score / a.test.total_marks * 100) if a.test.total_marks > 0 else 0
 
            # Heuristic categorisation based on available signals
            test_duration = getattr(a.test, 'duration_minutes', None)
            time_taken    = getattr(a, 'time_taken_minutes', None)
 
            # Time pressure: finished very fast or ran out of time
            time_share = 0

            if test_duration and time_taken:
                if time_taken >= test_duration:
                    time_share = round(wrong * 0.6)
                elif time_taken >= test_duration * 0.9:
                    time_share = round(wrong * 0.4)

                if time_share > 0:
                    mistake_buckets["time_pressure"] += time_share
                    subject_mistakes[subject_name]["time_pressure"] += time_share
                    wrong -= time_share

            concept_share = 0
            careless_share = 0

            # LOW SCORE → concept issue
            if score_pct < 40:
                concept_share = round(wrong * 0.7)
                careless_share = round(wrong * 0.2)

            # MID SCORE → mixed errors
            elif score_pct < 70:
                concept_share = round(wrong * 0.4)
                careless_share = round(wrong * 0.4)

            # HIGH SCORE → mostly careless
            elif score_pct < 90:
                careless_share = round(wrong * 0.7)

            # VERY HIGH SCORE → small careless/calculation slips
            else:
                careless_share = round(wrong * 0.6)

            # apply concept
            if concept_share > 0:
                mistake_buckets["concept"] += concept_share
                subject_mistakes[subject_name]["concept"] += concept_share

            # apply careless
            if careless_share > 0:
                mistake_buckets["careless"] += careless_share
                subject_mistakes[subject_name]["careless"] += careless_share

            wrong -= (concept_share + careless_share)

            # =========================================================
            # 3. CALCULATION (fallback remaining)
            # =========================================================
            if wrong > 0:
                mistake_buckets["calculation"] += wrong
                subject_mistakes[subject_name]["calculation"] += wrong

        # =========================================================
        # PERCENTAGE CALCULATION
        # =========================================================
        total_mistakes = sum(mistake_buckets.values())

        mistake_percentage = {}
        for k, v in mistake_buckets.items():
            mistake_percentage[k] = round((v / total_mistakes) * 100, 1) if total_mistakes else 0

        # =========================================================
        # PRIMARY MISTAKE
        # =========================================================
        primary_mistake = max(mistake_buckets, key=mistake_buckets.get) if total_mistakes else None

        explanations = {
            "concept": "Child is missing fundamental understanding of topics. Focus on concept clarity.",
            "calculation": "Child understands concepts but makes arithmetic errors. Practice calculation speed.",
            "careless": "Child knows answers but makes avoidable mistakes. Encourage careful revision.",
            "time_pressure": "Child struggles to complete tests on time. Practice timed mock tests.",
        }

        # =========================================================
        # SUBJECT BREAKDOWN
        # =========================================================
        subject_breakdown = [
            {
                "subject": subject,
                "mistakes": dict(counts),
            }
            for subject, counts in subject_mistakes.items()
        ]

        # =========================================================
        # ACCURACY
        # =========================================================
        accuracy_pct = 0
        if total_questions > 0:
            accuracy_pct = round(((total_questions - total_wrong) / total_questions) * 100, 1)

        # =========================================================
        # RESPONSE
        # =========================================================
        return Response({
            "mistake_buckets": mistake_buckets,
            "mistake_percentage": mistake_percentage,
            "primary_mistake": primary_mistake,
            "primary_explanation": explanations.get(primary_mistake, ""),
            "subject_breakdown": subject_breakdown,
            "total_wrong_answers": total_wrong,
            "total_questions": total_questions,
            "accuracy_pct": accuracy_pct,
            "note": "Mistake categories are estimated using performance + timing patterns. Question-level tracking improves accuracy."
        })


class MicroProgressAlertsAPI(APIView):

    def get(self, request, pk):
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)

        alerts = []

        # =========================================================
        # 1. STUDY TIME COMPARISON (IMPROVED)
        # =========================================================
        today_sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__date=today
        )

        yesterday_sessions = StudySession.objects.filter(
            student_id=pk,
            start_time__date=yesterday
        )

        today_mins = sum(s.duration or 0 for s in today_sessions)
        yesterday_mins = sum(s.duration or 0 for s in yesterday_sessions)

        if today_mins >= 20 and today_mins > yesterday_mins * 1.2:
            alerts.append({
                "type": "study_time_win",
                "message": f"Strong improvement! Studied {today_mins - yesterday_mins} more minutes today.",
                "emoji": "📚"
            })

        # =========================================================
        # 2. SUBJECT IMPROVEMENT (TREND BASED)
        # =========================================================
        recent_attempts = StudentTestAttemptModel.objects.filter(
            student_id=pk
        ).order_by('-started_at').select_related('test__subject')[:30]

        subject_scores = defaultdict(list)

        for a in recent_attempts:
            if a.test and a.test.subject and a.test.total_marks:
                subject_scores[a.test.subject.name].append(
                    (a.score / a.test.total_marks) * 100
                )

        for subject, scores in subject_scores.items():

            if len(scores) < 3:
                continue

            latest_avg = sum(scores[:2]) / 2
            previous_avg = sum(scores[2:5]) / min(3, len(scores[2:5]))

            diff = latest_avg - previous_avg

            if diff >= 8:
                alerts.append({
                    "type": "score_improvement",
                    "message": f"{round(diff, 1)}% improvement in {subject}!",
                    "subject": subject,
                    "prev": round(previous_avg, 1),
                    "latest": round(latest_avg, 1),
                    "emoji": "🎯"
                })

        # =========================================================
        # 3. STREAK (IMPROVED REAL CHECK)
        # =========================================================
        sessions_60 = StudySession.objects.filter(
            student_id=pk,
            start_time__gte=now - timedelta(days=60)
        )

        daily_map = defaultdict(int)
        for s in sessions_60:
            if s.duration:
                daily_map[s.start_time.date()] += s.duration

        streak = 0
        for i in range(60):
            d = today - timedelta(days=i)

            # at least 15 min required to count as study day
            if daily_map.get(d, 0) >= 15:
                streak += 1
            else:
                break

        if streak in (3, 5, 7, 10, 14, 21, 30):
            alerts.append({
                "type": "streak_milestone",
                "message": f"{streak}-day REAL study streak 🔥",
                "streak": streak,
                "emoji": "🔥"
            })

        # =========================================================
        # 4. BACK ON TRACK (IMPROVED)
        # =========================================================
        if today_mins >= 20 and yesterday_mins == 0:
            alerts.append({
                "type": "back_on_track",
                "message": "Back to studying after break. Good restart!",
                "emoji": "💪"
            })

        # =========================================================
        # 5. MULTI SESSION WIN (FILTERED)
        # =========================================================
        if today_sessions.count() >= 3 and today_mins >= 30:
            alerts.append({
                "type": "multi_session",
                "message": f"Strong focus: {today_sessions.count()} quality sessions!",
                "emoji": "⭐"
            })

        # =========================================================
        # RESPONSE
        # =========================================================
        return Response({
            "alerts": alerts,
            "alert_count": len(alerts),
            "has_wins": len(alerts) > 0,
            "message": (
                "Great progress today! Keep it going."
                if alerts else
                "No meaningful progress signals yet today."
            ),
            "today_study_minutes": today_mins,
        })