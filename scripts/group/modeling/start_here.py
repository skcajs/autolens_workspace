"""
Modeling: Lens x3 + Source x1
=============================

This script fits a `PointDict` dataset of a 'group-scale' strong lens where:

 - There are three lens galaxies whose light models are `SersicSph` profiles and total mass distributions
 are `IsothermalSph` models.
 - The source `Galaxy` is modeled as a point source `Point`.

The point-source dataset used in this example consists of the positions of the lensed source's multiple images and
their fluxes, both of which are used in the fit.

__Strong Lens Scale__

This script models an example strong lens on the 'group' scale, where there is a single primary lens galaxy
and two smaller galaxies nearby, whose mass contributes significantly to the ray-tracing and is therefore included in
the strong lens model.

In this example we model the source as a point-source, as fitting the full `Imaging` data and extended emission in the
lensed source's arcs is challenging due to the high complexity of the lens model.

The `group/chaining` package includes an example script showing how **PyAutoLens** can model this dataset's full
extended emission, however this requires familiarity's advanced feature called 'search chaining'
which is covered in chapter 3 of **HowToLens**. This package also shows how to do this using a pixelized source
reconstruction.
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
__Dataset__

Load the strong lens dataset `group`, which is the dataset we will use to perform lens modeling.

We begin by loading an image of the dataset. Although we perform point-source modeling and will not use this data in 
the model-fit, it is useful to load it for visualization. By passing this dataset to the model-fit at the
end of the script it will be used when visualizing the results. However, the use of an image in this way is entirely
optional, and if it were not included in the model-fit visualization would simple be performed using grids without
the image.
"""
dataset_name = "lens_x3__source_x1"
dataset_path = path.join("dataset", "group", dataset_name)

data = al.Array2D.from_fits(
    file_path=path.join(dataset_path, "data.fits"), pixel_scales=0.1
)

"""
We now load the point source dataset we will fit using point source modeling. We load this data as a `PointDict`,
which is a Python dictionary containing the positions and fluxes of every point source. 

In this example there is just one point source, corresponding to the brightest pixel of each lensed multiple image. For
other example point source datasets there are multiple sources.
"""
point_dict = al.PointDict.from_json(
    file_path=path.join(dataset_path, "point_dict.json")
)

"""
We can print this dictionary to see the `name`, `positions` and `fluxes` of the dataset, as well as their noise-map 
values.
"""
print("Point Source Dict:")
print(point_dict)

"""
We can plot our positions dataset over the observed image.
"""
visuals = aplt.Visuals2D(positions=point_dict.positions_list)

array_plotter = aplt.Array2DPlotter(array=data, visuals_2d=visuals)
array_plotter.figure_2d()

"""
We can also just plot the positions, omitting the image.
"""
grid_plotter = aplt.Grid2DPlotter(grid=point_dict["point_0"].positions)
grid_plotter.figure_2d()

"""
__PointSolver__

For point-source modeling we also need to define our `PointSolver`. This object determines the multiple-images of 
a mass model for a point source at location (y,x) in the source plane, by iteratively ray-tracing light rays to the 
source-plane. 

Checkout the script ? for a complete description of this object, we will use the default `PositionSolver` in this 
example with a `point_scale_precision` half the value of the position noise-map, which should be sufficiently good 
enough precision to fit the lens model accurately.
"""
grid = al.Grid2D.uniform(shape_native=data.shape_native, pixel_scales=data.pixel_scales)

point_solver = al.PointSolver(grid=grid, pixel_scale_precision=0.025)

"""
__Model__

We compose a lens model where:

 - There are three lens galaxy's with `IsothermalSph` total mass distributions, with the prior on the centre of each 
 profile informed by its observed centre of light [9 parameters].
 - The source galaxy's light is a point `PointFlux` [3 parameters].

The number of free parameters and therefore the dimensionality of non-linear parameter space is N=12.

__Model JSON File_

For group modeling, there can be many lens and source galaxies. Manually writing the model in a Python script, in the
way we do for galaxy-scale lenses, is therefore not ideal.

We therefore write the model for this system in a separate Python file and output it to a .json file, which we created 
via the script `group/model_maker/lens_x3__source_x1.py` and can be found in the 
file `group/models`. 

This file is used to load the model below and it can be easily altered to compose a group model suited to your lens 
dataset!
"""
model_path = path.join("dataset", "group", dataset_name)

