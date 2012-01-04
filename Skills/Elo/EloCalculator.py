from Skills.SkillCalculator import SkillCalculator
from Skills.Numerics.Range import Range
from Skills.Teams import Teams
from Skills.Elo.EloRating import EloRating
from Skills.Team import Team

class EloCalculator(SkillCalculator):

    def __init__(self, k_factor=EloRating.DEFAULT_K_FACTOR):
        SkillCalculator.__init__(self, Range.exactly(2), Range.exactly(1))
        self.k_factor = k_factor

    def calculate_new_ratings(self, game_info, teams):
        self.validate_team_count_and_players_count_per_team(teams)

        # ensure sorted by rank
        teams.sort()

        winner, winner_rating = teams[0].player_rating()[0]
        loser, loser_rating = teams[1].player_rating()[0]

        return Teams(Team(winner, self.calculate_new_rating(game_info,
                                                            winner_rating,
                                                            loser_rating,
                                                            teams.comparison())),
                     Team(loser, self.calculate_new_rating(game_info,
                                                           loser_rating,
                                                           winner_rating,
                                                           teams.comparison(False))))

    def calculate_new_rating(self, game_info, self_rating, opponent_rating, comparison):
        expected_probability = self.expected_score(game_info, self_rating, opponent_rating)
        actual_probability = self.actual_score(comparison)
        if hasattr(self_rating, 'k_factor'):
            k = self_rating.k_factor
        else:
            k = self.k_factor
        new_rating = self_rating + k * (actual_probability - expected_probability)
        if hasattr(self_rating, 'rating_floor'):
            if new_rating < self_rating.rating_floor:
                new_rating = self_rating.rating_floor
        return EloRating(new_rating)

    def expected_score(self, game_info, self_rating, opponent_rating):
        return (1.0 /
                (1.0 + 10.0 ** ((opponent_rating - self_rating) /
                                (2 * game_info.beta))));

    def actual_score(self, comparison):
        if comparison == Teams.WIN:
            return 1.0
        elif comparison == Teams.DRAW:
            return 0.5
        else:
            return 0.0

    def calculate_match_quality(self, game_info, teams):
        self.validate_team_count_and_players_count_per_team(teams)

        teams.sort()

        # The TrueSkill paper mentions that they used s1 - s2 (rating difference) to
        # determine match quality. Moser converts that to a percentage as a delta from 50%
        # using the cumulative density function of the specific curve being used
        expected_score = self.expected_score(game_info,
                                             teams[0].ratings()[0].mean,
                                             teams[1].ratings()[0].mean)
        return (0.5 - abs(expected_score - 0.5)) / 0.5
