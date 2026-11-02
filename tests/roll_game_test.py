import unittest

from bot.roll_game import MAX_ROLL, RANK_EMOJIS, get_badge_emoji, score_roll


class RollGameTests(unittest.TestCase):
    def test_roll_score_includes_multiple_traits_and_rank(self):
        result = score_roll(2112)

        self.assertEqual(result.number, 2112)
        self.assertIn(("Two pairs", 10), result.traits)
        self.assertIn(("Palindrome", 10), result.traits)
        self.assertIn(("Harshad number", 4), result.traits)
        self.assertEqual(result.score, sum(points for _, points in result.traits))
        self.assertEqual(result.rank, "Mythic")

    def test_special_numbers_get_rarity_bonuses(self):
        result = score_roll(67)

        self.assertIn(("Exactly 67", 20), result.traits)
        self.assertIn(("Contains 67", 6), result.traits)
        self.assertIn(("Divisible by 67", 6), result.traits)

    def test_all_repeated_digits_are_scored(self):
        result = score_roll(777777)

        self.assertIn(("All digits the same", 25), result.traits)
        self.assertIn(("Six of a kind", 30), result.traits)
        self.assertIn(("Six lucky sevens", 30), result.traits)

    def test_sequence_and_unique_digit_patterns_are_scored(self):
        result = score_roll(123456)

        self.assertIn(("Ascending consecutive digits", 20), result.traits)
        self.assertIn(("Contains a three-digit run", 5), result.traits)
        self.assertIn(("Strictly increasing digits", 8), result.traits)
        self.assertIn(("Five or more unique digits", 8), result.traits)

    def test_repeating_block_patterns_are_scored(self):
        result = score_roll(121212)

        self.assertIn(("Alternating digit pattern", 10), result.traits)
        self.assertIn(("Repeating two-digit block", 10), result.traits)
        self.assertIn(("Two-digit balance", 8), result.traits)

    def test_classic_number_properties_are_scored(self):
        square_and_fibonacci = score_roll(144)
        prime = score_roll(104729)
        automorphic = score_roll(76)
        armstrong = score_roll(153)
        kaprekar = score_roll(45)
        perfect = score_roll(28)

        self.assertIn(("Perfect square", 8), square_and_fibonacci.traits)
        self.assertIn(("Fibonacci number", 14), square_and_fibonacci.traits)
        self.assertIn(("Prime number", 12), prime.traits)
        self.assertIn(("Automorphic number", 12), automorphic.traits)
        self.assertIn(("Armstrong number", 14), armstrong.traits)
        self.assertIn(("Kaprekar number", 12), kaprekar.traits)
        self.assertIn(("Perfect number", 20), perfect.traits)

    def test_twin_prime_and_binary_palindrome_are_scored(self):
        twin_prime = score_roll(11)
        binary_palindrome = score_roll(585)

        self.assertIn(("Twin prime", 12), twin_prime.traits)
        self.assertIn(("Binary palindrome", 10), binary_palindrome.traits)

    def test_special_number_has_custom_bonus(self):
        result = score_roll(69_420)

        self.assertIn(("Nice blaze", 20), result.traits)

    def test_zero_and_one_get_ultra_rare_bonuses(self):
        zero = score_roll(0)
        one = score_roll(1)

        self.assertIn(("Single digit", 180), zero.traits)
        self.assertIn(("Zero roll", 1_000), zero.traits)
        self.assertIn(("Unique roll", 100), zero.traits)
        self.assertIn(("One roll", 800), one.traits)
        self.assertGreaterEqual(zero.score, 1_000)
        self.assertGreaterEqual(one.score, 1_000)
        self.assertEqual(zero.rank, "Impossible")
        self.assertEqual(one.rank, "Impossible")

    def test_single_digit_rolls_are_rewarded(self):
        result = score_roll(7)

        self.assertIn(("Single digit", 180), result.traits)
        self.assertNotIn(("Zero roll", 1_000), result.traits)
        self.assertNotIn(("One roll", 800), result.traits)

    def test_length_scaled_patterns_cover_two_through_six_digits(self):
        two_digit = score_roll(12)
        three_digit = score_roll(123)
        four_digit = score_roll(1234)
        five_digit = score_roll(12345)
        six_digit = score_roll(123456)

        self.assertIn(("2-digit ascending digits", 2), two_digit.traits)
        self.assertIn(("2-digit consecutive ascending run", 2), two_digit.traits)
        self.assertIn(("3-digit consecutive ascending run", 6), three_digit.traits)
        self.assertIn(("4-digit non-repeating", 11), four_digit.traits)
        self.assertIn(("5-digit consecutive ascending run", 28), five_digit.traits)
        self.assertIn(("6-digit ascending digits", 40), six_digit.traits)
        self.assertIn(("6-digit consecutive ascending run", 50), six_digit.traits)

    def test_hills_valleys_and_descending_patterns(self):
        hill = score_roll(132)
        valley = score_roll(312)
        descending = score_roll(654321)

        self.assertIn(("3-digit hill", 5), hill.traits)
        self.assertIn(("3-digit valley", 5), valley.traits)
        self.assertIn(("6-digit descending digits", 40), descending.traits)
        self.assertIn(("6-digit consecutive descending run", 50), descending.traits)

    def test_every_badge_and_rank_has_an_emoji(self):
        for number in (0, 1, 2, 132, 123456, 654321, 1_000_000):
            for trait, _ in score_roll(number).traits:
                self.assertTrue(get_badge_emoji(trait), trait)
        self.assertTrue(all(RANK_EMOJIS.values()))

    def test_roll_score_rejects_out_of_range_numbers(self):
        for number in (-1, MAX_ROLL + 1):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    score_roll(number)

    def test_roll_score_rejects_non_integer_numbers(self):
        with self.assertRaises(TypeError):
            score_roll(1.5)

    def test_roll_score_accepts_range_boundaries(self):
        zero = score_roll(0)
        self.assertEqual(zero.number, 0)
        self.assertNotIn(("All digits are unique", 4), zero.traits)
        self.assertNotIn(("All digits the same", 25), zero.traits)
        self.assertEqual(score_roll(MAX_ROLL).number, MAX_ROLL)


if __name__ == "__main__":
    unittest.main()
