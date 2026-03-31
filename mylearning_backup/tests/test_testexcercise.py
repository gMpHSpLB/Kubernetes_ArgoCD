from exercises.testexcercise import fibonacci

def test_fibonacci_basic():
    assert fibonacci(5) == [0, 1, 1, 2, 3]

def test_fibonacci_zero():
    assert fibonacci(0) == []
