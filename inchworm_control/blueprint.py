# Redirect the outer package import to the existing blueprint implementation.
from .inchworm_control.blueprint import blueprint

__all__ = ["blueprint"]
