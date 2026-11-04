from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Paginacion(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        esquema = super().get_paginated_response_schema(schema)
        esquema["properties"]["total_pages"] = {"type": "integer", "example": 3}
        return esquema
