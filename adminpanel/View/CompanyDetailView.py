# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from user_management.models import *
# import requests
# from django.shortcuts import render
# from ..pagination import ListPagination
 
 
 
# class CompanyDetailAPI(APIView):
#    permission_classes = [IsAuthenticated]
#    base_url = "https://graph.facebook.com"
 
#    def get(self,request):
#         data = []
#         company_id = request.GET.get('id')
#         companies = FacebookMetadata.objects.filter(user__created_by = None)
       
#         if company_id:
#             companies = companies.filter(id=company_id)
 
#         for company in companies:
#             company_user = company.user
#             waba_id = company.whatsapp_business_account_id
#             access_token = company.access_token
#             version = company.api_version
 
#             # Total Users created under this company
#             total_users = Account.objects.filter(created_by=company_user).count()
 
#             # Active Conversations
#             conversations = Conversation.objects.filter(user=company_user)
#             active_conversations = conversations.count()

#             total_contacts = Contact.objects.filter(user=company_user).count()
 
#             # Orders count
#             orders = Order.objects.filter(user=company_user).count()
 
#             # Flows count
#             flows = Flow.objects.filter(created_by=company_user).count()
           
#             total_broadcasts = BroadcastGroup.objects.filter(user=company_user).count()
 
#             total_templates = 0
#             if waba_id and access_token and version:
#                 try:
#                     url = f"{self.base_url}/{version}/{waba_id}/message_templates"
#                     headers = {
#                         "Authorization": f"Bearer {access_token}",
#                         "Content-Type": "application/json",
#                     }
#                     params = {"limit": 100000}
#                     response = requests.get(url, headers=headers, params=params)
#                     if response.status_code == 200:
#                         templates_data = response.json().get("data", [])
#                         total_templates = len(templates_data)
#                     else:
#                         total_templates = 0  # failed to fetch templates
#                 except Exception:
#                     print("Falied to get templates------------------")
#                     total_templates = 0
#             try:
#                wallet = Wallet.objects.get(user=company_user)
#                wallet_data = WalletSerializer(wallet)
#             except Wallet.DoesNotExist:
#                 wallet=[]

 
#             data.append({
#                 "company_name": company_user.full_name,
#                 "total_users": total_users,
#                 "total_broadcasts": total_broadcasts,
#                 "active_conversations": active_conversations,
#                 "total_contacts":total_contacts,
#                 "total_templates": total_templates,
#                 "wallet":wallet_data.data,
#                 "flows": flows,
#                 "orders" : orders,
#             })
 
#         return Response(data)
 

# class BroadcastDetailsView(APIView):

#     def get(self,request):
#         broadcast_details = []
#         company_id = request.GET.get('id')
#         companies = FacebookMetadata.objects.filter(user__created_by = None)
       
#         if company_id:
#             companies = companies.filter(id=company_id)
 
#         for company in companies:
#             company_user = company.user
#             broadcast = BroadcastGroup.objects.filter(user=company_user).order_by('-id')
#             for b in broadcast:
#                 broadcast_history = BroadcastHistory.objects.filter(broadcast=b)
#                 ALL_STATUSES = ["inquiry", "sent", "delivered", "read", "failed", "replied"]
#                 status_counts =(broadcast_history.exclude(status__isnull=True).values('status').annotate(count=models.Count('status')).order_by('status'))
#                 status_dict={s: 0 for s in ALL_STATUSES}
#                 status_dict.update({item['status']: item['count'] for item in status_counts})
#                 broadcast_details.append({
#                     "broadcast_group":b.title,
#                     "status":status_dict
#                 })

#         return Response({"broadcast_details":broadcast_details})

# class BroadcastListView(APIView):

#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         broadcast_company = FacebookMetadata.objects.filter(id=company)
#         broadcast_groups = BroadcastGroup.objects.filter(user=broadcast_company.first().user)
#         if search:
#             broadcast_groups = broadcast_groups.filter(
#                     Q(title__icontains=search)
#                     )
#         data=[]
#         for bg in broadcast_groups:
#             broadcast_history = BroadcastHistory.objects.filter(broadcast=bg)
#             data.append({
#                 'Title':bg.title,
#                 "Members":bg.contacts.all().count(),
#                 # 'Phone No.':bg.user.mobile,
#                 "Sent": broadcast_history.filter(status='sent').count(),
#                 "Delivered": broadcast_history.filter(status='delivered').count(),
#                 "Read": broadcast_history.filter(status='read').count(),
#                 "Replied": broadcast_history.filter(status='replied').count(),
#                 "Failed": broadcast_history.filter(status='failed').count(),
#                 "Inquiry": broadcast_history.filter(status='inquiry').count(),
#             })
#         paginator = ListPagination()
#         paginated_broadcasts = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_broadcasts)


# class ContactListView(APIView):
    