lenses_file = path.join(model_path, "lenses.json")
lenses = af.Collection.from_json(file=lenses_file)

sources_file = path.join(model_path, "sources.json")
sources = af.Collection.from_json(file=sources_file)

galaxies = lenses + sources

model = af.Collection(galaxies=galaxies)

"""
The `info` attribute shows the model in a readable format.

The source does not use the ``Point`` class discussed in the previous overview example, but instead uses
a ``PointSourceChi`` object.

This object changes the behaviour of how the positions in the point dataset are fitted. For a normal ``Point`` object,
the positions are fitted in the image-plane, by mapping the source-plane back to the image-plane via the lens model
and iteratively searching for the best-fit solution.

The ``PointSourceChi`` object instead fits the positions directly in the source-plane, by mapping the image-plane
positions to the source just one. This is a much faster way to fit the positions,and for group scale lenses it
typically sufficient to infer an accurate lens model.
"""
print(model.info)

"""
__Name Pairing__

Every point-source dataset in the `PointDict` has a name, which in this example was `point_0`. This `name` pairs 
the dataset to the `Point` in the model below. Because the name of the dataset is `point_0`, the 
only `Point` object that is used to fit it must have the name `point_0`.

If there is no point-source in the model that has the same name as a `PointDataset`, that data is not used in
the model-fit. If a point-source is included in the model whose name has no corresponding entry in 
the `PointDataset` **PyAutoLens** will raise an error.

In this example, where there is just one source, name pairing appears unecessary. However, point-source datasets may
have many source galaxies in them, and name pairing is necessary to ensure every point source in the lens model is 
fitted to its particular lensed images in the `PointDict`!
**PyAutoLens** assumes that the lens galaxy centre is near the coordinates (0.0", 0.0"). 

If for your dataset the  lens is not centred at (0.0", 0.0"), we recommend that you either: 

 - Reduce your data so that the centre is (`autolens_workspace/*/data_preparation`). 
 - Manually override the lens model priors (`autolens_workspace/*/imaging/modeling/customize/priors.py`).
"""
print(model)

"""
__Search__

The lens model is fitted to the data using the nested sampling algorithm Dynesty (see `start.here.py` for a 
full description).

The folders: 

 - `autolens_workspace/*/imaging/modeling/searches`.
 - `autolens_workspace/*/imaging/modeling/customize`
  
Give overviews of the non-linear searches **PyAutoLens** supports and more details on how to customize the
model-fit, including the priors on the model.

The `name` and `path_prefix` below specify the path where results ae stored in the output folder:  

 `/autolens_workspace/output/group/lens_x3__source_x1/mass[sie]_source[point]/unique_identifier`.

__Unique Identifier__

In the path above, the `unique_identifier` appears as a collection of characters, where this identifier is generated 
based on the model, search and dataset that are used in the fit.

An identical combination of model, search and dataset generates the same identifier, meaning that rerunning the
script will use the existing results to resume the model-fit. In contrast, if you change the model, search or dataset,
a new unique identifier will be generated, ensuring that the model-fit results are output into a separate folder. 

__Number Of Cores__

We include an input `number_of_cores`, which when above 1 means that Dynesty uses parallel processing to sample multiple 
lens models at once on your CPU. When `number_of_cores=2` the search will run roughly two times as
fast, for `number_of_cores=3` three times as fast, and so on. The downside is more cores on your CPU will be in-use
which may hurt the general performance of your computer.

You should experiment to figure out the highest value which does not give a noticeable loss in performance of your 
computer. If you know that your processor is a quad-core processor you should be able to use `number_of_cores=4`. 

Above `number_of_cores=4` the speed-up from parallelization diminishes greatly. We therefore recommend you do not
use a value above this.

For users on a Windows Operating system, using `number_of_cores>1` may lead to an error, in which case it should be 
reduced back to 1 to fix it.
"""
search = af.DynestyStatic(
    path_prefix=path.join("group", "modeling"),
    name="mass[sie]_source[point]",
    unique_tag=dataset_name,
    nlive=50,
    number_of_cores=1,
)

