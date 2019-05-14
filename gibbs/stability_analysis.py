import numpy as np
import attr
from scipy.optimize import differential_evolution as de


@attr.s(auto_attribs=True)
class StabilityResult:
    phase_split: bool
    x: np.ndarray
    reduced_tpd: float


def stability_test(model, P, T, z, monitor=False):
    n_components = model.number_of_components
    search_space = [(0, 1)] * n_components
    f_z = model.fugacity(P, T, z)

    result = de(
        _reduced_tpd, 
        bounds=search_space, 
        args=[model, P, T, f_z],
        popsize=25,
        recombination=0.9,
        disp=monitor,
        polish=False
    )

    x = result.x / result.x.sum()
    reduced_tpd = result.fun

    if np.allclose(x, z):
        phase_split = False
    elif reduced_tpd < 0.:
        phase_split = True
    else:
        phase_split = False

    stability_test_result = StabilityResult(
        phase_split=phase_split,
        x=x,
        reduced_tpd=reduced_tpd
    )

    return stability_test_result


def _reduced_tpd(x, model, P, T, f_z):
    tol = 1e-2
    x = x / x.sum()
    condition1 = 1 - tol <= x.sum()
    condition2 = x.sum() <= 1 + tol
    condition3 = x.max() <= 1.0
    condition4 = x.min() >= 0.0
    feasible_conditions = condition1 and condition2 and condition3 and condition4

    f_x = model.fugacity(P, T, x)
    tpd = np.sum(x * (np.log(f_x / f_z)))

    if not 1 - tol <= np.sum(x) <= 1 + tol:
        # Penalization if candidate is not in feasible space
        penalty_parameter = 10.
        tpd += penalty_parameter * _penalty_function(x, 1)

    return tpd


def _penalty_function(x, feasible_limit):
    feasible_region_marker = np.abs(x.sum() - feasible_limit)
    return feasible_region_marker * feasible_region_marker
