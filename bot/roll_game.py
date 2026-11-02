from dataclasses import dataclass
from math import isqrt


MAX_ROLL = 1_000_000

DIVISIBILITY_BONUSES = (
    (2, 1),
    (3, 1),
    (5, 2),
    (7, 2),
    (11, 3),
    (13, 3),
    (17, 4),
    (19, 4),
    (23, 4),
    (29, 4),
    (31, 4),
    (37, 4),
    (41, 5),
    (43, 5),
    (47, 5),
    (53, 5),
    (59, 5),
    (61, 5),
    (67, 6),
    (71, 6),
    (73, 6),
    (79, 6),
    (83, 6),
    (89, 6),
    (97, 6),
    (100, 6),
    (1_000, 10),
    (10_000, 13),
    (100_000, 17),
    (1_000_000, 20),
)

SPECIAL_NUMBERS = {
    42: ("The answer to life, the universe, and everything", 8),
    69: ("Nice", 10),
    911: ("Emergency number", 8),
    1_984: ("A very specific year", 8),
    420: ("Blaze it", 10),
    666: ("Number of the beast", 12),
    777: ("Lucky sevens", 14),
    8_008: ("Calculator spelling", 12),
    8_085: ("Calculator spelling", 12),
    80_085: ("Calculator spelling", 14),
    123_456: ("Perfect ascending sequence", 16),
    654_321: ("Perfect descending sequence", 16),
    1_337: ("Leetspeak", 12),
    13_337: ("Elite leetspeak", 16),
    42_069: ("The ultimate nice answer", 20),
    69_420: ("Nice blaze", 20),
    420_420: ("Double blaze", 24),
    666_666: ("Six sixes", 25),
    777_777: ("Six lucky sevens", 30),
    1_000_000: ("Maximum roll", 20),
}

RANKS = (
    (6, "Common"),
    (12, "Uncommon"),
    (20, "Rare"),
    (30, "Epic"),
    (45, "Legendary"),
    (80, "Mythic"),
    (160, "Cosmic"),
    (300, "Divine"),
    (600, "Celestial"),
    (1_000, "Singular"),
    (None, "Impossible"),
)

LENGTH_BONUSES = {
    2: 2,
    3: 5,
    4: 11,
    5: 22,
    6: 40,
}

CONSECUTIVE_BONUSES = {
    2: 2,
    3: 6,
    4: 14,
    5: 28,
    6: 50,
}

HILL_BONUSES = {
    3: 5,
    4: 12,
    5: 25,
    6: 45,
}

SPECIAL_ROLL_BONUSES = {
    0: ("Zero roll", 1_000),
    1: ("One roll", 800),
}

RANK_EMOJIS = {
    "Common": "⚪",
    "Uncommon": "🟢",
    "Rare": "🔵",
    "Epic": "🟣",
    "Legendary": "🟠",
    "Mythic": "🔴",
    "Cosmic": "🌌",
    "Divine": "✨",
    "Celestial": "🌠",
    "Singular": "👑",
    "Impossible": "💫",
}

BADGE_EMOJIS = {
    "One pair": "👯",
    "Two pairs": "🧩",
    "Three pairs": "🎭",
    "Three of a kind": "🎲",
    "Four of a kind": "🎯",
    "Five of a kind": "🌟",
    "Six of a kind": "💎",
    "Two triples": "🎭",
    "Four of a kind plus a pair": "🃏",
    "Full house": "🏠",
    "All digits are unique": "🔢",
    "Five or more unique digits": "🔣",
    "All digits the same": "🔁",
    "Palindrome": "🪞",
    "Repeated halves": "🪄",
    "Mirrored outer pairs": "🪞",
    "Alternating digit pattern": "🔀",
    "Two-digit balance": "⚖️",
    "Repeating two-digit block": "🔂",
    "Harshad number": "➗",
    "Tiny digit sum": "🤏",
    "Huge digit sum": "➕",
    "Prime digit sum": "💠",
    "Ascending consecutive digits": "📈",
    "Descending consecutive digits": "📉",
    "Contains a three-digit run": "🏃",
    "Strictly increasing digits": "📈",
    "Strictly decreasing digits": "📉",
    "Zigzag digits": "〰️",
    "All-even digits": "♻️",
    "All-odd digits": "🔆",
    "All prime digits": "💎",
    "Matching first and last digit": "🔗",
    "Double-zero ending": "🎯",
    "Round number": "⭕",
    "Contains a zero": "🕳️",
    "Prime number": "💎",
    "Perfect square": "🟦",
    "Perfect cube": "🧊",
    "Fibonacci number": "🌀",
    "Triangular number": "🔺",
    "Twin prime": "👯",
    "Emirp prime": "🔄",
    "Power of two": "⚡",
    "Power of ten": "🔟",
    "Factorial number": "❗",
    "Product of its digits": "✖️",
    "Automorphic number": "🪆",
    "Armstrong number": "💪",
    "Kaprekar number": "🧮",
    "Binary palindrome": "💻",
    "Perfect number": "✨",
    "Abundant number": "🎁",
    "Happy number": "😊",
    "Digit sum is a multiple of nine": "9️⃣",
    "Multiple of nine": "9️⃣",
    "Contains 67": "🔢",
    "Exactly 67": "🎰",
    "Single digit": "☝️",
    "Zero roll": "🕳️",
    "One roll": "🥇",
    "Unique roll": "👑",
}


