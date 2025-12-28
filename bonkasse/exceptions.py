"""
Custom exceptions for Bonkasse
"""


class DoNotRunDirectly(Exception):
    """Exception raised when attempting to run a module directly that should only be imported"""

    def __init__(self, module_name: str = ""):
        self.module_name = module_name
        message = f"Module '{module_name}' should not be run directly. Please run main.py instead."
        super().__init__(message)


if __name__ == "__main__":
    raise DoNotRunDirectly(__name__)