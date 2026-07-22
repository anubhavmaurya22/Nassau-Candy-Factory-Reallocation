"""
Static reference data for the Nassau Candy Distributor project:
- Factory locations
- Product -> current Factory assignment
- US State / Canadian Province centroids (used to estimate distance
  from each factory to each customer, since we don't have exact
  city-level geocoding available offline)
"""

# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
FACTORIES = {
    "Lot's O' Nuts":       {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's":     {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack":         {"lat": 48.119140, "lon": -96.181150},
    "Secret Factory":      {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory":   {"lat": 35.117500, "lon": -89.971107},
}

# ---------------------------------------------------------------------------
# Current Product -> Factory assignment (as given in the project brief)
# ---------------------------------------------------------------------------
PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise":  "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":          "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":     "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":         "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel":  "Wicked Choccy's",
    "Laffy Taffy":                        "Sugar Shack",
    "SweeTARTS":                          "Sugar Shack",
    "Nerds":                              "Sugar Shack",
    "Fun Dip":                            "Sugar Shack",
    "Fizzy Lifting Drinks":               "Sugar Shack",
    "Everlasting Gobstopper":             "Secret Factory",
    "Hair Toffee":                        "The Other Factory",
    "Lickable Wallpaper":                 "Secret Factory",
    "Wonka Gum":                          "Secret Factory",
    "Kazookles":                          "The Other Factory",
}

PRODUCT_DIVISION = {
    "Wonka Bar - Nutty Crunch Surprise":  "Chocolate",
    "Wonka Bar - Fudge Mallows":          "Chocolate",
    "Wonka Bar -Scrumdiddlyumptious":     "Chocolate",
    "Wonka Bar - Milk Chocolate":         "Chocolate",
    "Wonka Bar - Triple Dazzle Caramel":  "Chocolate",
    "Laffy Taffy":                        "Sugar",
    "SweeTARTS":                          "Sugar",
    "Nerds":                              "Sugar",
    "Fun Dip":                            "Sugar",
    "Fizzy Lifting Drinks":               "Other",
    "Everlasting Gobstopper":             "Sugar",
    "Hair Toffee":                        "Sugar",
    "Lickable Wallpaper":                 "Other",
    "Wonka Gum":                          "Other",
    "Kazookles":                          "Other",
}

# ---------------------------------------------------------------------------
# Ship Mode -> assumed standardized lead time (in days).
#
# IMPORTANT DATA QUALITY NOTE:
# The raw Order Date / Ship Date columns in this dataset are NOT usable to
# compute real lead time. Order IDs carry year prefixes 2021-2024, but the
# Order Date column only spans 2024-2025, and Ship Date spans 2026-2030 -
# three inconsistent timelines. This is a well-known public retail dataset
# ("Superstore") whose date fields have been re-randomized for this
# assignment, decoupling Order Date and Ship Date from each other and from
# reality. Naive (Ship Date - Order Date) averages ~1,320 days, which is
# obviously not a real shipping lead time.
#
# Instead, we treat Ship Mode as the ground-truth proxy for delivery speed,
# using an industry-standard mapping. This is called out explicitly as a
# limitation/finding in the research paper.
# ---------------------------------------------------------------------------
SHIP_MODE_LEAD_DAYS = {
    "Same Day":       1,
    "First Class":    3,
    "Second Class":   5,
    "Standard Class": 7,
}

# ---------------------------------------------------------------------------
# Distance-based adjustment assumptions.
#
# The raw data carries NO real link between factory location and delivery
# speed/cost (Ship Mode was chosen independently of which factory produced
# the item). To make factory reassignment analysis meaningful, we apply two
# standard, disclosed logistics assumptions:
#
#  1. Ground transit adds roughly 1 extra day of lead time per 500 miles
#     of distance beyond the base Ship-Mode speed (typical long-haul
#     trucking average ~500 miles/day).
#  2. Shipping cost scales with distance: $0.015 per unit per 100 miles,
#     subtracted from Gross Profit to get an adjusted, distance-aware
#     profit figure.
#
# These constants are explicitly called out as modeling assumptions in the
# research paper, not measured facts, since the raw dataset does not
# support estimating them empirically.
# ---------------------------------------------------------------------------
MILES_PER_EXTRA_DAY = 500.0
SHIPPING_COST_PER_UNIT_PER_100_MILES = 0.015

# ---------------------------------------------------------------------------
# Approximate centroid coordinates for US states + Canadian provinces
# present in the dataset. Used to estimate factory-to-customer distance.
# ---------------------------------------------------------------------------
STATE_CENTROIDS = {
    "Alabama": (32.806671, -86.791130), "Alaska": (61.370716, -152.404419),
    "Arizona": (33.729759, -111.431221), "Arkansas": (34.969704, -92.373123),
    "California": (36.116203, -119.681564), "Colorado": (39.059811, -105.311104),
    "Connecticut": (41.597782, -72.755371), "Delaware": (39.318523, -75.507141),
    "District of Columbia": (38.897438, -77.026817), "Florida": (27.766279, -81.686783),
    "Georgia": (33.040619, -83.643074), "Idaho": (44.240459, -114.478828),
    "Illinois": (40.349457, -88.986137), "Indiana": (39.849426, -86.258278),
    "Iowa": (42.011539, -93.210526), "Kansas": (38.526600, -96.726486),
    "Kentucky": (37.668140, -84.670067), "Louisiana": (31.169546, -91.867805),
    "Maine": (44.693947, -69.381927), "Maryland": (39.063946, -76.802101),
    "Massachusetts": (42.230171, -71.530106), "Michigan": (43.326618, -84.536095),
    "Minnesota": (45.694454, -93.900192), "Mississippi": (32.741646, -89.678696),
    "Missouri": (38.456085, -92.288368), "Montana": (46.921925, -110.454353),
    "Nebraska": (41.125370, -98.268082), "Nevada": (38.313515, -117.055374),
    "New Hampshire": (43.452492, -71.563896), "New Jersey": (40.298904, -74.521011),
    "New Mexico": (34.840515, -106.248482), "New York": (42.165726, -74.948051),
    "North Carolina": (35.630066, -79.806419), "North Dakota": (47.528912, -99.784012),
    "Ohio": (40.388783, -82.764915), "Oklahoma": (35.565342, -96.928917),
    "Oregon": (44.572021, -122.070938), "Pennsylvania": (40.590752, -77.209755),
    "Rhode Island": (41.680893, -71.511780), "South Carolina": (33.856892, -80.945007),
    "South Dakota": (44.299782, -99.438828), "Tennessee": (35.747845, -86.692345),
    "Texas": (31.054487, -97.563461), "Utah": (40.150032, -111.862434),
    "Vermont": (44.045876, -72.710686), "Virginia": (37.769337, -78.169968),
    "Washington": (47.400902, -121.490494), "West Virginia": (38.491226, -80.954453),
    "Wisconsin": (44.268543, -89.616508), "Wyoming": (42.755966, -107.302490),
    # Canadian provinces (approx centroids)
    "Ontario": (50.000000, -85.000000), "Quebec": (52.939916, -73.549136),
    "British Columbia": (53.726669, -127.647621), "Alberta": (53.933327, -116.576500),
    "Manitoba": (53.760860, -98.813873), "Saskatchewan": (52.939916, -106.450864),
    "Nova Scotia": (44.681999, -63.744312), "New Brunswick": (46.565315, -66.461914),
    "Newfoundland and Labrador": (53.135509, -57.660435),
    "Prince Edward Island": (46.510712, -63.416500),
}
