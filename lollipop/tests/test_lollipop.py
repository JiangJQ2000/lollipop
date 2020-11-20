import os
import tempfile
import unittest

packages_path = os.environ.get("COBAYA_PACKAGES_PATH") or os.path.join(
    tempfile.gettempdir(), "Lollipop_packages"
)

cosmo_params = {
    "cosmomc_theta": 0.0104085,
    "As": 2.0989031673191437e-09,
    "ombh2": 0.02237,
    "omch2": 0.1200,
    "ns": 0.9649,
    "Alens": 1.0,
    "tau": 0.0544,
}

chi2s = {"lowlB": 65.5, "lowlE": 46.1, "lowlEB": 212.9}


class LollipopTest(unittest.TestCase):
    def setUp(self):
        from cobaya.install import install

        install(
            {"likelihood": {"lollipop.lowlB": None}},
            path=packages_path,
            skip_global=True,
        )

    def test_lollipop(self):
        import camb
        import lollipop

        camb_cosmo = cosmo_params.copy()
        camb_cosmo.update({"lmax": 2500, "lens_potential_accuracy": 1})
        pars = camb.set_params(**camb_cosmo)
        results = camb.get_results(pars)
        powers = results.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=True)
        cl_dict = {k: powers["total"][:, v] for k, v in {"ee": 1, "bb": 2}.items()}

        for mode, chi2 in chi2s.items():
            _llp = getattr(lollipop, mode)
            my_lik = _llp({"packages_path": packages_path})
            loglike = my_lik.loglike(cl_dict, **{})
            self.assertAlmostEqual(-2 * loglike, chi2, 0)

    def test_cobaya(self):
        for mode, chi2 in chi2s.items():
            info = {
                "debug": True,
                "likelihood": {"lollipop.{}".format(mode): None},
                "theory": {"camb": {"extra_args": {"lens_potential_accuracy": 1}}},
                "params": cosmo_params,
                "modules": packages_path,
            }
            from cobaya.model import get_model

            model = get_model(info)
            self.assertAlmostEqual(-2 * model.loglikes({})[0][0], chi2, 0)
