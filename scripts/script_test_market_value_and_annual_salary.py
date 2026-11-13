
import math


def calculate_annual_salary(overall: int) -> float:
    """
    Estimates the annual salary in PES 2021.

    Model: Overall as the only variable.
    Result: Euros per year.
    """
    return 0.3007 * math.exp(0.1989 * overall)


def calculate_market_value(
    overall: int,
    age: int,
    reputation: int
) -> float:
    """
    Estimates the market value in PES 2021.

    Exploratory regression model:
    Overall + age + age squared + reputation.

    Formula:
    ln(MV) = 9.984
             + 0.1141 * Overall
             - 0.4031 * Age
             + 0.0065 * Age^2
             + 0.6097 * Reputation

    Result: Euros.

    WARNING:
    The model has limited explanatory power (R² ≈ 59.6%).
    It should not be used for automatic bulk editing
    without further validation.
    """
    exponent = (
        9.984
        + 0.1141 * overall
        - 0.4031 * age
        + 0.0065 * (age ** 2)
        + 0.6097 * reputation
    )

    return math.exp(exponent)


# Example usage
if __name__ == "__main__":
    overall = 90
    age = 27
    reputation = 8

    annual_salary = calculate_annual_salary(overall)

    market_value = calculate_market_value(
        overall,
        age,
        reputation
    )

    print(f"Estimated annual salary: €{annual_salary:,.2f}")
    print(f"Estimated market value: €{market_value:,.2f}")
