from flask import request, url_for
from sqlalchemy.orm import Query
from app.utils.constants import MAX_PAGE_SIZE


class PaginatedResult:
    """
    Class to standardize pagination results.
    Handles paginating SQLAlchemy queries and formatting response.
    """

    def __init__(self, query, page=1, per_page=10, error_out=False):
        """
        Initialize paginator with query and pagination parameters.

        Args:
            query: SQLAlchemy query object
            page: Current page number (default: 1)
            per_page: Items per page (default: 10)
            error_out: Whether to raise 404 when out of range (default: False)
        """
        self.query = query
        self.page = page
        self.per_page = per_page
        self.error_out = error_out

        # Get paginated items
        self.pagination = query.paginate(
            page=page, per_page=per_page, error_out=error_out
        )

    @property
    def items(self):
        """Get current page items"""
        return self.pagination.items

    @property
    def total(self):
        """Get total number of items"""
        return self.pagination.total

    def to_dict(self, schema, endpoint=None, **kwargs):
        """
        Convert paginated results to standardized dictionary response.

        Args:
            schema: Marshmallow schema to serialize items
            endpoint: Optional endpoint name for generating URLs
            **kwargs: Additional URL parameters to include in pagination links

        Returns:
            Dictionary with items and pagination metadata
        """
        # Serialize items with provided schema
        serialized_items = schema.dump(self.items)

        # Build pagination metadata
        pagination_data = {
            "total_items": self.pagination.total,
            "total_pages": self.pagination.pages,
            "current_page": self.page,
            "per_page": self.per_page,
            "has_next": self.pagination.has_next,
            "has_prev": self.pagination.has_prev,
        }

        # Add page navigation links if endpoint is provided
        if endpoint:
            pagination_data["links"] = self._get_pagination_links(endpoint, **kwargs)

        # Build final response
        return {"items": serialized_items, "pagination": pagination_data}

    def _get_pagination_links(self, endpoint, **kwargs):
        """
        Generate pagination links for different pages.
        """
        links = {}

        # Add parameters that should be included in all links
        params = kwargs.copy()
        params["per_page"] = self.per_page

        # First page link
        params["page"] = 1
        links["first"] = url_for(endpoint, **params, _external=True)

        # Last page link
        params["page"] = self.pagination.pages
        links["last"] = url_for(endpoint, **params, _external=True)

        # Previous page link
        if self.pagination.has_prev:
            params["page"] = self.page - 1
            links["prev"] = url_for(endpoint, **params, _external=True)

        # Next page link
        if self.pagination.has_next:
            params["page"] = self.page + 1
            links["next"] = url_for(endpoint, **params, _external=True)

        return links


def paginate(query, schema, endpoint=None, **kwargs):
    """
    Helper function to paginate a query and return standardized results.

    Args:
        query: SQLAlchemy query object
        schema: Marshmallow schema for serializing items
        endpoint: Optional endpoint name for generating navigation URLs
        **kwargs: Additional parameters (page, per_page, and URL params)

    Returns:
        Dictionary with items and pagination metadata
    """
    # Get pagination parameters from request or use defaults
    page = kwargs.pop("page", request.args.get("page", 1, type=int))
    per_page = kwargs.pop("per_page", request.args.get("per_page", 10, type=int))

    # Ensure reasonable limits for pagination
    per_page = min(max(per_page, 1), MAX_PAGE_SIZE)  # Between 1 and 100

    # Create paginated result
    paginated_result = PaginatedResult(query, page, per_page)

    # Return formatted result
    return paginated_result.to_dict(schema, endpoint, **kwargs)
