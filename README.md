# Integrated Modeling of Hydraulic Fracturing
## Introduction
Hydraulic fracture modeling (HFM) is a specialized workflow for modeling and simulating hydraulic fractured wells in ERT. It takes the advantages of multi-realization framework of ERT and integrates the fracture modeling tool (StimPlan) into reservoir simulation workflow, thus enabling assessment of effects of rock mechanics properties on well performance together with other geological and petrophysical properties. StimPlan geo-models are built based on detailed geological descriptions at the selected location on the well trajectory for hydraulic fracturing, ensuring consistency between the geological model from geologist and the StimPlan model for hydraulic fracture modeling.
## The workflow consists of the following major steps:
- Import Geo-grid and cell properties, typically exported from a RMS project
- Import pressure data, from flow simulation models or from a user-defined pressure-depth table in csv-format (depth in TVDMSL and pressure in bara)
- Build StimPlan models for selected locations (measured depths of the well) based on the Geo-grid and its cell properties, geo-mechanical input and pressure data
- Run StimPlan fracture propagation simulation
- Import StimPlan simulated fractures into ResInsight and convert the fractures and export them in the form of well completion data (well connection factors)
- Eclipse simulation for well performance
## Tools for HFM workflow
There are a few tools involved in the HFM workflow:
- StimPlan, a hydraulic fracturing modeling tool, is used to simulate hydraulic fracture propagation. The end result from StimPlan simulation is an xml file describing the fracture geometry and conductivities.
- ResInsight is used to:
  - prepare data and build and export StimPlan models
  - import the simulation results from StimPlan, convert and export the simulated fracture in the form of connection factors for Eclipse
  - plotting and 3D visualization.
- RMS for geo-modeling
- Eclipse or OPM for flow simulation
## Minimum data requirements
- Base case StimPlan fracture design setup, saved as a .FRK text file. It is obtained from a Windows-based StimPlan project (default file name is LASTDATA.FRK and default location is StimPlan Scratch Directory).
- Rock mechanics data for each litho-facies per formation zone, in csv format.
  - Young’s modulus
  - Poission’s ratio
  - Fracture toughness, K-Ic
  - Proppant embedment
  - Biot cofficient, a function of rock porosity and elastic modulus for porous rocks such as sandstone. It’s value ranges between zero and one.
  - Effective stress ratio of horizontal stress to vertical stress, k0
  - Fluid loss coefficient
  - Fluid spurt loss
  - Immobile fluid saturation
- Data from geo-grid model
  - lithofacies data (FACIES)
  - formation name file
  - petrophysical data (PERMX, PERMZ, PORO, SWL, NTG). The names of these properties must be Eclipse compatible.
- Reservoir pressure data from sim-grid or a pressure-depth table
  - initial reservoir pressure
  - current reservoir pressure, i.e. the pressure when the well is fractured
- Well data
  - well deviation file
  - number of hydraulic fractures
  - fracturing date
  - well startup date
  - data for well production constraints
    
A yaml-file is used for configuring input data, where file paths to different grids and rock mechanics data, well data and other data for creating StimPlan model template etc. are specified.

## HFM Workflow
A separate ERT configuration file for HFM is created, containing file structure setup, data preparation and forward model steps. This is the only file needs to be included in the main ERT configuration file (using the keywork INCLUDE). Drogon tutorial file structure is used as a standard in these forward model steps. The figure below shows all the necessary steps for HFM (found in the file called hydraulic_fracturing.ert):
