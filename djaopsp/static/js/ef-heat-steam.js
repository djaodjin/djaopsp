// CO2 Factor (kg CO2 per kWh)
// CH4 Factor (kg CH4 per kWh)
// N2O Factor (kg N2O per kWh)
// AR4 (kgCO2e)
// AR5 (kgCO2e)
Vue.prototype.$ef_heat_steam = {
  "heat-steam": {
    title: "Steam and Heat",
    co2_factor: 66.330000,
    ch4_factor: 0.001250,
    n2o_factor: 0.000125,
    ar4_factor: 66.398500,
    ar5_factor: 66.398125,
    unit: "mmbtu",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories,\" Table 7 Steam and Heat, March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub)."
  }
};
