"""Product catalog: vehicle fitment data, spec option groups, and product lookups.

Products themselves (name, price, image, stock, kind) live in the database
"products" collection and are managed from the admin dashboard. This module
holds the fixed option data and turns a cart line (product + chosen options)
into a name and price, so the browser and /checkout always agree.

The same option data is sent to the browser via ``frontend_config()``.
"""

from i18n import _

# Popular makes and models on Kenyan roads (largely Japanese used imports,
# plus the common European, Korean and pickup/SUV models).
MAKES_AND_MODELS = {
    "Toyota": ["Vitz", "Passo", "Belta", "Axio", "Fielder", "Corolla", "Premio", "Allion", "Auris", "Prius",
               "Probox", "Succeed", "Wish", "Sienta", "Noah", "Voxy", "Harrier", "RAV4", "Rush", "C-HR",
               "Mark X", "Crown", "Land Cruiser Prado", "Land Cruiser", "Fortuner", "Hilux", "Hiace"],
    "Nissan": ["March", "Note", "Tiida", "Sylphy", "Bluebird", "Wingroad", "AD Van", "Juke", "Dualis",
               "Qashqai", "X-Trail", "Murano", "Teana", "Serena", "Caravan", "Navara", "Patrol"],
    "Subaru": ["Impreza", "XV", "Forester", "Legacy", "Outback", "Levorg", "Exiga"],
    "Honda": ["Fit", "Grace", "Insight", "Vezel", "Freed", "Stream", "Civic", "Accord", "CR-V"],
    "Mazda": ["Demio", "Verisa", "Axela", "Atenza", "Premacy", "CX-3", "CX-5", "BT-50"],
    "Mitsubishi": ["Mirage", "Colt", "Lancer", "Galant", "RVR", "ASX", "Outlander", "Pajero", "L200"],
    "Suzuki": ["Alto", "Wagon R", "Swift", "SX4", "Ertiga", "Vitara", "Jimny", "Every", "Carry"],
    "Daihatsu": ["Mira", "Move", "Boon", "Terios", "Hijet"],
    "Isuzu": ["D-Max", "MU-X", "Elf"],
    "Lexus": ["IS", "NX", "RX", "GX", "LX"],
    "Volkswagen": ["Polo", "Golf", "Jetta", "Passat", "Tiguan", "Touareg", "Amarok"],
    "Mercedes-Benz": ["A-Class", "C-Class", "E-Class", "S-Class", "GLA", "GLC", "GLE", "ML-Class", "Sprinter"],
    "BMW": ["1 Series", "3 Series", "5 Series", "X1", "X3", "X5", "X6"],
    "Audi": ["A3", "A4", "A6", "Q3", "Q5", "Q7"],
    "Land Rover": ["Freelander", "Discovery", "Discovery Sport", "Defender", "Range Rover Evoque",
                   "Range Rover Sport", "Range Rover"],
    "Volvo": ["V40", "S60", "XC60", "XC90"],
    "Peugeot": ["208", "301", "308", "508", "2008", "3008", "5008"],
    "Ford": ["Fiesta", "Focus", "Kuga", "Everest", "Ranger"],
    "Hyundai": ["i10", "i20", "Accent", "Elantra", "Creta", "ix35", "Tucson", "Santa Fe"],
    "Kia": ["Picanto", "Rio", "Cerato", "Sportage", "Sorento"],
}

# Price adjustment (KSh) applied to vehicle-specific parts, by make
MAKE_PRICE_MODIFIERS = {
    "Mercedes-Benz": 2500.00,
    "BMW": 2500.00,
    "Audi": 2500.00,
    "Land Rover": 2500.00,
    "Lexus": 2500.00,
    "Volvo": 2500.00,
    "Toyota": 400.00,
    "Subaru": 400.00,
    "Nissan": -200.00,
    "Mazda": -200.00,
}

