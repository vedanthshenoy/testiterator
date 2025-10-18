from testiterator import testiterator

def add(a, b):
    return a + b

@testiterator('n', [2,3,5], mock_dependencies=False)
def factorial(n):
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result = add(result, result * (i - 1))
    return result

def permutation(n, r):
    if r > n:
        return 0
    return factorial(n) // factorial(add(n, -r))

if __name__ == "__main__":
    print(factorial(0))