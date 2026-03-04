"""BaseIntegration ABC for data source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseIntegration(ABC):
    """Abstract base for data source connectors."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def source_type(self) -> str: ...

    @abstractmethod
    async def connect(self, config: dict[str, Any]) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def execute_query(self, query: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_schema_info(
        self,
        schemas: list[str] | None = None,
        databases: list[str] | None = None,
    ) -> str:
        """Return a text description of tables/columns for the LLM.

        Args:
            schemas: Optional list of schema names to include. None means all schemas.
            databases: Optional list of database names to include. None means all accessible databases.
        """
        ...

    @property
    def connected(self) -> bool:
        return False
