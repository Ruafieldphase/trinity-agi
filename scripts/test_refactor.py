"""
A demonstration script for basic Python programming concepts.

This module contains functions for generating greetings, performing calculations,
and formatting data, with a main execution block to showcase their usage.
"""


def get_greeting() -> str:
    """Returns a classic "Hello, world!" greeting.

    Returns:
        A greeting string.
    """
    return "Hello, world!"


def calculate_sum(num1: int, num2: int) -> int:
    """Calculates and returns the sum of two numbers.

    Args:
        num1: The first number.
        num2: The second number.

    Returns:
        The sum of the two numbers.
    """
    return num1 + num2


def format_numbers(*numbers: int) -> str:
    """Formats a sequence of numbers into a space-separated string.

    Args:
        *numbers: A variable number of integer arguments.

    Returns:
        A string with the numbers separated by spaces.
    """
    return " ".join(map(str, numbers))


def main() -> None:
    """Main entry point for the script to demonstrate function usage."""
    # 1. Get and print a greeting.
    greeting = get_greeting()
    print(greeting)

    # 2. Calculate a sum and print the result with context.
    sum_result = calculate_sum(10, 5)
    print(f"The sum of 10 and 5 is: {sum_result}")

    # 3. Format and print a sequence of numbers.
    numbers_to_print = (1, 2, 3, 4, 5)
    formatted_sequence = format_numbers(*numbers_to_print)
    print(f"Formatted sequence: {formatted_sequence}")


if __name__ == "__main__":
    main()