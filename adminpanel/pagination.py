from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
 
 
class PaginationWithPageCount(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'rows_per_page': self.page_size,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'status': True,
            'results': data,
        })
 
 
class ListPagination(PaginationWithPageCount):
    page_size = 50
    max_page_size = 25
    page_query_param = 'page'    
   
    def get_page_size(self, request):
        # Override get_page_size to allow dynamic setting based on query parameters
        page_size = super().get_page_size(request)
        if 'row_per_page' in request.query_params:
            page_size = int(request.query_params['row_per_page'])
        return page_size
    
class PostListPagination(PaginationWithPageCount):
    page_size = 50
    max_page_size = 25
    page_query_param = 'page'    
   
    def get_page_size(self, request):
        # Override get_page_size to allow dynamic setting based on query parameters
        page_size = super().get_page_size(request)
        if 'row_per_page' in request.data:
            page_size = int(request.data['row_per_page'])
        return page_size
    
    def paginate_queryset(self, queryset, request, view=None):
        # Allow 'page' from body
        if self.page_query_param in request.data and self.page_query_param not in request.query_params:
            # Copy existing GET params
            mutable_get = request._request.GET.copy()
            mutable_get[self.page_query_param] = str(request.data[self.page_query_param])
            request._request.GET = mutable_get  # replace the raw Django GET dict

        return super().paginate_queryset(queryset, request, view)