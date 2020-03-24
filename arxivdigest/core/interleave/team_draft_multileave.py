# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import random
from collections import defaultdict
from collections import deque
from random import choice


class TeamDraftMultiLeaver:
    """A class that performs team draft multileaving of rankings from different
    systems.

    The multileaver will select systems at random for each multileaving,
    but systems that have fewer impressions will be preferred.
    This ensures that all systems will get a fair chance to be in approximately
    the same amount of multileavings.

    The multileaving is performed by letting systems propose elements in
    rounds, the order of the rounds are randomised each round. This is done
    until the multileaved rankings is the desired length, or the systems
    rankings are empty.

    Systems are give credit for elements they propose. The only exception for
    this is if there is a common prefix in the rankings included in the
    multileaving, then the common prefix is added to the multileaving
    without giving credit to any system.
    """

    def __init__(self, ranking_length, systems_per_ranking,
                 common_prefix=False):
        """Creates a team draft multileaver object.
        :param ranking_length: The desired length of the resulting ranking.
        :param systems_per_ranking: The desired number of systems multileaved
        per ranking.
        :param common_prefix: Whether common prefixes will give credit or not.
        """
        self.ranking_length = ranking_length
        self.systems_per_ranking = systems_per_ranking
        self.common_prefix = common_prefix
        self.impressions = defaultdict(int)

    def select_systems_for_multileaving(self, systems):
        """Selects systems randomly from `systems`, systems with fewer
        impressions will be prioritized.

        :param systems: A list of system ids eligible for multileaving.
        :return: A list of system ids that are candidates for multileaving.
        """
        impressions = {system: self.impressions[system] for system in systems}

        multileaving_candidates = []
        while (len(multileaving_candidates) < self.systems_per_ranking
               and len(impressions) > 0):
            # Select the systems with the fewest impression.
            candidate_systems = [system for system, impression in
                                 impressions.items()
                                 if impression == min(impressions.values())]
            # Pick random candidate from systems with the fewest impressions
            system = choice(candidate_systems)

            # Remove system when selected, to not select it twice.
            del impressions[system]
            multileaving_candidates.append(system)
            self.impressions[system] += 1

        return multileaving_candidates

    def team_draft_multileave(self, rankings):
        """Team draft multileaves rankings.

        :param rankings: A dictionary of system_id : ranking_list pairs.
        :return: Multileaved rankings list and system credit list
        """
        systems = [system for system, ranking in rankings.items() if ranking]
        systems = self.select_systems_for_multileaving(systems)
        rankings = {system: deque(rankings[system]) for system in systems}
        round_queue = None
        multileaved_ranking = []
        credit = []

        if self.common_prefix:
            multileaved_ranking.extend(common_prefix(rankings.values()))
            credit.extend([None for uncredited_element in multileaved_ranking])

        while len(multileaved_ranking) < self.ranking_length and systems:
            if not round_queue:  # New round, if no system in queue.
                round_queue = random.sample(systems, len(systems))
            system = round_queue.pop()
            for i, element in enumerate(rankings[system].copy()):
                if element in multileaved_ranking:
                    rankings[system].popleft()
                    continue
                else:
                    multileaved_ranking.append(element)
                    credit.append(system)
                    break
            if not rankings[system]:
                systems.remove(system)

        return multileaved_ranking, credit


def common_prefix(lists):
    """Given an iterable of iterables, returns the longest common prefix.
    Finds the first and last sublist when sorted lexicographically. Then
    compare how many elements these share, every sublist between these will
    share at least this common prefix."""
    first_sublist = list(min(lists))
    last_sublist = list(max(lists))
    for i, element in enumerate(first_sublist):
        if element != last_sublist[i]:
            return first_sublist[:i]
    return first_sublist
