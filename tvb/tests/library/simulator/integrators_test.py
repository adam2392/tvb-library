# -*- coding: utf-8 -*-
#
#
#  TheVirtualBrain-Scientific Package. This package holds all simulators, and 
# analysers necessary to run brain-simulations. You can use it stand alone or
# in conjunction with TheVirtualBrain-Framework Package. See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2017, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Test for tvb.simulator.coupling module
# TODO: evaluate equations?

.. moduleauthor:: Paula Sanz Leon <sanzleon.paula@gmail.com>
.. moduleauthor:: Marmaduke Woodman <mmwoodman@gmail.com>

"""

import numpy
import pytest
from tvb.tests.library.base_testcase import BaseTestCase
from tvb.simulator import integrators
from tvb.simulator import noise

# For the moment all integrators inherit dt from the base class
dt = integrators.Integrator.dt.interface['default']


class TestIntegrators(BaseTestCase):
    """
    Define test cases for coupling:
        - initialise each class
        - check default parameters
        - change parameters 
        
    """

    def _dummy_dfun(self, X, coupling, local_coupling):
        # equiv to linear system with identity matrix
        return X

    def _test_scheme(self, integrator):
        sh = 2, 10, 1
        nX = integrator.scheme(numpy.random.randn(*sh), self._dummy_dfun, 0.0, 0.0, 0.0)
        assert nX.shape == sh

    def _call_base_scheme(self, integrator):
        integrator.scheme(0.0, lambda x, y, z: 0.0, 0.0, 0.0, 0.0)

    def test_integrator_base_class(self):
        integrator = integrators.Integrator()
        assert integrator.dt == dt
        with pytest.raises(NotImplementedError):
            self._call_base_scheme(integrator)

    def test_heun(self):
        heun_det = integrators.HeunDeterministic()
        heun_sto = integrators.HeunStochastic()
        heun_sto.noise.dt = heun_sto.dt
        assert heun_det.dt == dt
        assert heun_sto.dt == dt
        assert isinstance(heun_sto.noise, noise.Additive)
        assert heun_sto.noise.nsig == 1.0
        assert heun_sto.noise.ntau == 0.0
        self._test_scheme(heun_det)
        self._test_scheme(heun_sto)

    def test_euler(self):
        euler_det = integrators.EulerDeterministic()
        euler_sto = integrators.EulerStochastic()
        euler_sto.noise.dt = euler_sto.dt
        assert euler_det.dt == dt
        assert euler_sto.dt == dt
        assert isinstance(euler_sto.noise, noise.Additive)
        assert euler_sto.noise.nsig == 1.0
        assert euler_sto.noise.ntau == 0.0
        self._test_scheme(euler_det)
        self._test_scheme(euler_sto)

    def test_rk4(self):
        rk4 = integrators.RungeKutta4thOrderDeterministic()
        assert rk4.dt == dt
        self._test_scheme(rk4)

    def test_identity_scheme(self):
        "Verify identity scheme works"
        x, c, lc, s = 1, 2, 3, 4

        def dfun(x, c, lc):
            return x + c - lc

        integ = integrators.Identity()
        xp1 = integ.scheme(x, dfun, c, lc, s)
        assert xp1 == 4
        self._test_scheme(integ)

    def _scipy_scheme_tester(self, name):
        "Test a SciPy integration scheme."
        for name_ in (name, name + 'Stochastic'):
            cls = getattr(integrators, name)
            obj = cls()
            assert dt == obj.dt
            self._test_scheme(obj)

    def test_scipy_vode(self):
        self._scipy_scheme_tester('VODE')

    def test_scipy_dop853(self):
        self._scipy_scheme_tester('Dop853')

    def test_scipy_dopri5(self):
        self._scipy_scheme_tester('Dopri5')

    def test_clamp(self):
        vode = integrators.VODE(
            clamped_state_variable_indices=numpy.r_[0, 3],
            clamped_state_variable_values=numpy.array([[42.0, 24.0]])
        )
        x = numpy.ones((5, 4, 2))
        for i in range(10):
            x = vode.scheme(x, self._dummy_dfun, 0.0, 0.0, 0.0)
        for idx, val in zip(vode.clamped_state_variable_indices, vode.clamped_state_variable_values):
            assert numpy.allclose(x[idx], val)
