"""Product catalog: the single source of truth for parts, options and prices.

The frontend receives the same data via ``frontend_config()`` so prices shown
in the browser always match what the server charges at checkout.
"""

MAKES_AND_MODELS = {
    "Toyota": ["Vitz", "Fielder", "Corolla", "Harrier", "Land Cruiser", "Probox"],
    "Nissan": ["X-Trail", "Note", "Sylphy", "Wingroad"],
    "Subaru": ["Impreza", "Forester", "Legacy"],
    "Honda": ["Fit", "Civic", "CR-V"],
    "Mazda": ["Demio", "Axela", "CX-5"],
    "Mitsubishi": ["Outlander", "Lancer", "Pajero"],
    "Volkswagen": ["Golf", "Tiguan", "Polo", "Passat"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
    "Hyundai": ["Tucson", "Elantra", "Santa Fe"]
}

# Price adjustment (KSh) applied to vehicle-specific parts, by make
MAKE_PRICE_MODIFIERS = {
    "Mercedes-Benz": 2500.00,
    "BMW": 2500.00,
    "Toyota": 400.00,
    "Subaru": 400.00,
    "Nissan": -200.00,
    "Mazda": -200.00,
}

# Spec-based parts: each has exactly two option groups, chosen in the modal.
# "label" is used in the product name, "hint" is the longer dropdown text.
SPEC_PRODUCTS = {
    "p6": {  # Car Battery
        "title": "Select Battery Specifications",
        "description": "Select your desired voltage, capacity, and battery build standard.",
        "name_format": "{second} Battery ({first})",
        "groups": [
            {
                "label": "Voltage / Capacity",
                "placeholder": "-- Choose Voltage & Capacity --",
                "options": {
                    "12v_45ah": {"label": "12V 45Ah", "hint": "12V 45Ah (Small Hatchback)", "modifier": -1500.00},
                    "12v_65ah": {"label": "12V 65Ah", "hint": "12V 65Ah (Medium Sedan)", "modifier": 0.00},
                    "12v_75ah": {"label": "12V 75Ah", "hint": "12V 75Ah (SUV / Crossover)", "modifier": 1500.00},
                    "12v_90ah": {"label": "12V 90Ah", "hint": "12V 90Ah (Large SUV / Diesel)", "modifier": 3500.00},
                    "24v_100ah": {"label": "24V 100Ah", "hint": "24V 100Ah (Commercial Truck)", "modifier": 7500.00},
                },
            },
            {
                "label": "Battery Type",
                "placeholder": "-- Choose Battery Type --",
                "options": {
                    "maintenance_free": {"label": "Maintenance-Free (SLA)", "hint": "Maintenance-Free (SLA)", "modifier": 0.00},
                    "agm": {"label": "AGM (Start-Stop)", "hint": "AGM (Start-Stop / Premium)", "modifier": 4000.00},
                    "efb": {"label": "EFB", "hint": "EFB (Enhanced Flooded)", "modifier": 2000.00},
                },
            },
        ],
    },
    "p7": {  # Coil Springs
        "title": "Select Coil Spring Specifications",
        "description": "Select the spring wire thickness duty and axle installation position.",
        "name_format": "{first} Coil Springs ({second})",
        "groups": [
            {
                "label": "Spring Type / Thickness",
                "placeholder": "-- Choose Type & Wire Thickness --",
                "options": {
                    "standard_14mm": {"label": "Standard Duty (14mm)", "hint": "Standard Duty (14mm wire)", "modifier": 0.00},
                    "heavy_duty_16mm": {"label": "Heavy Duty (16mm)", "hint": "Heavy Duty (16mm wire - Load Carrying)", "modifier": 1500.00},
                    "lowered_12mm": {"label": "Lowered / Sports (12mm)", "hint": "Lowered / Sports (12mm wire - Performance)", "modifier": 2500.00},
                },
            },
            {
                "label": "Position / Axle",
                "placeholder": "-- Choose Position --",
                "options": {
                    "front": {"label": "Front Axle", "hint": "Front Axle (Pair)", "modifier": 0.00},
                    "rear": {"label": "Rear Axle", "hint": "Rear Axle (Pair)", "modifier": -500.00},
                },
            },
        ],
    },
    "p3": {  # Motor Oil
        "title": "Select Motor Oil Specifications",
        "description": "Select your preferred oil brand and engine viscosity type.",
        "name_format": "{first} {second} Motor Oil",
        "groups": [
            {
                "label": "Oil Brand",
                "placeholder": "-- Choose Brand --",
                "options": {
                    "castrol": {"label": "Castrol", "hint": "Castrol", "modifier": 400.00},
                    "shell": {"label": "Shell Helix", "hint": "Shell Helix", "modifier": 200.00},
                    "mobil": {"label": "Mobil 1", "hint": "Mobil 1", "modifier": 500.00},
                    "total": {"label": "Total Quartz", "hint": "Total Quartz", "modifier": 0.00},
                },
            },
            {
                "label": "Oil Type & Viscosity",
                "placeholder": "-- Choose Oil Type --",
                "options": {
                    "synthetic": {"label": "Fully Synthetic (5W-30)", "hint": "Fully Synthetic (5W-30) - Premium Passenger", "modifier": 1500.00},
                    "semi_synthetic": {"label": "Semi-Synthetic (10W-40)", "hint": "Semi-Synthetic (10W-40) - Standard Daily", "modifier": 0.00},
                    "heavy_duty_4wd": {"label": "Heavy Duty / 4WD (15W-40)", "hint": "Heavy Duty / 4WD (15W-40) - SUV & Diesel", "modifier": 1000.00},
                },
            },
        ],
    },
}

BASE_PRODUCTS = [
    {"id": "p1", "name": "Brake Pad", "price": 3500.00, "image": "brakepad.jpg"},
    {"id": "p2", "name": "Air Filter", "price": 2200.00, "image": "air_filter.jpg"},
    {"id": "p3", "name": "Motor Oil", "price": 4500.00, "image": "motor_oil.jpg"},
    {"id": "p4", "name": "Car Wheel", "price": 12000.00, "image": "wheel.jpg"},
    {"id": "p5", "name": "Side Mirror", "price": 3200.00, "image": "side_mirror.jpg"},
    {"id": "p6", "name": "Car Battery", "price": 9500.00, "image": "battery.jpg"},
    {"id": "p7", "name": "Coil Springs", "price": 6000.00, "image": "springs.jpg"},
]


def vehicle_product_id(base_id, make, model):
    """e.g. ("p1", "Toyota", "Land Cruiser") -> "p1_toyota_land_cruiser". Must match cart.js."""
    return f"{base_id}_{make.lower()}_{model.lower().replace(' ', '_').replace('-', '_')}"


def _build_products():
    products = {}
    for bp in BASE_PRODUCTS:
        products[bp["id"]] = bp
        spec = SPEC_PRODUCTS.get(bp["id"])
        if spec:
            first, second = spec["groups"]
            for a_key, a_info in first["options"].items():
                for b_key, b_info in second["options"].items():
                    pid = f"{bp['id']}_{a_key}_{b_key}"
                    products[pid] = {
                        "id": pid,
                        "name": spec["name_format"].format(first=a_info["label"], second=b_info["label"]),
                        "price": bp["price"] + a_info["modifier"] + b_info["modifier"],
                        "image": bp["image"],
                    }
        else:  # vehicle-specific part
            for make, models in MAKES_AND_MODELS.items():
                for model in models:
                    pid = vehicle_product_id(bp["id"], make, model)
                    products[pid] = {
                        "id": pid,
                        "name": f"{make} {model} {bp['name']}",
                        "price": bp["price"] + MAKE_PRICE_MODIFIERS.get(make, 0.00),
                        "image": bp["image"],
                    }
    return products


# Every purchasable product id -> product, including all specific variants
PRODUCTS = _build_products()


def get_product(product_id):
    return PRODUCTS.get(product_id)


def frontend_config():
    """Data the browser needs to build the selection modal and price preview."""
    return {
        "makes": MAKES_AND_MODELS,
        "makeModifiers": MAKE_PRICE_MODIFIERS,
        "specProducts": SPEC_PRODUCTS,
    }
