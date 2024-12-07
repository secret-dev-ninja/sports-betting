from decimal import Decimal, getcontext
import math

def get_uname(text: str) -> str:
  return text.lower().replace('(', '').replace(')', '').replace(' ', '-').replace('---', '-')

def get_sum_vig(type: str, odds: dict) -> str:
  if type == "moneyline":
    result = 1/float(odds[0]) + 1/float(odds[1]) + 1/float(odds[2]) - 1
  elif type == "spread":
    result = 1/float(odds[0]) + 1/float(odds[1]) - 1
  elif type == "total":
    result = 1/float(odds[0]) + 1/float(odds[1]) - 1
  else:
    raise ValueError(f"Invalid type: {type}")
    
  return str(round(result, 2))

def calculate_vig_free_odds(odds_1: float, odds_2: float):
# Determine the longshot and favorite odds
  odds_longshot = max(odds_1, odds_2)
  odds_favorite = min(odds_1, odds_2)

  # Calculate probabilities
  p = 1 / odds_favorite
  q = 1 / odds_longshot

  # Calculate vig-free longshot odds using the formula
  longshot_vig_free = math.log((1 - p) / q) / math.log((1 - q) / p) + 1

  # Calculate vig-free favorite odds
  favorite_vig_free = 1 / (1 - 1 / longshot_vig_free)

  # Ensure the result maintains the input order
  result = (round(longshot_vig_free, 3), round(favorite_vig_free, 3))

  return result if odds_1 > odds_2 else result[::-1]


def get_no_vig_odds_multiway(odds: list):
  """
  :param odds: List of original odds for a multi-way market.
  :return: Tuple of no-vig (fair) odds calculated using the iterative method.
  """
  getcontext().prec = 10
  odds = [Decimal(o) for o in odds]

  c, target_overround, accuracy, current_error = 1, 0, 3, 1000
  max_error = (10 ** (-accuracy)) / 2

  fair_odds = list()
  while current_error > max_error:
    f = - 1 - target_overround
    for o in odds:
      f += (Decimal(1) / (o)) ** c

    f_dash = 0
    for o in odds:
      f_dash += ((Decimal(1) / o) ** c) * (-Decimal(math.log(o)))

    h = -f / f_dash
    c = c + h

    t = 0
    for o in odds:
      t += (Decimal(1) / o) ** c
    current_error = abs(t - 1 - target_overround)

  fair_odds = list()
  for o in odds:
    fair_odds.append(round(o ** c, 3))

  return tuple(fair_odds)