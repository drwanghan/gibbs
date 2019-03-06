import numpy as np
import attr

R = 8.3144598


def check_input_dimensions(instance, attribute, value):
    accentric_factor_not_eq_Tc = len(value) != len(instance.Tc)
    accentric_factor_not_eq_Pc = len(value) != len(instance.Pc)
    Pc_not_eq_Tc = len(instance.Tc) != len(instance.Pc)
    Pc_not_eq_z = len(instance.Pc) != len(instance.z)
    if accentric_factor_not_eq_Tc or accentric_factor_not_eq_Pc or Pc_not_eq_Tc or Pc_not_eq_z:
        raise ValueError("Inputed values have incompatible dimensions.")


def check_bip(instance, attribute, value):
        if value.shape[0] != value.shape[1]:
            raise ValueError("BIP's must be a 2-dim symmetric array.")
        if value.shape[0] != len(instance.Tc):
            raise ValueError("BIP's have incompatible dimension with input data such as critical temperature.")


@attr.s
class CEOS(object):
    """
    docstring here
        :param object: 
    """
    z = attr.ib(type=np.ndarray)
    Tc = attr.ib(type=np.ndarray)
    Pc = attr.ib(type=np.ndarray)
    acentric_factor = attr.ib(type=np.ndarray, validator=[check_input_dimensions])
    bip = attr.ib(type=np.ndarray, validator=[check_bip])

    @z.validator
    def check_overall_composition(self, attribute, value):
        tol = 1e-5
        if not 1 - tol <= np.sum(value) <= 1 + tol:
            raise ValueError('Overall composition must have summation equal 1.')
   
    @Tc.validator
    def validate_Tc(self, attribute, value):
        if value.any() < 0:
            raise ValueError('Temperature must be greater than zero.')
       
    @Pc.validator
    def validate_Pc(self, attribute, value):
        if value.any() < 0:
            raise ValueError('Pressure must be greater than zero.')

    @property
    def n_components(self):
        return len(self.Pc)

    def Tr(self, T):
        if T < 0:
            raise ValueError('Temperature must be greater than zero.')
        return T / self.Tc

    def Pr(self, P):
        if P < 0:
            raise ValueError('Pressure must be greater than zero.')
        return P / self.Pc


@attr.s
class PengRobinson78(CEOS):
    """
    docstring here
        :param CEOS: 
    """
    _Z_c = attr.ib(default=0.3074)
    _Omega_a = attr.ib(default=0.45724)
    _Omega_b = attr.ib(default=0.07780)

    @property
    def m(self):
        omega = self.acentric_factor
        m_low = 0.37464 + 1.54226 * omega - 0.26992 * omega * omega
        m_high = 0.3796 + 1.485 * omega - 0.1644 * omega * omega \
            + 0.01667 * omega * omega * omega
        m_value = np.where(self.acentric_factor > 0.49, m_high, m_low)
        return m_value

    def a_i(self, T):
        return self._Omega_a * R ** 2.0 * self.Tc * self.Tc / self.Pc * self.alpha(T)

    @property
    def b_i(self):
        return self._Omega_b * R * self.Tc / self.Pc

    def alpha(self, T):
        return (1 + self.m * (1 - np.sqrt(self.Tr(T)))) * (1 + self.m * (1 - np.sqrt(self.Tr(T))))

    def A_i(self, P, T):
        return self.a_i(T) * P / ((R * T) ** 2.0)

    def B_i(self, P, T):
        return self.b_i * P / (R * T)

    def A_mix(self, P, T, z):
        return np.dot(z, np.dot(z, self.A_ij(P, T)))

    def B_mix(self, P, T, z):
        return np.dot(z, self.B_i(P, T))

    def A_ij(self, P, T):
        return (1 - self.bip) * np.sqrt(np.outer(self.A_i(P, T), self.A_i(P, T)))

    def calculate_Z(self, P, T, z):
        A = self.A_mix(P, T, z)
        B = self.B_mix(P, T, z)
        a0 = -(A * B - B ** 2.0 - B ** 3.0)
        a1 = A - 3 * B ** 2.0 - 2 * B
        a2 = -(1 - B)
        a3 = 1
        coefficients = np.array([a3, a2, a1, a0])
        Z_roots = np.roots(coefficients)
        # A threshold is applied in imaginary part, since it can be 
        # numerically spurious.
        Z_real_roots = Z_roots.real[np.abs(Z_roots.imag) < 1e-5]
        return Z_real_roots


z = np.array([0.5, 0.42, 0.08])
omegas = np.array([0.0115, 0.1928, 0.4902])
Tcs = np.array([190.556, 425.16667, 617.666667])
Pcs = np.array([4604318.9, 3796942.8, 2.096e6])
kijs = np.zeros((3, 3))
eos = PengRobinson78(z=z, Tc=Tcs, Pc=Pcs, acentric_factor=omegas, bip=kijs)
P = 3.447e6
T = 410.928

z2 = np.array([0.02370, 0.46695, 0.50935])
print(eos.calculate_Z(P=P, T=T, z=z2))

z3 = np.array([0.58262, 0.41186, 0.00553])
print(eos.calculate_Z(P=P, T=T, z=z3))
