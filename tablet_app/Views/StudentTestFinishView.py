from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from tablet_app.models import StudentTestAttemptModel, StudentAnswerModel, TestModel


class StudentTestFinishAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:
            attempt_id = request.data.get('attempt_id')

            if not attempt_id:
                return Response(
                    {'status': False, 'message': 'attempt_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                attempt = StudentTestAttemptModel.objects.select_related(
                    'test'
                ).get(
                    id=attempt_id,
                    student=request.user
                )
            except StudentTestAttemptModel.DoesNotExist:
                return Response(
                    {'status': False, 'message': 'Test attempt not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if attempt.is_completes:
                return Response(
                    {'status': False, 'message': 'Test already completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            test = attempt.test

            if test.enable_timer and test.duration_minutes:
                end_time = attempt.started_at + timezone.timedelta(
                    minutes=test.duration_minutes
                )
                if timezone.now() > end_time:
                    pass

            answers = StudentAnswerModel.objects.select_related(
                'question', 'selected_option'
            ).filter(
                attempt=attempt
            )

            total_score = 0
            attempted_questions = answers.count()

            for answer in answers:
                if answer.selected_option.is_correct:
                    total_score += answer.question.marks

            attempt.score = total_score
            attempt.completed_at = timezone.now()
            attempt.is_completes = True
            attempt.save()

            return Response(
                {
                    'status': True,
                    'message': 'Test submitted successfully',
                    'data': {
                        'attempt_id': attempt.id,
                        'test': test.title,
                        'score': total_score,
                        'total_questions': test.number_of_questions,
                        'attempted_questions': attempted_questions,
                        'completed_at': attempt.completed_at
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
