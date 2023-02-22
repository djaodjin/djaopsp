// Scope 1 Mobile Combustion and Scope 3 Transportation
Vue.prototype.$activity_types = {
  "fuel-use": {
      title: "Fuel Use",
  },
  "distance": {
      title: "Distance"
  },
  "passenger-distance": {
      title: "Passenger Distance",
  },
  "vehicle-distance": {
      title: "Vehicle Distance",
  },
  "weight-distance": {
      title: "Weight Distance"
  },
};


Vue.prototype.$calculation_approach_types = {
    "purchased-electricity-location-based": {
        title: "Purchased Electricity - Location Based",
    },
    "purchased-electricity-market-based": {
        title: "Purchased Electricity - Market Based",
    },
    "heat-steam": {
        title: "Heat/Steam",
    },
};


Vue.prototype.$emission_factor_dataset_types = {
    "us-epa": {
        title: "US EPA",
    },
    "uk-defra": {
        title: "UK DEFRA",
    },
};


Vue.prototype.$fuel_types = {
    "motor-gasoline": {
        title: "Motor Gasoline",
    },
    "diesel-fuel": {
        title: "Diesel Fuel",
    },
    "biodiesel": {
        title: "Biodiesel (100%)",
    },
    "compressed-natural-gas": {
        title: "Compressed Natural Gas",
    },
    "ethanol": {
        title: "Ethanol (100%)",
    },
    "jet-fuel": {
        title: "Jet Fuel",
    },
    "aviation-gasoline": {
        title: "Aviation Gasoline",
    },
};


Vue.prototype.$mode_of_transport_types = {
    "car": {
        title: "Car",
    },
    "air": {
        title: "Air",
    },
    "bus": {
        title: "Bus",
    },
    "rail": {
        title: "Rail",
    },
    "ferry": {
        title: "Ferry",
    },
};


Vue.prototype.$scope3_category_types = {
    "upstream-td": {
        title: "Upstream T&D"
    },
    "business-travel": {
        title: "Business Travel"
    },
    "employee-commute": {
        title: "Employee Commute"
    },
};


Vue.prototype.$type_of_emission_factor_types = {
    "residual-mix": {
        title: "Residual Mix",
    },
    "grid-average-location-based": {
        title: "Grid Average/Location Based",
    },
};

// Scope 1 Mobile Combustion
Vue.prototype.$vehicle_types = {
    "gasoline-passenger-cars": {
        title: "Gasoline Passenger Cars",
    },
    "gasoline-light-duty-trucks": {
        title: "Gasoline Light-duty Trucks (Vans, Pickup Trucks, SUVs)",
    },
    "gasoline-heavy-duty-vehicles": {
        title: "Gasoline Heavy-duty Vehicles",
    },
    "hybrid-gasoline-passenger-cars": {
        title: "Hybrid (Gasoline) Passenger Cars",
    },
    "gasoline-agricultural-equipment": {
        title: "Gasoline Agricultural Equipment",
    },
    "gasoline-ships-and-boats": {
        title: "Gasoline Ships and Boats",
    },
    "gasoline-motorcycles": {
        title: "Gasoline Motorcycles",
    },
    "other-gasoline-non-road-vehicles": {
        title: "Other Gasoline Non-Road Vehicles",
    },
    "diesel-passenger-cars": {
        title: "Diesel Passenger Cars"
    },
    "diesel-light-duty-trucks": {
        title: "Diesel Light-duty Trucks"
    },
    "diesel-medium-and-heavy-duty-vehicles": {
        title: "Diesel Medium- and Heavy-duty Vehicles"
    },
    "diesel-agricultural-equipment": {
        title: "Diesel Agricultural Equipment"
    },
    "diesel-ships-and-boats": {
        title: "Diesel Ships and Boats"
    },
    "diesel-medium-and-heavy-duty-vehicles": {
        title: "Diesel Medium- and Heavy-duty Vehicles"
    },
    "other-diesel-non-road-vehicles": {
        title: "Other Diesel Non-Road Vehicles"
    },
    "biodiesel-passenger-cars": {
        title: "Biodiesel Passenger Cars"
    },
    "biodiesel-light-duty-vehicles": {
        title: "Biodiesel Light-duty Vehicles"
    },
    "biodiesel-medium-and-heavy-duty-vehicles": {
        title: "Biodiesel Medium- and Heavy-duty Vehicles"
    },
    "biodiesel-medium-and-heavy-duty-vehicles": {
        title: "Biodiesel Medium- and Heavy-duty Vehicles"
    },
    "cng-light-duty-vehicles": {
        title: "CNG Light-duty Vehicles"
    },
    "cng-medium-and-heavy-duty-vehicles": {
        title: "CNG Medium- and Heavy-duty Vehicles"
    },
    "ethanol-light-duty-vehicles": {
        title: "Ethanol Light-duty Vehicles"
    },
    "ethanol-medium-and-heavy-duty-vehicles": {
        title: "Ethanol Medium- and Heavy-duty Vehicles"
    },
    "jet-fuel-aircraft": {
        title: "Jet Fuel Aircraft"
    },
    "aviation-gasoline-aircraft": {
        title: "Aviation Gasoline Aircraft"
    },
};
