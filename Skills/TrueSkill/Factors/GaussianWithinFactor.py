from GaussianFactor import GaussianFactor, Gauss
from Skills.TrueSkill.TruncatedGaussianCorrectionFunctions import TruncatedGaussianCorrectionFunctions
from math import log, sqrt
from copy import copy

class GaussianWithinFactor(GaussianFactor):
    '''
    Factor representing a team difference that has not exceeded the draw margin
    '''

    def __init__(self, epsilon, variable):
        GaussianFactor.__init__(self, "%s <= %.2f" % (variable, epsilon))
        self.epsilon = epsilon
        self.create_variable_to_message_binding(variable)

    def log_normalization(self):
        marginal = self.variables[0].value
        message = self.messages[0].value
        message_from_variable = marginal / message
        mean = message_from_variable.mean
        std = message_from_variable.stdev
        z = (Gauss.cumulative_to((self.epsilon - mean) / std) -
             Gauss.cumulative_to((-self.epsilon - mean) / std))

        return -Gauss.log_product_normalization(message_from_variable, message) + log(z)

    def update_message_variable(self, message, variable):
        old_marginal = copy(variable.value)
        old_message = copy(message.value)
        message_from_variable = old_marginal / old_message

        c = message_from_variable.precision
        d = message_from_variable.precision_mean

        sqrt_c = sqrt(c)
        d_on_sqrt_c = d / sqrt_c

        epsilon_times_sqrt_c = self.epsilon * sqrt_c
        d = message_from_variable.precision_mean

        denominator = 1.0 - TruncatedGaussianCorrectionFunctions.w_within_margin(d_on_sqrt_c, epsilon_times_sqrt_c)
        new_precision = c / denominator
        new_precision_mean = (d + sqrt_c * TruncatedGaussianCorrectionFunctions.v_within_margin(d_on_sqrt_c, epsilon_times_sqrt_c)) / denominator

        new_marginal = Gauss.from_precision_mean(new_precision_mean, new_precision)
        new_message = (old_message * new_marginal) / old_marginal

        message.value = new_message
        variable.value = new_marginal

        return new_marginal - old_marginal
