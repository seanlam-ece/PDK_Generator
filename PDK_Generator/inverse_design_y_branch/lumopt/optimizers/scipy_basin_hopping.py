""" Copyright (c) 2019 Lumerical Inc. """

import copy
import numpy as np
import scipy as sp
import scipy.optimize as spo

from lumopt.optimizers.minimizer import Minimizer

class ScipyBasinHopping(Minimizer):
    """ 
        Wrapper for SciPy's basin hopping global optimizer. 

            https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.basinhopping.html#scipy.optimize.basinhopping

        Parameters
        ----------
        :param niter:            The number of basin-hopping iterations.
        :param T:                The “temperature” parameter for the accept or reject criterion. Higher “temperatures” mean that larger jumps in
                                 function value will be accepted. For best results T should be comparable to the separation (in function value)
                                 between local minima.
        :param stepsize:         Maximum step size for use in the random displacement.
        :param minimizer_kwargs: Extra keyword arguments to be passed to the local minimizer.
        :param take_step:        Callable take_step(x). Replaces the default step-taking routine with this routine. The default step-taking routine
                                 is a random displacement of the coordinates, but other step-taking algorithms may be better for some systems.
        :param accept_test:      Callable accept_test(f_new, x_new, f_old, x_old) returning a bool. It defines a test which will be used to judge
                                 whether or not to accept the step. This will be used in addition to the Metropolis test based on “temperature” T.
                                 If any of the tests return False then the step is rejected.
        :param interval:         Interval for how often to update the stepsize.
        :param disp:             True to print status messages.
        :param niter_success:    Stop the run if the global minimum candidate remains the same for this number of iterations.
        :param seed:             If seed is not specified, then the np.RandomState singleton is used.
        :param scaling_factor:   Used to scale the optimization parameters so that they have magnitudes in the range zero to one.
        :param scale_initial_gradient_to: enforces a rescaling of the gradient to change the optimization parameters by at least this much;
                                          the default value of zero disables automatic scaling.
        :param: penalty_fun:   penalty function to be added to the figure of merit; it must be a function that takes a vector with the
                               optimization parameters and returns a single value.
        :param: penalty_jac:   gradient of the penalty function; must be a function that takes a vector with the optimization parameters
                               and returns a vector of the same length.
    """

    def __init__(self,
                 niter = 100,
                 T = 1.0,
                 stepsize = 0.5,
                 minimizer_kwargs = {'args': (), 'method': 'L-BFGS-B', 'jac': None, 'hess': None, 'hessp': None, 'bounds': None, 'constraints': (), 'tol': None, 'callback': None,
                                     'options': {'maxiter': 100, 'disp': True, 'gtol': 1.0e-5,'ftol': 1.0e-5} },
                 take_step = None,
                 accept_test = None,
                 interval = 50,
                 disp = True,
                 niter_success = 10,
                 seed = 1234567890,
                 scaling_factor = 1.0,
                 scale_initial_gradient_to = 0.0,
                 penalty_fun = None,
                 penalty_jac = None):
        super(ScipyBasinHopping, self).__init__(max_iter = niter,
                                                scaling_factor = scaling_factor,
                                                scale_initial_gradient_to = scale_initial_gradient_to,
                                                penalty_fun = penalty_fun,
                                                penalty_jac = penalty_jac)
        self.T = float(T)
        self.stepsize = float(stepsize)
        self.minimizer_kwargs = dict(minimizer_kwargs)
        self.take_step = take_step
        self.accept_test = accept_test
        self.interval = int(interval)
        self.disp = bool(disp)
        self.niter_success = niter_success
        self.seed = int(seed)
    
    def run(self):
        print('Running SciPy basin hopping global optimizer:')
        print('bounds = {}'.format(self.bounds))
        print('start = {}'.format(self.start_point))
        self.minimizer_kwargs['bounds'] = self.bounds
        self.minimizer_kwargs['jac'] = self.callable_jac
        res = spo.basinhopping(func = self.callable_fom,
                               x0 = self.start_point,
                               niter = self.max_iter,
                               T = self.T,
                               stepsize = self.stepsize,
                               minimizer_kwargs = self.minimizer_kwargs,
                               take_step = self.take_step,
                               accept_test = self.accept_test,
                               callback = self.callback,
                               interval = self.interval,
                               disp = self.disp,
                               niter_success = self.niter_success,
                               seed = self.seed)
        res.fun = -res.fun
        res.x /= self.scaling_factor
        best_res = res.lowest_optimization_result
        best_res.fun = -best_res.fun
        best_res.x /= self.scaling_factor
        if hasattr(best_res, 'jac'):
            best_res.jac = -self.scaling_factor*best_res.jac
        print('')
        print('Completed basin hopping optimization: {}'.format(res.message[0]))
        print('Number of global iterations: {}'.format(res.nit))
        print('Number of minimization failures: {}'.format(res.minimization_failures))
        print('Number of FOM evaluations: {}'.format(res.nfev))
        print('BEST FOM = {}'.format(best_res.fun))
        print('BEST PARAMETERS = {}'.format(best_res.x))
        with open(self.logfile,'a') as f:
            f.write('best_fom = {};\n'.format(best_res.fun))
            f.write('best_params = {};\n'.format(best_res.x))
            if hasattr(best_res, 'jac'):
                f.write('best_jac = {};\n'.format(best_res.jac))
            f.write('\n \n')
        return res

    def report_writing(self):
        with open(self.logfile,'a') as f:
            f.write('\n')
            f.write('fom(1+{0}) = {1};\n'.format(self.iteration, np.array2string(self.fom_hist[-1], separator = ', ')))
            f.write('params(1+{0},:) = {1};\n'.format(self.iteration, np.array2string(self.params_hist[-1]/self.scaling_factor, separator = ', ')))
            if len(self.gradients_hist) > 0:
                f.write('jac(1+{0},:) = {1};\n'.format(self.iteration, np.array2string(-self.gradients_hist[-1]*self.scaling_factor, separator = ', ')))
            f.write('\n')