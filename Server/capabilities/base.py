"""
Abstract Capability base class.
Subclass this to add a new capability to the framework.
"""

from abc import ABC, abstractmethod


class Capability(ABC):
    # Subclasses must set these class-level attributes.
    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, params: dict) -> str:
        """
        Execute the capability with the given params dict.
        Returns output as a plain string (passed back to the operator as the task result).
        """
