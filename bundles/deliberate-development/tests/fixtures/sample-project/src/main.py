"""Sample main module for testing."""


def hello(name: str) -> str:
    """Return a greeting.
    
    Args:
        name: The name to greet.
        
    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers.
    
    Args:
        a: First number.
        b: Second number.
        
    Returns:
        Sum of a and b.
    """
    return a + b


if __name__ == "__main__":
    print(hello("World"))
