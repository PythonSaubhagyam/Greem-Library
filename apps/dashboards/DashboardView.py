# adminside/api/views_dashboard.py
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # optional
from user_management.models import *
# from company.models import Company, ChatbotInfo
# from broadcastapp.models import Conversation, Account, ChatMessage
# from account.models import FacebookMetadata
# from catalogs.models import Order,OrderedProduct
# from flows_app.models import Flow
# from myapp.models import BroadcastGroup,Contact

class DashboardStatsAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # uncomment if you want login protection

    def get(self, request):
        # Total Companies
        users = UserModel.objects.filter(is_active=True).exclude(role__type__in=['Admin'])
        total_parents = users.filter(role__type='Parent').count()
        total_teachers = users.filter(role__type='Teacher').count()
        total_students = StudentModel.objects.all().count()
        
        total_users = users.count() + total_students

        data = {
            "total_companies":total_students,     # total companies
            "active_companies": total_parents,     # active companies
            "inactive_companies":  total_teachers,       # inactive companies
            "total_users": total_users,         # total users
        }
        return Response(data)

# adminside/api/views_dashboard.py
from django.db.models import Count
from datetime import timedelta

# class CompanyStatsAPIView(APIView):
#     def get(self, request):

#         data = []
#         companies = FacebookMetadata.objects.filter(user__created_by = None)

#         for company in companies:
#             company_user = company.user  

#             # Total Users created under this company
#             total_users = Account.objects.filter(created_by=company_user).count()

#             # Active Conversations
#             conversations = Conversation.objects.filter(user=company_user)
#             active_conversations = conversations.count()
            
#             total_contacts = Contact.objects.filter(user=company_user).count()

#             # Messages sent/received
#             messages = ChatMessage.objects.filter(conversation__in=conversations)
#             messages_sent = messages.exclude(sender="User").count()
#             messages_received = messages.filter(sender="User").count()

#             # Orders count
#             orders = Order.objects.filter(user=company_user).count()

#             # Flows count
#             flows = Flow.objects.filter(created_by=company_user).count()
            
#             total_broadcasts = BroadcastGroup.objects.filter(user=company_user).count()

#             # Last Active time
#             user = company_user  # already Account object

#             last_active = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "—"
#             data.append({
#                 "company": company_user.full_name,
#                 "total_users": total_users,
#                 "total_broadcasts": total_broadcasts,
#                 "active_conversations": active_conversations,
#                 "total_contacts":total_contacts,
#                 "messages_sent": messages_sent,
#                 "messages_received": messages_received,
#                 "orders": orders,
#                 "flows": flows,
#                 "last_active": last_active
#             })

#         return Response(data)
