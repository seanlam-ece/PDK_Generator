import numpy as np
import inspect

from lumopt.geometries.geometry import Geometry

class ParameterizedGeometry(Geometry):
    """ 
        Defines a parametrized geometry using any of the built-in geometric structures available in the FDTD CAD.
        Users must provide a Python function with the signature ('params', 'fdtd', 'only_update'). The function
        must take the optimization parameters and a handle to the FDTD CAD to build the geometry under optimization
        (material assignments included). The flag 'only_update' is used to avoid frequent recreations of the parameterized
        geometry: when the flag is true, it is assumed that the geometry was already added at least once to the CAD.

        Parameters
        ----------
        :param func:           function with the signature ('params', 'fdtd', 'only_update', **kwargs).
        :param initial_params: flat array with the initial optimization parameter values.
        :param bounds:         bounding ranges (min/max pairs) for each optimization parameter.
        :param dx:             step size for computing the figure of merit gradient using permittivity perturbations.
    """
    
    def __init__(self, func, initial_params, bounds, dx, deps_num_threads=1):
        self.deps_num_threads=deps_num_threads
        self.func = func
        self.current_params = np.array(initial_params).flatten()
        self.bounds = bounds
        self.dx = float(dx)

        if inspect.isfunction(self.func):
            bound_args = inspect.signature(self.func).bind('params', 'fdtd', 'only_update')
            if bound_args.args != ('params', 'fdtd', 'only_update'):
                raise UserWarning("user defined function does not take three positional arguments.")
        else:
            raise UserWarning("argument 'func' must be a Python function.")
        if self.dx <= 0.0:
            raise UserWarning("step size must be positive.")

        self.params_hist = list(self.current_params)

    def update_geometry(self, params, sim):
        self.current_params = params
        self.params_hist.append(params)

    def get_current_params(self):
        return self.current_params

    def calculate_gradients(self, gradient_fields):
        raise UserWarning("unsupported gradient calculation method.")

    def add_geo(self, sim, params, only_update):
        sim.fdtd.switchtolayout()
        if params is None:
            return self.func(self.current_params, sim.fdtd, only_update)
        else:
            return self.func(params, sim.fdtd, only_update)
