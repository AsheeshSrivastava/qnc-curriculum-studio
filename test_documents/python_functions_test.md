# Python Functions Guide

## Introduction to Functions

Functions are reusable blocks of code in Python that perform specific tasks. They help organize code, make it more readable, and reduce repetition.

## Defining Functions

In Python, functions are defined using the `def` keyword:

```python
def greet(name):
    """Return a greeting message."""
    return f"Hello, {name}!"

# Call the function
message = greet("Alice")
print(message)  # Output: Hello, Alice!
```

## Function Parameters

### Positional Parameters
Parameters passed in order:

```python
def add(a, b):
    return a + b

result = add(5, 3)  # a=5, b=3
```

### Keyword Parameters
Parameters passed by name:

```python
def describe_person(name, age, city):
    return f"{name} is {age} years old and lives in {city}"

info = describe_person(name="Bob", age=30, city="New York")
```

### Default Parameters
Parameters with default values:

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Uses default: Hello, Alice!
print(greet("Bob", "Hi"))          # Custom greeting: Hi, Bob!
```

### Variable Arguments (*args)
Accept any number of positional arguments:

```python
def sum_all(*numbers):
    return sum(numbers)

print(sum_all(1, 2, 3))        # 6
print(sum_all(1, 2, 3, 4, 5))  # 15
```

### Keyword Arguments (**kwargs)
Accept any number of keyword arguments:

```python
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=25, city="Boston")
```

## Return Values

### Single Return Value
```python
def square(x):
    return x ** 2
```

### Multiple Return Values
```python
def get_min_max(numbers):
    return min(numbers), max(numbers)

minimum, maximum = get_min_max([1, 5, 3, 9, 2])
```

### No Return Value
Functions without explicit return statement return `None`:

```python
def print_message(msg):
    print(msg)
    # Implicitly returns None
```

## Function Scope

### Local Variables
Variables defined inside a function are local:

```python
def my_function():
    local_var = 10  # Only accessible inside function
    return local_var
```

### Global Variables
Access global variables with `global` keyword:

```python
counter = 0

def increment():
    global counter
    counter += 1
```

## Lambda Functions

Anonymous functions for simple operations:

```python
# Regular function
def square(x):
    return x ** 2

# Lambda equivalent
square = lambda x: x ** 2

# Common use with map, filter
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
```

## Function Decorators

Modify function behavior without changing its code:

```python
def uppercase_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper

@uppercase_decorator
def greet(name):
    return f"hello, {name}"

print(greet("alice"))  # Output: HELLO, ALICE
```

## Best Practices

### 1. Use Descriptive Names
```python
# Bad
def f(x, y):
    return x + y

# Good
def calculate_sum(first_number, second_number):
    return first_number + second_number
```

### 2. Keep Functions Small
Each function should do one thing well. If a function is too long, break it into smaller functions.

### 3. Use Docstrings
Document what your function does:

```python
def calculate_area(radius):
    """
    Calculate the area of a circle.
    
    Args:
        radius (float): The radius of the circle
        
    Returns:
        float: The area of the circle
    """
    import math
    return math.pi * radius ** 2
```

### 4. Follow PEP 8
- Use lowercase with underscores for function names
- Use 4 spaces for indentation
- Add blank lines between functions
- Keep lines under 79 characters

### 5. Handle Errors Gracefully
```python
def divide(a, b):
    """Safely divide two numbers."""
    try:
        return a / b
    except ZeroDivisionError:
        return "Cannot divide by zero"
    except TypeError:
        return "Invalid input types"
```

### 6. Use Type Hints (Python 3.5+)
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    return a + b
```

## Common Patterns

### Factory Functions
```python
def create_multiplier(factor):
    def multiply(x):
        return x * factor
    return multiply

double = create_multiplier(2)
triple = create_multiplier(3)

print(double(5))  # 10
print(triple(5))  # 15
```

### Recursive Functions
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))  # 120
```

### Generator Functions
```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

for num in fibonacci(10):
    print(num, end=' ')  # 0 1 1 2 3 5 8 13 21 34
```

## Conclusion

Functions are fundamental to Python programming. They promote code reusability, improve readability, and make programs easier to maintain. Master these concepts to write better Python code!