# Spec-based product kinds: each has exactly two option groups, chosen in the modal.
# "label" is used in the product name, "hint" is the longer dropdown text.
SPEC_KINDS = {
    "battery": {
        "admin_label": "Battery (voltage + type)",
        "title": "Select Battery Specifications",
        "description": "Select your desired voltage, capacity, and battery build standard.",
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
    "coil_springs": {
        "admin_label": "Coil springs (thickness + position)",
        "title": "Select Coil Spring Specifications",
        "description": "Select the spring wire thickness duty and axle installation position.",
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
    "motor_oil": {
        "admin_label": "Motor oil (brand + viscosity)",
        "title": "Select Motor Oil Specifications",
        "description": "Select your preferred oil brand and engine viscosity type.",
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

# What the admin can choose as a product's "kind"
PRODUCT_KINDS = {
    "vehicle": "Vehicle-specific (customer picks make & model)",
    "simple": "Simple (no options)",
    **{kind: spec["admin_label"] for kind, spec in SPEC_KINDS.items()},
}

# Images shipped in static/images that the admin can pick instead of a URL
BUILTIN_IMAGES = ["brakepad.jpg", "air_filter.jpg", "motor_oil.jpg", "wheel.jpg",
                  "side_mirror.jpg", "battery.jpg", "springs.jpg"]

DEFAULT_STOCK = 20

# Seeded into an empty products collection on first run
DEFAULT_PRODUCTS = [
    {"id": "p1", "name": "Brake Pad", "price": 3500.00, "image": "brakepad.jpg", "kind": "vehicle"},
    {"id": "p2", "name": "Air Filter", "price": 2200.00, "image": "air_filter.jpg", "kind": "vehicle"},
    {"id": "p3", "name": "Motor Oil", "price": 4500.00, "image": "motor_oil.jpg", "kind": "motor_oil"},
    {"id": "p4", "name": "Car Wheel", "price": 12000.00, "image": "wheel.jpg", "kind": "vehicle"},
    {"id": "p5", "name": "Side Mirror", "price": 3200.00, "image": "side_mirror.jpg", "kind": "vehicle"},
    {"id": "p6", "name": "Car Battery", "price": 9500.00, "image": "battery.jpg", "kind": "battery"},
    {"id": "p7", "name": "Coil Springs", "price": 6000.00, "image": "springs.jpg", "kind": "coil_springs"},
]


def seed_products(db):
    """Create the default products if the products collection is empty."""
    products = db.collection('products')
    if next(iter(products.limit(1).stream()), None) is not None:
        return False
    for i, p in enumerate(DEFAULT_PRODUCTS):
        data = {k: v for k, v in p.items() if k != 'id'}
        data.update({"stock": DEFAULT_STOCK, "description": "", "active": True, "sort": i})
        products.document(p["id"]).set(data)
    return True


def list_products(db, include_inactive=False):
    """All products as dicts (with "id"), sorted for display."""
    products = []
    for snap in db.collection('products').stream():
        p = snap.to_dict()
        p["id"] = snap.id
        if include_inactive or p.get("active", True):
            products.append(p)
    return sorted(products, key=lambda p: (p.get("sort", 1000), p.get("name", "").lower()))


def get_product(db, product_id):
    if not isinstance(product_id, str) or not product_id:
        return None
    snap = db.collection('products').document(product_id).get()
    if not snap.exists:
        return None
    p = snap.to_dict()
    p["id"] = snap.id
    return p


def resolve_variant(product, options):
    """Turn a product + chosen options into (variant_key, name, unit_price), or raise ValueError.

    options: {"make", "model"} for vehicle parts, {"first", "second"} for spec kinds, {} for simple.
    Must stay in sync with currentSelection() in static/cart.js.
    """
    options = options if isinstance(options, dict) else {}
    kind = product.get("kind", "simple")
    base_price = float(product.get("price", 0))

    if kind == "vehicle":
        make, model = options.get("make"), options.get("model")
        if make not in MAKES_AND_MODELS or model not in MAKES_AND_MODELS[make]:
            raise ValueError(_("Choose a valid make and model for {name}", name=product['name']))
        return f"{make}|{model}", f"{make} {model} {product['name']}", base_price + MAKE_PRICE_MODIFIERS.get(make, 0.00)

    spec = SPEC_KINDS.get(kind)
    if spec:
        first_group, second_group = spec["groups"]
        first, second = first_group["options"].get(options.get("first")), second_group["options"].get(options.get("second"))
        if not first or not second:
            raise ValueError(_("Choose {first} and {second} for {name}", first=_(first_group['label']),
                               second=_(second_group['label']), name=product['name']))
        name = f"{product['name']} - {first['label']} / {second['label']}"
        return f"{options['first']}|{options['second']}", name, base_price + first["modifier"] + second["modifier"]

    return "", product["name"], base_price


def frontend_config():
    """Data the browser needs to build the selection modal and price preview."""
    return {
        "makes": MAKES_AND_MODELS,
        "makeModifiers": MAKE_PRICE_MODIFIERS,
        "specKinds": SPEC_KINDS,
    }
