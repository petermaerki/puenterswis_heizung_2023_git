from zentral.util_transition import linear_transition, sine_transition


def test_transition():
    for x_given, y_expected in (
        (-3.0, 100.0),
        (5.0, 150.0),
        (13.0, 200.0),
    ):
        y = linear_transition(x=x_given, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0)
        assert abs(y - y_expected) < 0.01
        y = sine_transition(x=x_given, start_x=2.0, end_x=8.0, start_y=100.0, end_y=200.0)
        assert abs(y - y_expected) < 0.01


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
    matplot_reset()


if __name__ == "__main__":
    test_transition()
