import streamlit as st
from typing import Callable, Any
import functools


class ErrorHandler:
    """Centralized error handling for the application."""

    @staticmethod
    def handle_api_error(func: Callable) -> Callable:
        """Decorator to handle API errors consistently."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                st.error(
                    "Unable to connect to the server. Please check your connection."
                )
                return None
            except TimeoutError:
                st.error("Request timed out. Please try again.")
                return None
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                return None

        return wrapper

    @staticmethod
    def display_error(message: str, error_type: str = "error"):
        """Display error message with consistent formatting."""
        if error_type == "error":
            st.error(message)
        elif error_type == "warning":
            st.warning(message)
        elif error_type == "info":
            st.info(message)

    @staticmethod
    def validate_form_inputs(**kwargs) -> tuple[bool, str]:
        """Validate form inputs and return validation result."""
        for field_name, value in kwargs.items():
            if not value or not value.strip():
                return False, f"Please enter {field_name.replace('_', ' ')}"
        return True, ""

    @staticmethod
    def validate_password_match(
        password: str, confirm_password: str
    ) -> tuple[bool, str]:
        """Validate password confirmation."""
        if password != confirm_password:
            return False, "Passwords do not match"
        return True, ""