def get_badge_emoji(trait: str) -> str:
    if trait in BADGE_EMOJIS:
        return BADGE_EMOJIS[trait]
    if trait.startswith("Divisible by "):
        return "➗"
    if "hill" in trait.lower():
        return "⛰️"
    if "valley" in trait.lower():
        return "🏞️"
    if "ascending" in trait.lower() or "increasing" in trait.lower():
        return "📈"
    if "descending" in trait.lower() or "decreasing" in trait.lower():
        return "📉"
    if "non-repeating" in trait.lower() or "unique" in trait.lower():
        return "🔢"
    if "single digit" in trait.lower():
        return "🔹"
    if trait in dict(SPECIAL_NUMBERS.values()):
        return "🌠"
    return "🏅"


@dataclass(frozen=True)
class RollResult:
    number: int
    score: int
    rank: str
    traits: tuple[tuple[str, int], ...]


def _is_prime(number: int) -> bool:
    if number < 2:
        return False
    if number % 2 == 0:
        return number == 2
    return all(number % divisor for divisor in range(3, isqrt(number) + 1, 2))


def _is_square(number: int) -> bool:
    root = isqrt(number)
    return root * root == number


def _is_cube(number: int) -> bool:
    root = round(number ** (1 / 3))
    return any(candidate ** 3 == number for candidate in range(max(0, root - 1), root + 2))


def _is_fibonacci(number: int) -> bool:
    def is_square(value: int) -> bool:
        root = isqrt(value)
        return root * root == value

    return is_square(5 * number * number + 4) or is_square(5 * number * number - 4)


def _is_happy(number: int) -> bool:
    seen = set()
    while number != 1 and number not in seen:
        seen.add(number)
        number = sum(int(digit) ** 2 for digit in str(number))
    return number == 1


def _is_triangular(number: int) -> bool:
    discriminant = 8 * number + 1
    root = isqrt(discriminant)
    return root * root == discriminant


def _proper_divisor_sum(number: int) -> int:
    if number <= 1:
        return 0
    total = 1
    for divisor in range(2, isqrt(number) + 1):
        if number % divisor == 0:
            total += divisor
            paired_divisor = number // divisor
            if paired_divisor != divisor:
                total += paired_divisor
    return total


def _is_kaprekar(number: int) -> bool:
    if number < 1:
        return False
    square = str(number * number)
    split_at = len(square) - len(str(number))
    left = int(square[:split_at] or "0")
    right = int(square[split_at:] or "0")
    return left + right == number


