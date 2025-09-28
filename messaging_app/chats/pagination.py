from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    """
    Default Pagination: 20 items per page
    Override with ?page=<n> and optionally ?page_size=<m> max(100)
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
