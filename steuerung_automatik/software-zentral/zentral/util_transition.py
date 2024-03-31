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


def selftest():
    for x_given, y_expected in (
        (-3.0, 100.0),
        (5.0, 150.0),
        (13.0, 200.0),
    ):
        y = linear_transition(
            x=x_given, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0
        )
        assert abs(y-y_expected) < 0.01
        y = sine_transition(
            x=x_given, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0
        )
        assert abs(y-y_expected) < 0.01

selftest()

def demo_plot():
    import matplotlib.pyplot as plt
    import numpy as np

    x_values = np.linspace(0.0, 10.0, 100)
    y_values_linear = [linear_transition(x) for x in x_values]
    y_values_sine = [sine_transition(x) for x in x_values]

    plt.plot(x_values, y_values_linear, label="linear_transition")
    plt.plot(x_values, y_values_sine, label="sine_transition")
    plt.xlabel("X")
    plt.ylabel("Y")
    # plt.title('Soft Transition Function')
    plt.grid(True)
    plt.legend()
    plt.show()
