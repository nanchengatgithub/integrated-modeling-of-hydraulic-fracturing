# Integrated Modeling of Hydraulic Fracturing

Hydraulic fracture modeling (HFM) is a specialized workflow for modeling and simulating hydraulic fractured wells in ERT. It takes the advantages of multi-realization framework of ERT and integrates the fracture modeling tool (StimPlan) into reservoir simulation workflow, thus enabling assessment of effects of rock mechanics properties on well performance together with other geological and petrophysical properties. StimPlan geo-models are built based on detailed geological descriptions at the selected location on the well trajectory for hydraulic fracturing, ensuring consistency between the geological model from geologist and the StimPlan model for hydraulic fracture modeling.


The workflow consists of the following major steps:
- Import Geo-grid and cell properties, typically exported from a RMS project
- Import pressure data, from flow simulation models or from a user-defined pressure-depth table in csv-format (depth in TVDMSL and pressure in bara)
- Build StimPlan models for selected locations (measured depths of the well) based on the Geo-grid and its cell properties, geo-mechanical input and pressure data
- Run StimPlan fracture propagation simulation
- Import StimPlan simulated fractures into ResInsight and convert the fractures and export them in the form of well completion data (well connection factors)
- Eclipse simulation for well performance



