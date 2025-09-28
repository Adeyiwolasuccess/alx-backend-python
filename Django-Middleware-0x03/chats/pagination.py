from rest_framework.pagination import PageNumberPagination
from rest_framework import response

class DefaultPagination(PageNumberPagination):
    """
    Default Pagination: 20 items per page
    Override with ?page=<n> and optionally ?page_size=<m> max(100)
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "page_size": self.get_page_size(self.request) or self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })
