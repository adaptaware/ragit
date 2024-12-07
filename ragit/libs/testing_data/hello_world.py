"""Completely dummy program."""


def add_ints(i, j):
    """Adds two integers."""
    return i + j


def main():
    """As dummy as it gets."""
    a = [1, 3, 9]
    b = [2, 31, 94]
    x = [add_ints(v1, v2) for v1, v2 in zip(a, b)]
    print(x)


if __name__ == '__main__':
    main()