#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         contact_company = FacebookMetadata.objects.filter(id=company)
#         contacts = Contact.objects.filter(user=contact_company.first().user)
#         if search:
#             contacts = contacts.filter(
#                     Q(name__icontains=search) |
#                     Q(contact__icontains=search) |
#                     Q(city__icontains=search) |
#                     Q(tag__icontains=search)
#                     )
#         data=[]
#         for contact in contacts:
#             data.append({
#                "Name":contact.name,
#                "Contact":contact.contact,
#                "City":contact.city,
#                "Tag":contact.tag,
#             })
#         paginator = ListPagination()
#         paginated_contacts = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_contacts)
    
# class TemplateListView(APIView):
    
#     def get(self,request):
#         company = request.query_params.get('company','')
#         company_template = FacebookMetadata.objects.filter(id=company)
#         user = company_template.first().user()

# class UserListView(APIView):
    
#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         user_company = FacebookMetadata.objects.filter(id=company)
#         users = Account.objects.filter(created_by=user_company.first().user)
#         if search:
#             users = users.filter(
#                     Q(full_name__icontains=search) |
#                     Q(email__icontains=search) |
#                     Q(mobile__icontains=search) |
#                     Q(role__name__icontains=search)|
#                     Q(date_joined__icontains=search) 
#                     )
#         data = []
#         for user in users:
#             data.append({
#                 "Name":user.full_name,
#                 "E-mail":user.email,
#                 "Mobile":user.mobile,
#                 "Role":user.role.name if user.role else '',
#                 "Created At":user.date_joined.strftime("%d-%m-%Y")

#             })
#         paginator = ListPagination()
#         paginated_users = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_users)
    
# class ActiveContactList(APIView):

#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         active_contact_company = FacebookMetadata.objects.filter(id=company)
#         conversations = Conversation.objects.filter(user=active_contact_company.first().user)
#         if search:
#             conversations = conversations.filter(
#                     Q(user__full_name__icontains=search) |
#                     Q(user__email__icontains=search) |
#                     Q(contact__contact__icontains=search) |
#                     Q(last_active__icontains=search)
#                     )
#         data = []
#         for conversation in conversations:
#              data.append({
#                  "Name":conversation.user.full_name,
#                  "E-mail":conversation.user.email,
#                  "Mobile":conversation.contact.contact if conversation.contact else '',
#                  "Last Active": conversation.last_active.strftime("%d-%m-%Y, %H:%M:%S") if conversation.last_active else ''
#              })
#         paginator = ListPagination()
#         paginated_active_contacts = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_active_contacts)

# class OrderListView(APIView):

#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         order_company = FacebookMetadata.objects.filter(id=company)
#         orders = Order.objects.filter(user=order_company.first().user)
#         data=[]
#         if search:
#             orders = orders.filter(
#                     Q(order_id__icontains=search) |
#                     Q(customer_name__icontains=search) |
#                     Q(customer_phone__icontains=search) |
#                     Q(total_amount__icontains=search)|
#                     Q(sale_status__icontains=search) |
#                     Q(order_status__icontains=search)|
#                     Q(created_at__icontains=search)
#                     )
#         for order in orders:
#             data.append({
#                 "Order Id":order.order_id,
#                 "Customer Name":order.customer_name,
#                 "Customer Phone":order.customer_phone,
#                 f"Total Amount ({order.currency})":order.total_amount,
#                 "Sale Status":order.sale_status,
#                 "Order Status":order.order_status,
#                 "Created At":order.created_at.strftime("%d-%m-%Y, %H:%M:%S") if order.created_at else ''
#             })
#         paginator = ListPagination()
#         paginated_orders = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_orders)
    
# class FlowListView(APIView):

#     def get(self,request):
#         company = request.query_params.get('company','')
#         search = request.query_params.get('search','')
#         flow_company = FacebookMetadata.objects.filter(id=company)
#         flows = Flow.objects.filter(created_by=flow_company.first().user)
#         data=[]
#         if search:
#             print(search,'search')
#             if search in ['active','not active','inactive']:
#                 status_value = True if search.lower() == 'active' else False
#                 flows = flows.filter(status=status_value)
#             else:
#                 flows = flows.filter(
#                         Q(flow_name__icontains=search) |
#                         Q(status__icontains=search) |
#                         Q(type__icontains=search) |
#                         Q(created_at__icontains=search)
#                         )
#         for flow in flows:
#             data.append({
#                 "Flow Name":flow.flow_name,
#                 "Status":"Active" if flow.status else "Not Active",
#                 "Type":flow.type,
#                 "Created At":flow.created_at.strftime("%d-%m-%Y, %H:%M:%S") if flow.created_at else ''
#             })
#         paginator = ListPagination()
#         paginated_flows = paginator.paginate_queryset(data,request)

        
#         return paginator.get_paginated_response(paginated_flows)
