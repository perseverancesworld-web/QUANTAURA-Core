"""Discrete Exterior Calculus kernel — incidence matrices and d²=0."""

from .complex2d import GridComplex2D, exterior_derivative, discrete_gradient, discrete_curl, discrete_div

__all__ = [
    "GridComplex2D",
    "exterior_derivative",
    "discrete_gradient",
    "discrete_curl",
    "discrete_div",
]
