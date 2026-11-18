"""Type-strict equality for already bounded JSON values."""


def exact_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(right, dict):
        return left.keys() == right.keys() and all(
            exact_json(left[k], v) for k, v in right.items()
        )
    if isinstance(right, list):
        return len(left) == len(right) and all(
            exact_json(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right
