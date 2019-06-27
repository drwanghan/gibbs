import attr
import types
from typing import Union
from enum import Enum
import numpy as np
from scipy.optimize import differential_evolution


class OptimizationMethod(Enum):
    """
    Available optimization solvers.
    """
    SCIPY_DE = 1


@attr.s(auto_attribs=True)
class ScipyDifferentialEvolutionSettings:
    """
    Optional arguments to pass for SciPy's differential evolution caller.

    Members
    ----------------

    :ivar str strategy:
        The differential evolution strategy to use. Should be one of: - 'best1bin' - 'best1exp' - 'rand1exp' -
        'randtobest1exp' - 'currenttobest1exp' - 'best2exp' - 'rand2exp' - 'randtobest1bin' - 'currenttobest1bin' -
        'best2bin' - 'rand2bin' - 'rand1bin' The default is 'best1bin'.

    :ivar float recombination:
        The recombination constant, should be in the range [0, 1]. In the literature this is also known as the crossover
        probability, being denoted by CR. Increasing this value allows a larger number of mutants to progress into the
        next generation, but at the risk of population stability.

    :ivar float mutation:
        The mutation constant. In the literature this is also known as differential weight, being denoted by F. If
        specified as a float it should be in the range [0, 2].

    :ivar float tol:
        Relative tolerance for convergence, the solving stops when `np.std(pop) = atol + tol * np.abs(np.mean(population_energies))`,
        where and `atol` and `tol` are the absolute and relative tolerance respectively.

    :ivar int|numpy.random.RandomState seed:
        If `seed` is not specified the `np.RandomState` singleton is used. If `seed` is an int, a new
        `np.random.RandomState` instance is used, seeded with seed. If `seed` is already a `np.random.RandomState instance`,
        then that `np.random.RandomState` instance is used. Specify `seed` for repeatable minimizations.

    :ivar int workers:
        If `workers` is an int the population is subdivided into `workers` sections and evaluated in parallel
        (uses `multiprocessing.Pool`). Supply -1 to use all available CPU cores. Alternatively supply a map-like
        callable, such as `multiprocessing.Pool.map` for evaluating the population in parallel. This evaluation is
        carried out as `workers(func, iterable)`.

    :ivar bool disp:
        Display status messages during optimization iterations.

    :ivar polish:
        If True (default), then `scipy.optimize.minimize` with the `L-BFGS-B` method is used to polish the best
        population member at the end, which can improve the minimization slightly.
    """
    number_of_decision_variables: int
    strategy: str = 'best1bin'
    recombination: float = 0.3
    mutation: float = 0.6
    tol: float = 1e-5
    seed: Union[np.random.RandomState, int] = np.random.RandomState()
    workers: int = 1
    disp: bool = False
    polish: bool = True
    popsize: int = None
    population_size_for_each_variable: int = 15
    total_population_size_limit: int = 100

    def __attrs_post_init__(self):
        if self.popsize is None:
            self.popsize = self._estimate_population_size()

    def _estimate_population_size(self):
        population_size = self.population_size_for_each_variable * self.number_of_decision_variables
        if population_size > self.total_population_size_limit:
            population_size = self.total_population_size_limit

        return population_size


@attr.s(auto_attribs=True)
class OptimizationProblem:
    """
    This class stores and solve optimization problems with the available solvers.
    """
    objective_function: types.FunctionType
    bounds: list
    args: list
    optimization_method: OptimizationMethod
    solver_args: ScipyDifferentialEvolutionSettings = None

    def __attrs_post_init__(self):
        if self.optimization_method == OptimizationMethod.SCIPY_DE and self.solver_args is None:
            self.solver_args = ScipyDifferentialEvolutionSettings(self._number_of_decision_variables)

    @property
    def _number_of_decision_variables(self):
        return len(self.bounds)

    def solve_minimization(self):
        if self.optimization_method == OptimizationMethod.SCIPY_DE:
            result = differential_evolution(
                self.objective_function,
                bounds=self.bounds,
                args=self.args,
                strategy=self.solver_args.strategy,
                popsize=self.solver_args.popsize,
                recombination=self.solver_args.recombination,
                mutation=self.solver_args.mutation,
                tol=self.solver_args.tol,
                disp=self.solver_args.disp,
                polish=self.solver_args.polish,
                seed=self.solver_args.seed,
                workers=self.solver_args.workers
            )
            return result
        else:
            raise NotImplementedError('Unavailable optimization method.')
