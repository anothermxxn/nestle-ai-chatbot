"""
Search module for Nestle AI Chatbot
"""

from .azure_search import AzureSearchClient
from .config import *

__all__ = ["AzureSearchClient"] 