import math


def linear_transition(x=5.0, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0):
    assert start_x < end_x
    faktor_0_1 = min(max(x - start_x, 0) / (end_x - start_x), 1.0)
    return faktor_0_1 * end_y + (1 - faktor_0_1) * start_y


def sine_transition(x=5.0, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0):
    assert start_x < end_x
    faktor_0_1 = min(max(x - start_x, 0) / (end_x - start_x), 1.0)
    factor_sin = math.sin((faktor_0_1 - 0.5) * math.pi) * 0.5 + 0.5
    return factor_sin * end_y + (1 - factor_sin) * start_y
