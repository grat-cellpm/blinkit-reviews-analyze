"""Pluggable review sources for future App Store / Reddit ingestion."""

from abc import ABC, abstractmethod
from typing import Any


class ReviewSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, count: int | None = None) -> list[dict[str, Any]]:
        """Return normalized review dicts with keys:
        review_id, user_name, content, rating, thumbs_up, review_date, reply_content, source
        """


class GooglePlayReviewSource(ReviewSource):
    name = "google_play"

    def fetch(self, count: int | None = None) -> list[dict[str, Any]]:
        from app.services.ingestion import GooglePlaySource

        return GooglePlaySource().fetch(count)


# Future:
# class AppStoreReviewSource(ReviewSource): ...
# class RedditReviewSource(ReviewSource): ...
