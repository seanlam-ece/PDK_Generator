""" Copyright chriskeraly
    Copyright (c) 2019 Lumerical Inc. """

from lumopt.optimizers.optimizer import Optimizer

class Minimizer(Optimizer):
    """ Base class (or super class) for all optimizers coded as minimizers. """

    def define_callables(self, callable_fom, callable_jac):
        """ Defines the functions that the Optimizer class will use to evaluate the figure of merit and its gradient. The sign
            of the figure of merit and its gradient are flipped here so that the Optimizer class sees a maximizer rather
            than a minimizer.

            Parameters
            ----------
            :param callable_fom: function taking a numpy vector of optimization parameters and returning a scalar figure of merit.
            :param callable_jac: function taking a numpy vector of optimization parameters and returning a vector of the same
                                 size with the computed gradients.
        """

        def callable_fom_local(params):
            params_over_scaling_factor = params / self.scaling_factor
            fom = callable_fom(params_over_scaling_factor)
            fom_penalty = self.penalty_fun(params_over_scaling_factor)
            self.current_fom = -(fom + fom_penalty)
            self.current_params = params
            self.fom_calls += 1
            return self.current_fom * self.fom_scaling_factor

        def callable_jac_local(params):
            params_over_scaling_factor = params / self.scaling_factor
            fom_gradients = callable_jac(params_over_scaling_factor) / self.scaling_factor
            fom_penalty_gradients = self.penalty_jac(params_over_scaling_factor) / self.scaling_factor
            self.current_gradients = -(fom_gradients + fom_penalty_gradients)
            if self.fom_calls==1:
                self.callback(params)
            return self.current_gradients * self.fom_scaling_factor

        return callable_fom_local,callable_jac_local