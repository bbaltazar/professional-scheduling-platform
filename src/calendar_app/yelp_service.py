"""
Yelp API integration service for workplace validation and search.

This module provides functionality to search for businesses using the Yelp API
and validate workplace information.
"""

import httpx
from typing import List, Optional, Dict, Any
from .config import settings
from .models import YelpBusinessResponse, YelpBusinessSearch


class YelpAPIError(Exception):
    """Custom exception for Yelp API errors."""

    pass


class YelpService:
    """Service class for interacting with the Yelp Fusion API."""

    def __init__(self):
        self.api_key = settings.YELP_API_KEY
        self.base_url = settings.YELP_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search_businesses(
        self, search_params: YelpBusinessSearch
    ) -> List[YelpBusinessResponse]:
        """
        Search for businesses using Yelp API.

        Args:
            search_params: Search parameters including term, location, etc.

        Returns:
            List of YelpBusinessResponse objects

        Raises:
            YelpAPIError: If API request fails or API key is missing
        """
        if not self.api_key:
            raise YelpAPIError(
                "Yelp API key is not configured. Please set YELP_API_KEY environment variable."
            )

        params = {
            "term": search_params.term,
            "location": search_params.location,
            "limit": search_params.limit,
        }

        if search_params.radius:
            params["radius"] = search_params.radius
        if search_params.categories:
            params["categories"] = search_params.categories

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/businesses/search",
                    headers=self.headers,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                businesses = []
                for business in data.get("businesses", []):
                    # Parse location information
                    location = business.get("location", {})
                    address_parts = location.get("display_address", [])
                    address = (
                        ", ".join(address_parts[:-1]) if len(address_parts) > 1 else ""
                    )

                    # Parse categories
                    categories = [
                        cat.get("title", "") for cat in business.get("categories", [])
                    ]

                    business_response = YelpBusinessResponse(
                        id=business.get("id", ""),
                        name=business.get("name", ""),
                        url=business.get("url", ""),
                        phone=business.get("phone"),
                        display_phone=business.get("display_phone"),
                        address=address,
                        city=location.get("city", ""),
                        state=location.get("state", ""),
                        zip_code=location.get("zip_code", ""),
                        country=location.get("country", "US"),
                        rating=business.get("rating"),
                        review_count=business.get("review_count"),
                        categories=categories,
                        image_url=business.get("image_url"),
                        is_closed=business.get("is_closed", False),
                        distance=business.get("distance"),
                    )
                    businesses.append(business_response)

                return businesses

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise YelpAPIError("Invalid Yelp API key")
            elif e.response.status_code == 400:
                raise YelpAPIError("Invalid search parameters")
            else:
                raise YelpAPIError(
                    f"Yelp API error: {e.response.status_code} - {e.response.text}"
                )
        except httpx.RequestError as e:
            raise YelpAPIError(f"Network error when calling Yelp API: {str(e)}")
        except Exception as e:
            raise YelpAPIError(f"Unexpected error: {str(e)}")

    async def get_business_details(
        self, business_id: str
    ) -> Optional[YelpBusinessResponse]:
        """
        Get detailed information about a specific business.

        Args:
            business_id: Yelp business ID

        Returns:
            YelpBusinessResponse object or None if not found

        Raises:
            YelpAPIError: If API request fails
        """
        if not self.api_key:
            raise YelpAPIError("Yelp API key is not configured")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/businesses/{business_id}",
                    headers=self.headers,
                    timeout=30.0,
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                business = response.json()

                # Parse location information
                location = business.get("location", {})
                address_parts = location.get("display_address", [])
                address = (
                    ", ".join(address_parts[:-1]) if len(address_parts) > 1 else ""
                )

                # Parse categories
                categories = [
                    cat.get("title", "") for cat in business.get("categories", [])
                ]

                return YelpBusinessResponse(
                    id=business.get("id", ""),
                    name=business.get("name", ""),
                    url=business.get("url", ""),
                    phone=business.get("phone"),
                    display_phone=business.get("display_phone"),
                    address=address,
                    city=location.get("city", ""),
                    state=location.get("state", ""),
                    zip_code=location.get("zip_code", ""),
                    country=location.get("country", "US"),
                    rating=business.get("rating"),
                    review_count=business.get("review_count"),
                    categories=categories,
                    image_url=business.get("image_url"),
                    is_closed=business.get("is_closed", False),
                    distance=business.get("distance"),
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise YelpAPIError("Invalid Yelp API key")
            else:
                raise YelpAPIError(
                    f"Yelp API error: {e.response.status_code} - {e.response.text}"
                )
        except httpx.RequestError as e:
            raise YelpAPIError(f"Network error when calling Yelp API: {str(e)}")
        except Exception as e:
            raise YelpAPIError(f"Unexpected error: {str(e)}")

    async def validate_business(self, yelp_business_id: str) -> bool:
        """
        Validate that a Yelp business ID exists and is active.

        Args:
            yelp_business_id: Yelp business ID to validate

        Returns:
            True if business exists and is not closed, False otherwise
        """
        try:
            business = await self.get_business_details(yelp_business_id)
            return business is not None and not business.is_closed
        except YelpAPIError:
            return False


# Global instance
yelp_service = YelpService()
