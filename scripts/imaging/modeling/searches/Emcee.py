"""
Searches: Emcee
===============

Emcee (https://github.com/dfm/emcee) is an ensemble MCMC sampler.

An MCMC algorithm only seeks to map out the posterior of parameter space, unlike a nested sampling algorithm like
Dynesty, which also aims to estimate the Bayesian evidence if the model. Therefore, in principle, an MCMC approach like
Emcee should be faster than Dynesty.

In our experience, `Emcee` is outperformed by `Dynesty` for lens modeling in all circumstances, whether that be
initializing the lens model, fitting a pixelized source or models with high dimensionality. Nevertheless, we encourage
you to give it a go yourself, and let us know on the PyAutoLens GitHub if you find an example of a problem where
`Emcee` outperforms Dynesty!

__Start Here Notebook__

If any code in this script is unclear, refer to the modeling `start_here.ipynb` notebook for more detailed comments.
"""
# %matplotlib inline
# from pyprojroot import here
# workspace_path = str(here())
# %cd $workspace_path
# print(f"Working Directory has been set to `{workspace_path}`")

from os import path
import autofit as af
import autolens as al
import autolens.plot as aplt

"""
__Dataset + Masking__

Load and plot the strong lens dataset `simple__no_lens_light` via .fits files.
"""
dataset_name = "simple__no_lens_light"
dataset_path = path.join("dataset", "imaging", dataset_name)

dataset = al.Imaging.from_fits(
    data_path=path.join(dataset_path, "data.fits"),
    psf_path=path.join(dataset_path, "psf.fits"),
    noise_map_path=path.join(dataset_path, "noise_map.fits"),
    pixel_scales=0.1,
)

mask = al.Mask2D.circular(
    shape_native=dataset.shape_native, pixel_scales=dataset.pixel_scales, radius=3.0
)

dataset = dataset.apply_mask(mask=mask)

"""
__Model__ 

In our experience, emcee is ineffective at initializing a lens model and therefore needs a 'starting point' which is
near the highest likelihood lens models. We set this starting point up below by manually inputting `UniformPriors` on
every parameter, where the centre of these priors is near the true values of the simulated lens data.

Given this need for a robust starting point, Emcee is only suited to model-fits where we have this information. It may
therefore be useful when performing lens modeling search chaining (see HowToLens chapter 3). However, even in such
circumstances, we have found that is often outperformed by other searches such as Dynesty and Zeus for both speed
and accuracy.
"""
# Lens:

mass = af.Model(al.mp.Isothermal)
mass.centre.centre_0 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)
mass.centre.centre_1 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)
mass.ell_comps.ell_comps_0 = af.UniformPrior(lower_limit=-0.3, upper_limit=0.3)
mass.ell_comps.ell_comps_1 = af.UniformPrior(lower_limit=-0.3, upper_limit=0.3)
mass.einstein_radius = af.UniformPrior(lower_limit=1.0, upper_limit=2.0)

shear = af.Model(al.mp.ExternalShear)
shear.gamma_1 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)
shear.gamma_2 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)

# Source:

bulge = af.Model(al.lp.Sersic)
bulge.centre.centre_0 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)
bulge.centre.centre_1 = af.UniformPrior(lower_limit=-0.1, upper_limit=0.1)
bulge.ell_comps.ell_comps_0 = af.UniformPrior(lower_limit=-0.3, upper_limit=0.3)
bulge.ell_comps.ell_comps_1 = af.UniformPrior(lower_limit=-0.3, upper_limit=0.3)
bulge.intensity = af.UniformPrior(lower_limit=0.1, upper_limit=0.5)
bulge.effective_radius = af.UniformPrior(lower_limit=0.0, upper_limit=0.4)
bulge.sersic_index = af.UniformPrior(lower_limit=0.5, upper_limit=2.0)

lens = af.Model(al.Galaxy, redshift=0.5, mass=mass, shear=shear)
source = af.Model(al.Galaxy, redshift=1.0, bulge=bulge)

# Overall Lens Model:

model = af.Collection(galaxies=af.Collection(lens=lens, source=source))

"""
__Analysis__ 

We create the Analysis as per using.
"""
analysis = al.AnalysisImaging(dataset=dataset)

"""
__Search__

Below we use emcee to fit the lens model, using the model with start points as described above. See the Emcee docs
for a description of what the input parameters below do.
"""
search = af.Emcee(
    path_prefix=path.join("imaging", "searches"),
    name="Emcee",
    unique_tag=dataset_name,
    nwalkers=30,
    nsteps=500,
    initializer=af.InitializerBall(lower_limit=0.49, upper_limit=0.51),
    auto_correlations_settings=af.AutoCorrelationsSettings(
        check_for_convergence=True,
        check_size=100,
        required_length=50,
        change_threshold=0.01,
    ),
    iterations_per_update=5000,
    number_of_cores=1,
)

result = search.fit(model=model, analysis=analysis)

"""
__Result__

We can use an `EmceePlotter` to create a corner plot, which shows the probability density function (PDF) of every
parameter in 1D and 2D.
"""
search_plotter = aplt.EmceePlotter(samples=result.samples)
search_plotter.corner()

"""
Finish.
"""
