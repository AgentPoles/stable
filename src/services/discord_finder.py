"""
Service for finding proposals where different parties have varying voting choices.
Uses batch processing with pagination to efficiently find discords.
"""

import asyncio
import logging
from typing import List, Dict, Set
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices
from src.config import NUMBER_OF_PROPOSALS_PER_REQUEST

class RateLimiter:
    """Rate limiter for API calls.
    
    Snapshot API limits:
    - Free tier: 100 requests per minute
    - We make 2 API calls per batch
    """
    def __init__(self, max_requests: int = 100, time_window: float = 60.0):
        self.max_requests = max_requests  # 100 requests per minute
        self.time_window = time_window    # 60 seconds
        self.semaphore = asyncio.Semaphore(max_requests)
        self.last_reset = asyncio.get_event_loop().time()
        self.request_count = 0

    async def acquire(self):
        """Acquire a rate limit slot."""
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_reset >= self.time_window:
            self.request_count = 0
            self.last_reset = current_time
        
        if self.request_count >= self.max_requests:
            await asyncio.sleep(self.time_window - (current_time - self.last_reset))
            self.request_count = 0
            self.last_reset = asyncio.get_event_loop().time()
        
        await self.semaphore.acquire()
        self.request_count += 1

    def release(self):
        """Release a rate limit slot."""
        self.semaphore.release()

class DiscordFinderError(Exception):
    """Custom exception for DiscordFinder errors."""
    pass

class DiscordFinder:
    """Service for finding voting discords between parties.
    
    Attributes:
        client: SnapshotClient instance for API calls
        rate_limiter: RateLimiter instance for controlling API calls
    """
    def __init__(self, client: SnapshotClient):
        self.client = client
        self.rate_limiter = RateLimiter()

    async def find_discords(
        self, 
        space_ids: List[str], 
        parties: List[str], 
        max_retries: int = 3
    ) -> List[VaryingChoices]:
        """
        Find proposals where parties have different voting choices.
        
        Process:
        1. Fetch proposals from specified spaces
        2. For each proposal, fetch votes from all parties
        3. Filter for proposals with different choices
        4. Return list of proposals with discord
        
        Args:
            space_ids: List of space IDs to query
            parties: List of party addresses to check
            max_retries: Maximum number of retry attempts for failed requests
            
        Returns:
            List of VaryingChoices objects containing proposals with different choices
            
        Raises:
            DiscordFinderError: If there's an error fetching data
        """
        async with self.client as client:
            retries_left = max_retries
            all_proposals = []
            skip = 0
            
            while True:
                try:
                    await self.rate_limiter.acquire()
                    proposals = await client.fetch_proposals(space_ids, skip)
                    self.rate_limiter.release()
                    
                    if not proposals:
                        break
                        
                    all_proposals.extend(proposals)
                    skip += len(proposals)
                    
                except Exception as e:
                    self.rate_limiter.release()
                    logging.error(f"Error fetching proposals: {e}")
                    if retries_left <= 0:
                        raise DiscordFinderError(f"Failed to fetch proposals after retries: {e}")
                    retries_left -= 1
                    await asyncio.sleep(1)
                    continue
            
            if not all_proposals:
                return []
                
            proposal_ids = [p.id for p in all_proposals]
            varying_choices: List[VaryingChoices] = []
            skip = 0
            retries_left = max_retries
            
            while True:
                try:
                    await self.rate_limiter.acquire()
                    choices = await client.fetch_proposals_with_varying_choices(
                        proposal_ids, parties, skip
                    )
                    self.rate_limiter.release()
                    
                    if not choices:
                        break
                        
                    varying_choices.extend(choices)
                    skip += len(choices)
                    
                except Exception as e:
                    self.rate_limiter.release()
                    logging.error(f"Error fetching varying choices: {e}")
                    if retries_left <= 0:
                        raise DiscordFinderError(f"Failed to fetch varying choices after retries: {e}")
                    retries_left -= 1
                    await asyncio.sleep(1)
                    continue
                    
            return varying_choices