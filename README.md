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
> 
  - Young’s modulus
  - Poission’s ratio
  - Fracture toughness, K-Ic
  - Proppant embedment
  - Biot cofficient, a function of rock porosity and elastic modulus for porous rocks such as sandstone. It’s value ranges between zero and one.
  - Effective stress ratio of horizontal stress to vertical stress, k0
  - Fluid loss coefficient
  - Fluid spurt loss
  - Immobile fluid saturation
<
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

-------- generate formation name file as input to ResInsight
INSTALL_JOB      FORMATION_NAME   <CONFIG_PATH>/../bin/jobs/HFM_FORMATION_NAME
FORWARD_MODEL    FORMATION_NAME(<RUNPATH>=<RUNPATH>)

-------- generate facies name file as input to ResInsight
INSTALL_JOB      FACIES_NAME   <CONFIG_PATH>/../bin/jobs/HFM_FACIES_NAME
FORWARD_MODEL    FACIES_NAME(<RUNPATH>=<RUNPATH>)

-------- geomodel and properties
INSTALL_JOB      GEOMODEL_PROPS   <CONFIG_PATH>/../bin/jobs/HFM_GEOMODEL_PROPS
FORWARD_MODEL    GEOMODEL_PROPS(<RUNPATH>=<RUNPATH>)

-------- generate well facies log file .las for selecting fracure locations
INSTALL_JOB      GENERATE_FACIES_LOG   <CONFIG_PATH>/../bin/jobs/HFM_GENERATE_FACIES_LOG
FORWARD_MODEL    GENERATE_FACIES_LOG(<RUNPATH>=<RUNPATH>)

------- find proper fracture locations (trying to place fractures in non-shale facies and away from faults)
INSTALL_JOB      SELECT_FRAC_LOCATIONS   <CONFIG_PATH>/../bin/jobs/HFM_SELECT_FRAC_LOCATIONS
FORWARD_MODEL    SELECT_FRAC_LOCATIONS(<RUNPATH>=<RUNPATH>)

-------- build ResInsight project for creating StimPlan geological models
INSTALL_JOB      BUILD_RI_PROJECT  <CONFIG_PATH>/../bin/jobs/HFM_BUILD_RI_PROJECT
FORWARD_MODEL    BUILD_RI_PROJECT(<RUNPATH>=<RUNPATH>)

-------- export StimPlan geological models and  save resinsight project file
INSTALL_JOB      EXPORT_STIMPLAN_MODELS  <CONFIG_PATH>/../bin/jobs/HFM_EXPORT_STIMPLAN_MODELS
FORWARD_MODEL    EXPORT_STIMPLAN_MODELS(<RUNPATH>=<RUNPATH>)

-------- plot the exported StimPlan models for QC
INSTALL_JOB      STIMPLAN_MODEL_QC  <CONFIG_PATH>/../bin/jobs/HFM_STIMPLAN_MODEL_QC
FORWARD_MODEL    STIMPLAN_MODEL_QC(<RUNPATH>=<RUNPATH>)

-------- update the StimPlan BASE datafiles with ERT-generated uncertainty parameter
INSTALL_JOB      STIMPLAN_UPDATE  <CONFIG_PATH>/../bin/jobs/HFM_STIMPLAN_UPDATE
FORWARD_MODEL    STIMPLAN_UPDATE(<RUNPATH>=<RUNPATH>)

-------- run StimPlan simulations and copy the resulting contour.xml file to /resinsight/input/
INSTALL_JOB      STIMPLAN_SIM        <CONFIG_PATH>/../bin/jobs/HFM_STIMPLAN_SIM
FORWARD_MODEL    STIMPLAN_SIM(<IENS>=<IENS>, <ITER>=<ITER>, <RUNPATH>=<RUNPATH>)

-------- plotting StimPlan simulation result file data_vs_time.csv, two .png files created, one for all parameters and the other for selected parameters
INSTALL_JOB      PLOTTING_STIMPLAN_SIM  <CONFIG_PATH>/../bin/jobs/HFM_PLOTTING_STIMPLAN_SIM
FORWARD_MODEL    PLOTTING_STIMPLAN_SIM(<IENS>=<IENS>, <ITER>=<ITER>, <RUNPATH>=<RUNPATH>)

-------- add stimplan result files .xml as fracture templates and fractures to resinsight project and export well completion data
INSTALL_JOB      INSERT_FRACS   <CONFIG_PATH>/../bin/jobs/HFM_INSERT_FRACS
FORWARD_MODEL    INSERT_FRACS(<IENS>=<IENS>, <ITER>=<ITER>, <RUNPATH>=<RUNPATH>)

-------- include the export well connection data into the schedule file for prediction
INSTALL_JOB      SCH_UPDATE   <CONFIG_PATH>/../bin/jobs/HFM_SCH_UPDATE
FORWARD_MODEL    SCH_UPDATE(<IENS>=<IENS>, <ITER>=<ITER>, <RUNPATH>=<RUNPATH>)

-------- insert an includ file for hydraulic fractures in Summary section for report production per fracture
-------- upate max number of connections per well in WELLDIMS keyword
INSTALL_JOB      ECL_UPDATE <CONFIG_PATH>/../bin/jobs/HFM_ECL_UPDATE
FORWARD_MODEL    ECL_UPDATE(<IENS>=<IENS>, <ITER>=<ITER>, <RUNPATH>=<RUNPATH>)
A snapshot of how data is organized for the HFM workflow (assuming that a realization is successfully run through):

-- eclipse
   -- include -> /scratch/fmu/nanc/ert/01_drogon_ahm/realization-18/pred_op6_hf/../iter-3/eclipse/include
   -- include_pred
      -- schedule
   -- model
-- fmuconfig -> /scratch/fmu/nanc/ert/01_drogon_ahm/realization-18/pred_op6_hf/../iter-3/fmuconfig
-- resinsight
   -- input
   -- model
   -- output
-- rms
   -- input
      -- well_modelling
   -- model
   -- output
      -- well_modelling
-- share
   -- results
       -- images
       -- maps
       -- polygons
       -- wells
-- stimplan
   -- input
   -- log
   -- model
      -- OP6_StimPlanModel_01_Valysar
      -- OP6_StimPlanModel_02_Volon
      -- OP6_StimPlanModel_03_Valysar
      -- OP6_StimPlanModel_04_Volon
   -- output
      -- OP6_StimPlanModel_01_Valysar
      -- OP6_StimPlanModel_02_Volon
      -- OP6_StimPlanModel_03_Valysar
      -- OP6_StimPlanModel_04_Volon
