"""
Database: Models
================

In this tutorial, we use the database to load models and `Tracer`'s from a non-linear search. This allows us to
visualize and interpret its results.

We then show how the database also allows us to load many `Tracer`'s correspond to many samples of the non-linear
search. This allows us to compute the errors on quantities that the `Tracer` contains, but were not sampled directly
by the non-linear search.
"""
# %matplotlib inline
# from pyprojroot import here
# workspace_path = str(here())
# %cd $workspace_path
# print(f"Working Directory has been set to `{workspace_path}`")

import autofit as af
import autolens as al
import autolens.plot as aplt

"""
__Database File__

First, set up the aggregator as we did in the previous tutorial.
"""
agg = af.Aggregator.from_database("database.sqlite")

"""
__Tracer via Database__

Having performed a model-fit, we now want to interpret and visualize the results. In this example, we want to inspect
the `Tracer` objects that gave good fits to the data. 

Using the API shown in the `start_here.py` example this would require us to create a `Samples` object and manually 
compose our own `Tracer` object. For large datasets, this would require us to use generators to ensure it is 
memory-light, which are cumbersome to write.

This example therefore uses the `TracerAgg` object, which conveniently loads the `Tracer` objects of every fit via 
generators for us. Explicit examples of how to do this via generators is given in the `advanced/manual_generator.py` 
tutorial.

We get a tracer generator via the `al.agg.TracerAgg` object, where this `tracer_gen` contains the maximum log
likelihood tracer of every model-fit.
"""
tracer_agg = al.agg.TracerAgg(aggregator=agg)
tracer_gen = tracer_agg.max_log_likelihood_gen_from()

"""
We can now iterate over our tracer generator to make the plots we desire.
"""
grid = al.Grid2D.uniform(shape_native=(100, 100), pixel_scales=0.1)

for tracer in tracer_gen:
    tracer_plotter = aplt.TracerPlotter(tracer=tracer, grid=grid)
    tracer_plotter.figures_2d(convergence=True, potential=True)

"""
__Einstein Mass Example__

Each tracer has the information we need to compute the Einstein mass of a model. Therefore, lets print 
the Einstein mass of each of our most-likely lens galaxies.

The model instance uses the model defined by a pipeline. In this pipeline, we called the lens galaxy `lens`.
"""
tracer_agg = al.agg.TracerAgg(aggregator=agg)
tracer_gen = tracer_agg.max_log_likelihood_gen_from()

print("Maximum Log Likelihood Lens Einstein Masses:")

for tracer in tracer_gen:
    einstein_mass = tracer.galaxies[0].einstein_mass_angular_from(grid=grid)

    print("Einstein Mass (angular units) = ", einstein_mass)

    cosmology = al.cosmo.Planck15()

    critical_surface_density = (
        cosmology.critical_surface_density_between_redshifts_from(
            redshift_0=tracer.galaxies[0].redshift,
            redshift_1=tracer.galaxies[1].redshift,
        )
    )

    einstein_mass_kpc = einstein_mass * critical_surface_density

    print("Einstein Mass (kpc) = ", einstein_mass_kpc)
    print("Einstein Mass (kpc) = ", "{:.4e}".format(einstein_mass_kpc))

    print(einstein_mass)

