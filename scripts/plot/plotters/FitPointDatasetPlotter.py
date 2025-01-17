"""
Plots: PointDatasetPlotter
==========================

This example illustrates how to plot a `PointDataset` dataset using an `PointDatasetPlotter`.
"""
# %matplotlib inline
# from pyprojroot import here
# workspace_path = str(here())
# %cd $workspace_path
# print(f"Working Directory has been set to `{workspace_path}`")

from os import path
import autolens as al
import autolens.plot as aplt

"""
__Dataset__

First, lets load an example strong lens `PointDataset` object.
"""
dataset_name = "simple"
dataset_path = path.join("dataset", "point_source", dataset_name)

point_dict = al.PointDict.from_json(
    file_path=path.join(dataset_path, "point_dict.json")
)

point_dataset = point_dict["point_0"]

"""
__Fit__

We now fit it with a `Tracer` to create a `FitPointDataset` object.
"""
lens_galaxy = al.Galaxy(
    redshift=0.5,
    mass=al.mp.Isothermal(
        centre=(0.0, 0.0),
        einstein_radius=1.6,
        ell_comps=al.convert.ell_comps_from(axis_ratio=0.9, angle=45.0),
    ),
)

source_galaxy = al.Galaxy(
    redshift=1.0, point_0=al.ps.PointFlux(centre=(0.0, 0.0), flux=0.8)
)

tracer = al.Tracer.from_galaxies(galaxies=[lens_galaxy, source_galaxy])

grid = al.Grid2D.uniform(shape_native=(100, 100), pixel_scales=0.1)

point_solver = al.PointSolver(grid=grid, pixel_scale_precision=0.025)

fit = al.FitPointDataset(
    point_dataset=point_dataset, tracer=tracer, point_solver=point_solver
)

"""
__Figures__

We now pass the FitPointDataset to a `FitPointDatasetPlotter` and call various `figure_*` methods to plot different 
attributes.
"""
fit_plotter = aplt.FitPointDatasetPlotter(fit=fit)
fit_plotter.figures_2d(positions=True, fluxes=True)

"""
Finish.
"""
