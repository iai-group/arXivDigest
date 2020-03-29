# -*- coding: utf-8 -*-
import unittest
from collections import Counter

from arxivdigest.core.interleave.team_draft_multileave import TeamDraftMultiLeaver


class TestTeamDraftMultileaver(unittest.TestCase):
    def test_position_distribution_probabilistically(self):
        """Tests that the distribution of positions given to systems is
        approximately equal between systems. This function may fail very
        rarely because of the probabilistic nature, this is why the failure
        threshold is set a bit high at  0.025. Increasing the number of
        simulations could mitigate this at the cost of execution time."""
        ranking_length = 9
        rankings = {1: [1, 2, 3], 2: [11, 12, 13], 3: [21, 22, 23]}
        multileaver = TeamDraftMultiLeaver(ranking_length, 3)

        times_each_position = {i: Counter() for i in range(ranking_length)}
        n = 10000
        for i in range(0, n):
            ranking, credit = multileaver.team_draft_multileave(rankings)
            for pos, system in enumerate(credit):
                times_each_position[pos].update([system])

        for position, times_position in times_each_position.items():
            for system, count in times_position.items():
                self.assertAlmostEqual(count/n, 1 / len(rankings), delta=0.025)

    def test_ranking_common_prefix(self):
        """Test that the common prefix is kept, and ranking interleaved
        normally after the common prefix."""
        common_prefix = [1, 2, 3, 4]
        rankings = {
            1: common_prefix + [5, 6, 7, 8, 9, 10],
            2: common_prefix + [15, 16, 17, 18, 19, 20],
            3: common_prefix + [25, 26, 27, 28, 29, 30]
        }
        multileaver = TeamDraftMultiLeaver(10, 3, common_prefix=True)
        ranking, credit = multileaver.team_draft_multileave(rankings)
        # Assert that the common prefix is correct
        self.assertEqual(ranking[:4], common_prefix)

        # Assert that the correct values are multileaved after common prefix,
        # in the first round. Order cannot be validated because the order is
        # random
        self.assertIn(rankings[1][4], ranking[4:7])
        self.assertIn(rankings[2][4], ranking[4:7])
        self.assertIn(rankings[3][4], ranking[4:7])
        # Check that the correct values are multileaved in the second round
        self.assertIn(rankings[1][5], ranking[7:10])
        self.assertIn(rankings[2][5], ranking[7:10])
        self.assertIn(rankings[3][5], ranking[7:10])

    def test_credit_with_common_prefix(self):
        """Test that no credit are awarded for the common prefix, and that
        credits are awarded normally after the common prefix."""
        common_prefix = [1, 2, 3, 4]
        rankings = {
            1: common_prefix + [5, 6, 7, 8, 9, 10],
            2: common_prefix + [15, 16, 17, 18, 19, 20],
            3: common_prefix + [25, 26, 27, 28, 29, 30]
        }
        multileaver = TeamDraftMultiLeaver(10, 3, common_prefix=True)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        # Assert that no credit is given for common prefix
        self.assertEqual(credit[:4], [None, None, None, None])
        # Assert credit is given to correct system after common prefix
        for element, credit in zip(ranking, credit):
            if credit is not None:
                self.assertIn(element, rankings[credit])

    def test_no_duplicates_output_ranking(self):
        """Test that an element is not present more than once in the
        resulting ranking."""
        rankings = {
            1: list(range(0, 1000)),
            2: list(range(0, 1000)),
            3: list(range(0, 1000))
        }
        multileaver = TeamDraftMultiLeaver(3000, 3)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        self.assertEqual(len(ranking), len(set(ranking)))

    def test_order_of_output_ranking(self):
        """Tests that elements occur in the order in the result set as the
        systems ranked them."""
        rankings = {
            1: list(range(0, 1000)),
            2: list(range(1000, 2000)),
            3: list(range(2000, 3000))
        }
        multileaver = TeamDraftMultiLeaver(3000, 3)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        for element, system in zip(ranking, credit):
            self.assertEqual(element, rankings[system].pop(0))

    def test_systems_get_only_one_element_per_round(self):
        """Tests that a system never gets to recommend more than one element
        per recommendation round."""
        rankings = {
            1: list(range(0, 1000)),
            2: list(range(1000, 2000)),
            3: list(range(2000, 3000))
        }
        multileaver = TeamDraftMultiLeaver(3000, 3)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        for i in range(0, len(credit), 3):
            self.assertEqual(set(rankings.keys()), set(credit[i:i+3]))

    def test_credit_to_correct_system(self):
        """Test that the correct system is given credit for a element."""
        rankings = {
            1: list(range(0, 1000)),
            2: list(range(1000, 2000)),
            3: list(range(2000, 3000))
        }
        multileaver = TeamDraftMultiLeaver(3000, 3)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        for element, credit in zip(ranking, credit):
            self.assertIn(element, rankings[credit])

    def test_max_output_ranking_length(self):
        """Test that the result length does not exceed the maximum length."""
        rankings = {1: [1, 2, 3, 4], 2: [11, 12, 13, 14], 3: [21, 22, 23, 24]}

        ranking_length = 10
        multileaver = TeamDraftMultiLeaver(ranking_length, 3)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        self.assertEqual(len(ranking), ranking_length)

    def test_maximal_number_of_interleaved_systems(self):
        """Test that the number of systems each interleaving does not exceed
        the configured maximum amount of systems per interleaving."""
        rankings = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3], 4: [1, 2, 3]}
        max_systems = 3
        multileaver = TeamDraftMultiLeaver(100, max_systems)
        ranking, credit = multileaver.team_draft_multileave(rankings)

        self.assertEqual(len(set(credit)), max_systems)

    def test_approximately_equal_representation(self):
        """Tests that each system gets selected for interleaving
        approximately the same amount of times for interleaving over a large
        amount of interleavings."""
        rankings = {1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}
        multileaver = TeamDraftMultiLeaver(3, 3)
        representations = Counter()
        for i in range(0, 1000):
            ranking, credit = multileaver.team_draft_multileave(rankings)
            representations.update(set(credit))

        for representation in representations.values():
            self.assertAlmostEqual(representations[1], representation, delta=1)


if __name__ == '__main__':
    unittest.main()
