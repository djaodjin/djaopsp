// CO2 Factor (kg CO2 per mmBtu)
// CH4 Factor (g CH4 per mmBtu)
// N2O Factor (g N2O per mmBtu)
// Biogenic CO2 Factor (kg Biogenic CO2 per mmBtu)
// AR4 (kgCO2e)
// AR5 (kgCO2e)
Vue.prototype.$ef_mobile_combustion = {
  "electricity-mobile-electric-vehicle": {
    title: "Electricity - Mobile - Electric Vehicle",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000000,
    n2o_factor: 0.000000,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 0.000000,
    ar5_factor: 0.000000,
    unit: "kwh",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-passenger-cars": {
    title: "Motor Gasoline - Gasoline Passenger Cars",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000389,
    n2o_factor: 0.000081,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.813869,
    ar5_factor: 8.812364,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-light-duty-trucks": {
    title: "Motor Gasoline - Gasoline Light-duty Trucks (Vans, Pickup Trucks, SUVs)",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000264,
    n2o_factor: 0.000107,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.818464,
    ar5_factor: 8.815727,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-heavy-duty-vehicles": {
    title: "Motor Gasoline - Gasoline Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000293,
    n2o_factor: 0.000118,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.822466,
    ar5_factor: 8.819454,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-diesel-passenger-cars": {
    title: "Diesel Fuel - Diesel Passenger Cars",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.000011,
    n2o_factor: 0.000023,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.216986,
    ar5_factor: 10.216278,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-diesel-light-duty-trucks": {
    title: "Diesel Fuel - Diesel Light-duty Trucks",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.000016,
    n2o_factor: 0.000024,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.217646,
    ar5_factor: 10.216893,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-diesel-medium-and-heavy-duty-vehicles": {
    title: "Diesel Fuel - Diesel Medium- and Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.000045,
    n2o_factor: 0.000042,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.223710,
    ar5_factor: 10.222450,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "biodiesel-100-biodiesel-passenger-cars": {
    title: "Biodiesel (100%) - Biodiesel Passenger Cars",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000011,
    n2o_factor: 0.000023,
    biogenic_co2_factor: 9.450000,
    ar4_factor: 0.006986,
    ar5_factor: 0.006278,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "biodiesel-100-biodiesel-light-duty-vehicles": {
    title: "Biodiesel (100%) - Biodiesel Light-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000008,
    n2o_factor: 0.000016,
    biogenic_co2_factor: 9.450000,
    ar4_factor: 0.005030,
    ar5_factor: 0.004520,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "biodiesel-100-biodiesel-medium-and-heavy-duty-vehicles": {
    title: "Biodiesel (100%) - Biodiesel Medium- and Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000044,
    n2o_factor: 0.000044,
    biogenic_co2_factor: 9.450000,
    ar4_factor: 0.014212,
    ar5_factor: 0.012892,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "compressed-natural-gas-cng-light-duty-vehicles": {
    title: "Compressed Natural Gas - CNG Light-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.407239,
    ch4_factor: 0.089313,
    n2o_factor: 0.006059,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 4.445710,
    ar5_factor: 4.513695,
    unit: "scf",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "compressed-natural-gas-cng-medium-and-heavy-duty-vehicles": {
    title: "Compressed Natural Gas - CNG Medium- and Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.407239,
    ch4_factor: 0.129419,
    n2o_factor: 0.011520,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 7.075674,
    ar5_factor: 7.083771,
    unit: "scf",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "ethanol-100-ethanol-light-duty-vehicles": {
    title: "Ethanol (100%) - Ethanol Light-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000891,
    n2o_factor: 0.001085,
    biogenic_co2_factor: 5.750000,
    ar4_factor: 0.345724,
    ar5_factor: 0.312579,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "ethanol-100-ethanol-medium-and-heavy-duty-vehicles": {
    title: "Ethanol (100%) - Ethanol Medium- and Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.001734,
    n2o_factor: 0.001540,
    biogenic_co2_factor: 5.750000,
    ar4_factor: 0.502260,
    ar5_factor: 0.456641,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-hybrid-gasoline-passenger-cars": {
    title: "Motor Gasoline - Hybrid (Gasoline) Passenger Cars",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000539,
    n2o_factor: 0.000112,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.826905,
    ar5_factor: 8.824820,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-agricultural-equipment": {
    title: "Motor Gasoline - Gasoline Agricultural Equipment",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.001260,
    n2o_factor: 0.000220,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.877060,
    ar5_factor: 8.873580,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-diesel-agricultural-equipment": {
    title: "Diesel Fuel - Diesel Agricultural Equipment",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.001440,
    n2o_factor: 0.000260,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.323480,
    ar5_factor: 10.319220,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-ships-and-boats": {
    title: "Motor Gasoline - Gasoline Ships and Boats",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000640,
    n2o_factor: 0.000220,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.861560,
    ar5_factor: 8.856220,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-diesel-ships-and-boats": {
    title: "Diesel Fuel - Diesel Ships and Boats",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.000060,
    n2o_factor: 0.000450,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.345600,
    ar5_factor: 10.330930,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "jet-fuel-jet-fuel-aircraft": {
    title: "Jet Fuel - Jet Fuel Aircraft",
    heat_content: 0.000000,
    co2_factor: 9.750000,
    ch4_factor: 0.000000,
    n2o_factor: 0.000300,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 9.839400,
    ar5_factor: 9.829500,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "aviation-gasoline-aviation-gasoline-aircraft": {
    title: "Aviation Gasoline - Aviation Gasoline Aircraft",
    heat_content: 0.000000,
    co2_factor: 8.310000,
    ch4_factor: 0.007060,
    n2o_factor: 0.000110,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.519280,
    ar5_factor: 8.536830,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-gasoline-motorcycles": {
    title: "Motor Gasoline - Gasoline Motorcycles",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.003360,
    n2o_factor: 0.000345,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.966810,
    ar5_factor: 8.965505,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "motor-gasoline-other-gasoline-non-road-vehicles": {
    title: "Motor Gasoline - Other Gasoline Non-Road Vehicles",
    heat_content: 0.000000,
    co2_factor: 8.780000,
    ch4_factor: 0.000500,
    n2o_factor: 0.000220,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 8.858060,
    ar5_factor: 8.852300,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "diesel-fuel-other-diesel-non-road-vehicles": {
    title: "Diesel Fuel - Other Diesel Non-Road Vehicles",
    heat_content: 0.000000,
    co2_factor: 10.210000,
    ch4_factor: 0.000570,
    n2o_factor: 0.000260,
    biogenic_co2_factor: 0.000000,
    ar4_factor: 10.301730,
    ar5_factor: 10.294860,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  },
  "biodiesel-100-biodiesel-medium-and-heavy-duty-vehicles": {
    title: "Biodiesel (100%) - Biodiesel Medium- and Heavy-duty Vehicles",
    heat_content: 0.000000,
    co2_factor: 0.000000,
    ch4_factor: 0.000029,
    n2o_factor: 0.000029,
    biogenic_co2_factor: 9.450000,
    ar4_factor: 0.009529,
    ar5_factor: 0.008644,
    unit: "gallons",
    source: "EPA, \"Emission Factors for Greenhouse Gas Inventories\", March 9, 2018 (https://www.epa.gov/climateleadership/center-corporate-climate-leadership-ghg-emission-factors-hub); WRI, GHG Protocol - Emission Factors from Cross-Sector Tools, April 2014"
  }
};