"""
__Errors (PDF from samples)__

In this example, we will compute the errors on the axis ratio of a model. Computing the errors on a quantity 
like the trap `density` is simple, because it is sampled by the non-linear search. The errors are therefore accessible
via the `Samples`, by marginalizing over all over parameters via the 1D Probability Density Function (PDF).

Computing the errors on the axis ratio is more tricky, because it is a derived quantity. It is a parameter or 
measurement that we want to calculate but was not sampled directly by the non-linear search. The `TracerAgg` object 
object has everything we need to compute the errors of derived quantities.

Below, we compute the axis ratio of every model sampled by the non-linear search and use this determine the PDF 
of the axis ratio. When combining each axis ratio we weight each value by its `weight`. For Dynesty, 
the nested sampler used by the fit, this ensures models which gave a bad fit (and thus have a low weight) do not 
contribute significantly to the axis ratio error estimate.

We set `minimum_weight=`1e-4`, such that any sample with a weight below this value is discarded when computing the 
error. This speeds up the error computation by only using a small fraction of the total number of samples. Computing
a delta ellipticity is cheap, and this is probably not necessary. However, certain quantities have a non-negligible
computational overhead is being calculated and setting a minimum weight can speed up the calculation without 
significantly changing the inferred errors.

Below, we use the `TracerAgg` to get the `Tracer` of every Dynesty sample in each model-fit. We extract from each 
tracer the model's axis-ratio, store them in a list and find the value via the PDF and quantile method. This again
uses generators, ensuring minimal memory use. 

In order to use these samples in the function `quantile`, we also need the weight list of the sample weights. We 
compute this using the `TracerAgg`'s function `weights_above_gen_from`, which computes generators of the weights of all 
points above this minimum value. This again ensures memory use in minimal.
"""
tracer_agg = al.agg.TracerAgg(aggregator=agg)
tracer_list_gen = tracer_agg.all_above_weight_gen_from(minimum_weight=1e-4)
weight_list_gen = tracer_agg.weights_above_gen_from(minimum_weight=1e-4)

for tracer_gen, weight_gen in zip(tracer_list_gen, weight_list_gen):
    axis_ratio_list = []

    for tracer in tracer_gen:
        axis_ratio = al.convert.axis_ratio_from(
            ell_comps=tracer.galaxies[0].mass.ell_comps
        )

        axis_ratio_list.append(axis_ratio)

    weight_list = [weight for weight in weight_gen]

    median_axis_ratio, upper_axis_ratio, lower_axis_ratio = af.marginalize(
        parameter_list=axis_ratio_list, sigma=3.0, weight_list=weight_list
    )

    print(f"Axis-Ratio = {median_axis_ratio} ({upper_axis_ratio} {lower_axis_ratio}")

"""
__Errors (Random draws from PDF)__

An alternative approach to estimating the errors on a derived quantity is to randomly draw samples from the PDF 
of the non-linear search. For a sufficiently high number of random draws, this should be as accurate and precise
as the method above. However, it can be difficult to be certain how many random draws are necessary.

The weights of each sample are used to make every random draw. Therefore, when we compute the axis-ratio and its errors
we no longer need to pass the `weight_list` to the `quantile` function.
"""
tracer_agg = al.agg.TracerAgg(aggregator=agg)
tracer_list_gen = tracer_agg.randomly_drawn_via_pdf_gen_from(total_samples=2)

for tracer_gen in tracer_list_gen:
    axis_ratio_list = []

    for tracer in tracer_gen:
        axis_ratio = al.convert.axis_ratio_from(
            ell_comps=tracer.galaxies[0].mass.ell_comps
        )

        axis_ratio_list.append(axis_ratio)

    median_axis_ratio, upper_axis_ratio, lower_axis_ratio = af.marginalize(
        parameter_list=axis_ratio_list, sigma=3.0
    )

    print(f"Axis-Ratio = {median_axis_ratio} ({upper_axis_ratio} {lower_axis_ratio}")


"""
__Pickle Files__

In the modeling script, we used the pickle_files input to search.run() to pass a .pickle file from the dataset folder to 
the database. 

Our strong lens dataset was created via a simulator script, so we passed the `Tracer` used to simulate the strong
lens, which was written as a .pickle file called `true_tracer.pickle` to the search to make it accessible in the 
database. This will allow us to directly compare the inferred model to the `truth`. 
"""
# true_tracers = [true_tracer for true_tracer in agg.values("true_tracer")]

print("Parameters used to simulate the lens dataset:")
# print(true_tracers)


"""
Finish.
"""
