from __future__ import annotations


class AlreadyExistsError(Exception):
    """Represents an error that occurs when an entity already exists."""

    def __init__(self, message="The resource already exists."):
        """Initializes the AlreadyExistsError exception.

        Args:
            message (str): An optional custom message to describe the error.
        """
        self.message = message
        super().__init__(self.message)
