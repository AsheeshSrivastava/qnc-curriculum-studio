"""Prioritized Tavily search for research-grade content retrieval."""

from typing import Any, Optional

from tavily import TavilyClient

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Domain prioritization for Python research
PRIORITY_DOMAINS = {
    "tier_1": [
        "python.org",
        "docs.python.org",
        "peps.python.org",
        "pypi.org",
    ],  # Official Python
    "tier_2": [
        "arxiv.org",
        "ieee.org",
        "acm.org",
        "scholar.google.com",
        "dl.acm.org",
    ],  # Academic
    "tier_3": [
        "realpython.com",
        "stackoverflow.com",
        "github.com",
        "python.plainenglish.io",
        "towardsdatascience.com",
    ],  # Quality community
}


class TavilyResearchClient:
    """Enhanced Tavily client with domain prioritization for research."""

    def __init__(self, api_key: str) -> None:
        self.client = TavilyClient(api_key=api_key)
        self.settings = get_settings()

    async def search_prioritized(
        self,
        query: str,
        depth: str = "standard",
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Execute prioritized search across official, academic, and quality sources.

        Args:
            query: Search query
            depth: Research depth (quick/standard/deep)
            max_results: Maximum total results to return

        Returns:
            List of search results with priority scoring
        """
        all_results = []

        # Determine search strategy based on depth
        if depth == "quick":
            # Quick: Official sources only
            searches = [("tier_1", 5)]
        elif depth == "standard":
            # Standard: Official + Academic
            searches = [("tier_1", 5), ("tier_2", 3)]
        else:  # deep
            # Deep: All tiers
            searches = [("tier_1", 5), ("tier_2", 3), ("tier_3", 5)]

        # Execute prioritized searches
        for tier, limit in searches:
            try:
                results = await self._search_tier(query, tier, limit)
                all_results.extend(results)
                
                logger.info(
                    "tavily.search.tier_complete",
                    tier=tier,
                    results_count=len(results),
                    query=query[:50],
                )
            except Exception as e:
                logger.warning(
                    "tavily.search.tier_failed",
                    tier=tier,
                    error=str(e),
                    query=query[:50],
                )
                continue

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        # Limit to max_results
        final_results = unique_results[:max_results]

        logger.info(
            "tavily.search.complete",
            total_results=len(final_results),
            tiers_searched=len(searches),
            depth=depth,
        )

        return final_results

    async def _search_tier(
        self,
        query: str,
        tier: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        Search within a specific domain tier.

        Args:
            query: Search query
            tier: Domain tier (tier_1, tier_2, tier_3)
            limit: Maximum results for this tier

        Returns:
            List of search results with tier metadata
        """
        domains = PRIORITY_DOMAINS.get(tier, [])
        if not domains:
            return []

        # Build site-restricted query
        site_filters = " OR ".join([f"site:{domain}" for domain in domains])
        enhanced_query = f"{query} ({site_filters})"

        try:
            # Execute Tavily search
            response = self.client.search(
                query=enhanced_query,
                max_results=limit,
                search_depth="advanced",  # Use advanced search for better quality
                include_domains=domains,  # Restrict to priority domains
            )

            results = response.get("results", [])

            # Add tier metadata
            for result in results:
                result["priority_tier"] = tier
                result["tier_rank"] = self._get_tier_rank(tier)

            return results

        except Exception as e:
            logger.error(
                "tavily.search.tier_error",
                tier=tier,
                error=str(e),
                exc_info=True,
            )
            return []

    def _get_tier_rank(self, tier: str) -> int:
        """Return numeric rank for tier (lower = higher priority)."""
        tier_ranks = {"tier_1": 1, "tier_2": 2, "tier_3": 3}
        return tier_ranks.get(tier, 99)

    def search_general(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Fallback to general Tavily search (synchronous).

        Used when prioritized search fails or for non-Python topics.
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
            )
            return response.get("results", [])
        except Exception as e:
            logger.error(
                "tavily.search.general_error",
                error=str(e),
                exc_info=True,
            )
            return []



