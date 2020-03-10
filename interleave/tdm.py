# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2020, The arXivDigest project"
''''''
from os.path import commonprefix
from random import choice
from collections import defaultdict


def TeamDraftMultileave(rankings, k):
    '''Teamdraft multileaving. Creates one list of recommendations from lists of recommendations from different systems'''
    L = []
    T = []
    # finds the common prefix for the lists
    prefix = commonprefix(list(rankings.values()))
    L.extend(prefix)
    T.extend([None for x in prefix])  # gives no team credit for common prefix
    # cache to avoid unnecessary "in" checks
    teamIndex = {k: 0 for k in rankings.keys()}
    availableTeams = [k for k, v in rankings.items() if len(v) > 0]
    # add all available teams to the list of teams that haven't added an article this round
    curTeams = list(availableTeams)
    while len(L) < k and availableTeams:
        # select a random team from the list of teams that havent selected this round
        team = choice(curTeams)
        # remove team from this round, so it wont be selected again before the rest have gotten their turn
        curTeams.remove(team)

        R = rankings[team]
        p = teamIndex[team]  # caches previos position to avoid rechecking
        # find highest rated item not already submited by another team
        while R[p] in L and p < k-1:
            p += 1
            if p >= len(R)-1:
                # remove team from list of available if all items are present in the results
                availableTeams.remove(team)
                break
        teamIndex[team] = p
        if not curTeams:  # if all teams have gotten their turn, start a new round
            curTeams = list(availableTeams)

        if R[p] not in L:  # if the item selected by the team is not in the result,
            L.append(R[p])  # add it,
            T.append(team)  # and give the team credit
    return L, T


class multiLeaver():
    '''Creates a multiLeaver, listlength decides how long the multileaved list will be, and systemsPerList decides how
    many systems will be multileaved per list. The multileaver will select random systems per user, but will prefer systems that 
    have been recommended less.'''

    def __init__(self, listLength, systemsPerList):
        self.listLength = listLength
        self.systemsPerList = systemsPerList
        self.impressions = defaultdict(int)

    def TDM(self, rankings):
        '''Teamdraft multileaving. Creates one list of recommendations from lists of recommendations from different systems
        input:{sysid:[articleids]}
        output:[articleIDs],[systemIDs]
        '''
        lists = {}
        # generate list of systems that can be selected from
        systems = {k: self.impressions[k] for k in rankings.keys()}
        # stop running if enough systems have been selected or if there are no more systems
        while len(lists) < self.systemsPerList and len(systems) > 0:
            # select systems with the lowest impression
            minVal = min(systems.values())
            minSys = [k for k, v in systems.items() if v == minVal]
            system = choice(minSys)
            # remove system when selected, to not select it twice
            del systems[system]
            lists[system] = rankings[system]
        for sys in lists.keys():  # increment impession for selected system
            self.impressions[sys] += 1
        return TeamDraftMultileave(lists, self.listLength)
