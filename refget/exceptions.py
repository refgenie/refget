class InvalidSeqColError(Exception):
    """Object was not validated successfully according to schema."""

    def __init__(self, message, errors):
        super().__init__(message)
        self.message = message
        self.errors = errors

    def __str__(self):
        return f"InvalidSeqColError ({self.message}): {self.errors}"