def score_roll(number: int) -> RollResult:
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("number must be an integer")
    if not 0 <= number <= MAX_ROLL:
        raise ValueError(f"number must be between 0 and {MAX_ROLL}")

    digits = str(number)
    digit_counts = {digit: digits.count(digit) for digit in set(digits)}
    digit_sum = sum(int(digit) for digit in digits)
    digit_product = 1
    for digit in digits:
        digit_product *= int(digit)
    traits: list[tuple[str, int]] = []

    def award(name: str, points: int) -> None:
        traits.append((name, points))

    if len(digits) == 1:
        award("Single digit", 180)
        special_roll = SPECIAL_ROLL_BONUSES.get(number)
        if special_roll is not None:
            award(*special_roll)

    if number:
        for divisor, points in DIVISIBILITY_BONUSES:
            if number % divisor == 0:
                award(f"Divisible by {divisor}", points)

    pairs = sum(count == 2 for count in digit_counts.values())
    triples = sum(count == 3 for count in digit_counts.values())
    quads = sum(count == 4 for count in digit_counts.values())
    five_kind = sum(count == 5 for count in digit_counts.values())
    six_kind = sum(count == 6 for count in digit_counts.values())
    if pairs == 1:
        award("One pair", 3)
    if pairs == 2:
        award("Two pairs", 10)
    if pairs == 3:
        award("Three pairs", 15)
    if triples == 1:
        award("Three of a kind", 7)
    if quads == 1:
        award("Four of a kind", 15)
    if five_kind == 1:
        award("Five of a kind", 22)
    if six_kind == 1:
        award("Six of a kind", 30)
    if triples == 2:
        award("Two triples", 20)
    if quads == 1 and pairs == 1:
        award("Four of a kind plus a pair", 22)
    if triples == 1 and pairs == 1:
        award("Full house", 14)

    if len(digits) > 1 and len(digit_counts) == len(digits):
        award("All digits are unique", 4)
        if len(digits) >= 5:
            award("Five or more unique digits", 8)
        award(f"{len(digits)}-digit non-repeating", LENGTH_BONUSES[len(digits)])
    if len(digits) > 1 and len(digit_counts) == 1:
        award("All digits the same", 25)

    if len(digits) > 1 and digits == digits[::-1]:
        award("Palindrome", 10 if len(digits) < 5 else 16)
    if len(digits) >= 4 and digits[:len(digits) // 2] == digits[len(digits) // 2:]:
        award("Repeated halves", 10)
    if len(digits) >= 4 and digits[:2] == digits[-2:][::-1]:
        award("Mirrored outer pairs", 7)
    if (
        len(digits) >= 4
        and len(set(digits[::2])) == 1
        and len(set(digits[1::2])) == 1
        and digits[0] != digits[1]
    ):
        award("Alternating digit pattern", 10)
    if len(digit_counts) == 2 and len(digits) >= 4 and all(count == len(digits) // 2 for count in digit_counts.values()):
        award("Two-digit balance", 8)
    if len(digits) >= 4 and len(set(digits[:2])) == 2 and digits == (digits[:2] * 3)[:len(digits)]:
        award("Repeating two-digit block", 10)

    if len(digits) > 1 and digit_sum and number % digit_sum == 0:
        award("Harshad number", 4)
    if len(digits) > 1 and digit_sum in (1, 2, 3, 5, 7):
        award("Tiny digit sum", 10)
    if digit_sum >= 40:
        award("Huge digit sum", 8)
    if _is_prime(digit_sum):
        award("Prime digit sum", 4)

    if len(digits) >= 3 and all(int(digits[index]) + 1 == int(digits[index + 1]) for index in range(len(digits) - 1)):
        award("Ascending consecutive digits", 20)
    elif len(digits) >= 3 and all(int(digits[index]) - 1 == int(digits[index + 1]) for index in range(len(digits) - 1)):
        award("Descending consecutive digits", 20)

    def has_consecutive_run(length: int, step: int) -> bool:
        return any(
            all(
                int(digits[start + offset + 1]) - int(digits[start + offset]) == step
                for offset in range(length - 1)
            )
            for start in range(len(digits) - length + 1)
        )

    for length in range(2, min(6, len(digits)) + 1):
        for step, adjective in (
            (1, "ascending"),
            (-1, "descending"),
        ):
            if has_consecutive_run(length, step):
                award(
                    f"{length}-digit consecutive {adjective} run",
                    CONSECUTIVE_BONUSES[length],
                )

    if len(digits) > 1:
        strictly_increasing = all(
            int(digits[index]) < int(digits[index + 1])
            for index in range(len(digits) - 1)
        )
        strictly_decreasing = all(
            int(digits[index]) > int(digits[index + 1])
            for index in range(len(digits) - 1)
        )
        if strictly_increasing:
            award(f"{len(digits)}-digit ascending digits", LENGTH_BONUSES[len(digits)])
        if strictly_decreasing:
            award(f"{len(digits)}-digit descending digits", LENGTH_BONUSES[len(digits)])

    if len(digits) >= 3:
        values = [int(digit) for digit in digits]
        for peak in range(1, len(values) - 1):
            if (
                all(values[index] < values[index + 1] for index in range(peak))
                and all(values[index] > values[index + 1] for index in range(peak, len(values) - 1))
            ):
                award(f"{len(digits)}-digit hill", HILL_BONUSES[len(digits)])
                break
        for valley in range(1, len(values) - 1):
            if (
                all(values[index] > values[index + 1] for index in range(valley))
                and all(values[index] < values[index + 1] for index in range(valley, len(values) - 1))
            ):
                award(f"{len(digits)}-digit valley", HILL_BONUSES[len(digits)])
                break

    three_digit_runs = (
        *(f"{value}{value + 1}{value + 2}" for value in range(7)),
        *(f"{value}{value - 1}{value - 2}" for value in range(9, 2, -1)),
    )
    if any(run in digits for run in three_digit_runs):
        award("Contains a three-digit run", 5)
    if len(digits) > 1 and all(int(digits[index]) < int(digits[index + 1]) for index in range(len(digits) - 1)):
        award("Strictly increasing digits", 8)
    if len(digits) > 1 and all(int(digits[index]) > int(digits[index + 1]) for index in range(len(digits) - 1)):
        award("Strictly decreasing digits", 8)
    if len(digits) >= 4 and all(
        (int(digits[index]) < int(digits[index + 1])) == (index % 2 == 0)
        for index in range(len(digits) - 1)
    ):
        award("Zigzag digits", 8)

    if len(digits) > 1 and all(int(digit) % 2 == 0 for digit in digits):
        award("All-even digits", 6)
    if len(digits) > 1 and all(int(digit) % 2 == 1 for digit in digits):
        award("All-odd digits", 6)
    if len(digits) > 1 and all(_is_prime(int(digit)) for digit in digits):
        award("All prime digits", 8)
    if digits[0] == digits[-1] and len(digits) > 1:
        award("Matching first and last digit", 4)
    if number > 0 and digits.endswith("00"):
        award("Double-zero ending", 8)
    elif number > 0 and digits.endswith("0"):
        award("Round number", 3)
    if len(digits) > 1 and "0" in digits:
        award("Contains a zero", 2)

    if _is_prime(number):
        award("Prime number", 12)
    if _is_square(number):
        award("Perfect square", 8)
    if _is_cube(number):
        award("Perfect cube", 12)
    if _is_fibonacci(number):
        award("Fibonacci number", 14)
    if _is_triangular(number):
        award("Triangular number", 8)
    if number > 2 and (
        (_is_prime(number) and _is_prime(number + 2))
        or (_is_prime(number - 2) and _is_prime(number))
    ):
        award("Twin prime", 12)
    if _is_prime(number) and _is_prime(int(digits[::-1])) and digits != digits[::-1]:
        award("Emirp prime", 16)
    if number > 0 and number & (number - 1) == 0:
        award("Power of two", 10)
    if number in (1, 10, 100, 1_000, 10_000, 100_000, 1_000_000):
        award("Power of ten", 10)
    if number in (1, 2, 6, 24, 120, 720, 5_040, 40_320, 362_880):
        award("Factorial number", 12)
    if digit_product == number and len(digits) > 1:
        award("Product of its digits", 10)
    if number > 0 and number == number * number % 10 ** len(digits):
        award("Automorphic number", 12)
    if number > 0 and sum(int(digit) ** len(digits) for digit in digits) == number:
        award("Armstrong number", 14)
    if _is_kaprekar(number):
        award("Kaprekar number", 12)
    binary_digits = format(number, "b")
    if len(binary_digits) > 1 and binary_digits == binary_digits[::-1]:
        award("Binary palindrome", 10)
    divisor_sum = _proper_divisor_sum(number)
    if number > 1 and divisor_sum == number:
        award("Perfect number", 20)
    elif number > 1 and divisor_sum > number:
        award("Abundant number", 4)
    if _is_happy(number):
        award("Happy number", 6)
    if number > 0 and sum(int(digit) for digit in digits) % 9 == 0:
        award("Digit sum is a multiple of nine", 5)
    if number > 0 and number % 9 == 0 and number % 10 != 0:
        award("Multiple of nine", 3)

    if "67" in digits:
        award("Contains 67", 6)
    if number == 67:
        award("Exactly 67", 20)
    if number in (0, 1):
        award("Unique roll", 100)
    special_number = SPECIAL_NUMBERS.get(number)
    if special_number is not None:
        award(*special_number)

    score = sum(points for _, points in traits)
    rank = next(label for threshold, label in RANKS if threshold is None or score < threshold)
    return RollResult(number=number, score=score, rank=rank, traits=tuple(traits))
