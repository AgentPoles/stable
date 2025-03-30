"""
Service for finding proposals where different parties have varying voting choices.
Uses batch processing with pagination to efficiently find discords.
"""

import asyncio
import logging
from typing import List
import aiohttp
from ..api.client import SnapshotClient
from ..models import VaryingChoices
from config import NUMBER_OF_PROPOSALS_PER_REQUEST

class RateLimiter:
    """Rate limiter for Snapshot API calls.
    
    Attributes:
        max_requests: Maximum number of requests allowed in time window
        time_window: Time window in seconds
        semaphore: Semaphore for controlling concurrent requests
    """
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.semaphore = asyncio.Semaphore(max_requests)
        self.last_reset = asyncio.get_event_loop().time()

    async def acquire(self):
        """Acquire a rate limit slot."""
        await self.semaphore.acquire()
        now = asyncio.get_event_loop().time()
        if now - self.last_reset >= self.time_window:
            self.semaphore = asyncio.Semaphore(self.max_requests)
            self.last_reset = now

    def release(self):
        """Release a rate limit slot."""
        self.semaphore.release()

class DiscordFinderError(Exception):
    """Custom exception for DiscordFinder errors."""
    pass

class DiscordFinder:
    """Service for finding voting discords between parties.
    
    Attributes:
        client: Snapshot API client
        logger: Logger instance
        rate_limiter: Rate limiter for API calls
    """
    def __init__(self, client: SnapshotClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60)

    async def find_discords(
        self, 
        space_ids: List[str], 
        parties: List[str],
        max_retries: int = 3
    ) -> List[VaryingChoices]:
        """
        Find proposals where parties have different voting choices.
        
        Process:
        1. Fetch batch of proposals with rate limiting
        2. Get votes for all parties in one query
        3. Return immediately if discords found
        4. Increment skip and continue if no discords
        5. Handle errors with retries and exponential backoff
        
        Args:
            space_ids: List of space IDs to query
            parties: List of party addresses to check
            max_retries: Maximum number of retry attempts for failed requests
            
        Returns:
            List of VaryingChoices objects containing proposals with different choices
            
        Raises:
            DiscordFinderError: If max retries exceeded or other errors occur
        """
        skip = 0
        retry_count = 0

        while True:
            try:
                await self.rate_limiter.acquire()
                proposals = await self.client.fetch_proposals(space_ids, skip)
                if not proposals:
                    self.logger.info("No more proposals found")
                    return []

                await self.rate_limiter.acquire()
                varying_choices = await self.client.fetch_proposals_with_varying_choices(
                    proposal_ids=[p.id for p in proposals],
                    voters=parties
                )

                if varying_choices:
                    self.logger.info(f"Found {len(varying_choices)} discords in batch")
                    return varying_choices

                skip += NUMBER_OF_PROPOSALS_PER_REQUEST
                retry_count = 0

            except aiohttp.ClientError as e:
                self.logger.error(f"Network error: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise DiscordFinderError("Max retries exceeded") from e
                await asyncio.sleep(2 ** retry_count)

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise DiscordFinderError("Failed to find discords") from e

            finally:
                self.rate_limiter.release() 