"""
__Analysis__

The `AnalysisPoint` object defines the `log_likelihood_function` used by the non-linear search to fit the model 
to the `PointDataset`.
"""
analysis = al.AnalysisPoint(point_dict=point_dict, solver=point_solver)

"""
__Run Times__

Lens modeling can be a computationally expensive process. When fitting complex models to high resolution datasets 
run times can be of order hours, days, weeks or even months.

Run times are dictated by two factors:

 - The log likelihood evaluation time: the time it takes for a single `instance` of the lens model to be fitted to 
   the dataset such that a log likelihood is returned.

 - The number of iterations (e.g. log likelihood evaluations) performed by the non-linear search: more complex lens
   models require more iterations to converge to a solution.

The log likelihood evaluation time can be estimated before a fit using the `profile_log_likelihood_function` method,
which returns two dictionaries containing the run-times and information about the fit.
"""
run_time_dict, info_dict = analysis.profile_log_likelihood_function(
    instance=model.random_instance()
)

"""
The overall log likelihood evaluation time is given by the `fit_time` key.

For this example, it is ~0.001 seconds, which is extremely fast for lens modeling. The source-plane chi-squared
is possibly the fastest way to fit a lens model to a dataset, and therefore whilst it has limitations it is a good
way to get a rough estimate of the lens model parameters quickly.

Feel free to go ahead a print the full `run_time_dict` and `info_dict` to see the other information they contain. The
former has a break-down of the run-time of every individual function call in the log likelihood function, whereas the 
latter stores information about the data which drives the run-time (e.g. number of image-pixels in the mask, the
shape of the PSF, etc.).
"""
print(f"Log Likelihood Evaluation Time (second) = {run_time_dict['fit_time']}")

"""
To estimate the expected overall run time of the model-fit we multiply the log likelihood evaluation time by an 
estimate of the number of iterations the non-linear search will perform. 

Estimating this quantity is more tricky, as it varies depending on the lens model complexity (e.g. number of parameters)
and the properties of the dataset and model being fitted.

For this example, we conservatively estimate that the non-linear search will perform ~10000 iterations per free 
parameter in the model. This is an upper limit, with models typically converging in far fewer iterations.

If you perform the fit over multiple CPUs, you can divide the run time by the number of cores to get an estimate of
the time it will take to fit the model. However, above ~6 cores the speed-up from parallelization is less efficient and
does not scale linearly with the number of cores.
"""
print(
    "Estimated Run Time Upper Limit (seconds) = ",
    (run_time_dict["fit_time"] * model.total_free_parameters * 10000)
    / search.number_of_cores,
)

"""
__Model-Fit__

We begin the model-fit by passing the model and analysis object to the non-linear search (checkout the output folder
for on-the-fly visualization and results).
"""
result = search.fit(model=model, analysis=analysis)

"""
__Result__

The search returns a result object, which includes: 

 - The lens model corresponding to the maximum log likelihood solution in parameter space.
 - The corresponding maximum log likelihood `Tracer` object.
 - Information on the posterior as estimated by the `Dynesty` non-linear search.
"""
print(result.max_log_likelihood_instance)

tracer_plotter = aplt.TracerPlotter(
    tracer=result.max_log_likelihood_tracer, grid=result.grid
)
tracer_plotter.subplot_tracer()

search_plotter = aplt.DynestyPlotter(samples=result.samples)
search_plotter.cornerplot()

"""
Checkout `autolens_workspace/*/modeling/results.py` for a full description of the result object.
"""
