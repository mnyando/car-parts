"""English / Swahili translations for site text.

Keys are the English strings themselves, so a missing translation just shows
English. Use {name} placeholders for values:

    _('Only {n} left', n=3)          # Python and Jinja templates
    t("Only {n} left", { n: 3 })     # static/cart.js (gets the dict as window.I18N)

The chosen language is stored in the "lang" cookie (set by /lang/<code>).
Product names stay exactly as the admin typed them.
"""
from flask import g, has_request_context, redirect, request, url_for

LANGUAGES = ('en', 'sw')
DEFAULT_LANG = 'en'
COOKIE = 'lang'

SW = {
    # --- Site / navigation
    "Car Parts": "Vipuri vya Magari",
    "Genuine and aftermarket car parts in Nairobi. Order online, pay with M-Pesa.":
        "Vipuri halisi na mbadala vya magari jijini Nairobi. Agiza mtandaoni, lipa kwa M-Pesa.",
    "Language": "Lugha",
    "Close": "Funga",
    "Close menu": "Funga menyu",
    "Open menu": "Fungua menyu",
    "Open cart": "Fungua kikapu",
    "Close cart": "Funga kikapu",
    "Home": "Nyumbani",
    "Shop parts": "Nunua vipuri",
    "Cart": "Kikapu",
    "Admin": "Msimamizi",
    "Contact": "Mawasiliano",
    "Log in": "Ingia",
    "Log out": "Toka",
    "Signed in as {name}": "Umeingia kama {name}",
    "(admin)": "(msimamizi)",
    "Your Cart": "Kikapu Chako",

    # --- Landing
    "Genuine & aftermarket parts — Nairobi": "Vipuri halisi na mbadala — Nairobi",
    "The right part,": "Kipuri sahihi,",
    "delivered fast.": "kinakufikia haraka.",
    "Engine, brakes, electrical and body parts for every make. Order online, pay with M-Pesa.":
        "Vipuri vya injini, breki, umeme na bodi kwa kila aina ya gari. Agiza mtandaoni, lipa kwa M-Pesa.",
    "Browse parts →": "Tazama vipuri →",
    "Genuine & OEM parts": "Vipuri halisi na vya OEM",
    "Nationwide delivery": "Tunasafirisha kote nchini",
    "Pay with M-Pesa": "Lipa kwa M-Pesa",

    # --- Catalog
    "Catalog": "Bidhaa",
    "Parts": "Vipuri",
    "In stock": "Zipo",
    "Only {n} left": "Zimebaki {n} tu",
    "Out of stock": "Zimeisha",
    "Add To Cart": "Weka Kikapuni",
    "No parts available yet. Please check back soon.": "Hakuna vipuri kwa sasa. Tafadhali rudi baadaye.",
    "Your order will be processed and delivered within one hour of placing.":
        "Agizo lako litashughulikiwa na kukufikia ndani ya saa moja baada ya kuagiza.",
    "Make sure you have the total amount for the order during delivery.":
        "Hakikisha una kiasi kamili cha agizo wakati wa kupokea.",
    "In case of any comment or complaint, please reach out to us as fast as possible.":
        "Ukiwa na maoni au malalamiko yoyote, tafadhali wasiliana nasi mapema iwezekanavyo.",
    "Regards, Management": "Wako, Uongozi",

    # --- Selection modal
    "Select Your Vehicle": "Chagua Gari Lako",
    "Select your car make and model to match the exact compatible part for your vehicle.":
        "Chagua aina na modeli ya gari lako ili kupata kipuri kinachofaa gari lako.",
    "Close modal": "Funga dirisha",
    "Make / Manufacturer": "Aina / Mtengenezaji",
    "Model": "Modeli",
    "-- Choose Make --": "-- Chagua Aina --",
    "-- Choose Model --": "-- Chagua Modeli --",
    "Confirm & Add": "Thibitisha na Ongeza",
    "Price: {price}": "Bei: {price}",
    "Please select both Make and Model!": "Tafadhali chagua aina na modeli ya gari!",
    "Please select both {first} and {second}!": "Tafadhali chagua {first} na {second}!",
    # battery
    "Select Battery Specifications": "Chagua Vipimo vya Betri",
    "Select your desired voltage, capacity, and battery build standard.":
        "Chagua volteji, uwezo na aina ya betri unayotaka.",
    "Voltage / Capacity": "Volteji / Uwezo",
    "-- Choose Voltage & Capacity --": "-- Chagua Volteji na Uwezo --",
    "12V 45Ah (Small Hatchback)": "12V 45Ah (Gari Dogo)",
    "12V 65Ah (Medium Sedan)": "12V 65Ah (Saloon ya Wastani)",
    "12V 75Ah (SUV / Crossover)": "12V 75Ah (SUV / Crossover)",
    "12V 90Ah (Large SUV / Diesel)": "12V 90Ah (SUV Kubwa / Dizeli)",
    "24V 100Ah (Commercial Truck)": "24V 100Ah (Lori la Biashara)",
    "Battery Type": "Aina ya Betri",
    "-- Choose Battery Type --": "-- Chagua Aina ya Betri --",
    "Maintenance-Free (SLA)": "Isiyohitaji Matengenezo (SLA)",
    "AGM (Start-Stop / Premium)": "AGM (Start-Stop / Bora)",
    "EFB (Enhanced Flooded)": "EFB (Iliyoboreshwa)",
    # coil springs
    "Select Coil Spring Specifications": "Chagua Vipimo vya Springi",
    "Select the spring wire thickness duty and axle installation position.":
        "Chagua unene wa waya wa springi na upande wa ekseli itakapowekwa.",
    "Spring Type / Thickness": "Aina ya Springi / Unene",
    "-- Choose Type & Wire Thickness --": "-- Chagua Aina na Unene wa Waya --",
    "Standard Duty (14mm wire)": "Kawaida (waya wa 14mm)",
    "Heavy Duty (16mm wire - Load Carrying)": "Mzigo Mzito (waya wa 16mm - Kubeba Mizigo)",
    "Lowered / Sports (12mm wire - Performance)": "Iliyoshushwa / Michezo (waya wa 12mm - Kasi)",
    "Position / Axle": "Upande / Ekseli",
    "-- Choose Position --": "-- Chagua Upande --",
    "Front Axle (Pair)": "Ekseli ya Mbele (Jozi)",
    "Rear Axle (Pair)": "Ekseli ya Nyuma (Jozi)",
    # motor oil
    "Select Motor Oil Specifications": "Chagua Vipimo vya Oili ya Injini",
    "Select your preferred oil brand and engine viscosity type.":
        "Chagua chapa ya oili na uzito (viscosity) unaofaa injini yako.",
    "Oil Brand": "Chapa ya Oili",
    "-- Choose Brand --": "-- Chagua Chapa --",
    "Oil Type & Viscosity": "Aina ya Oili na Uzito",
    "-- Choose Oil Type --": "-- Chagua Aina ya Oili --",
    "Fully Synthetic (5W-30) - Premium Passenger": "Sintetiki Kamili (5W-30) - Magari ya Abiria",
    "Semi-Synthetic (10W-40) - Standard Daily": "Nusu Sintetiki (10W-40) - Matumizi ya Kila Siku",
    "Heavy Duty / 4WD (15W-40) - SUV & Diesel": "Kazi Nzito / 4WD (15W-40) - SUV na Dizeli",

    # --- Cart & checkout (cart.js)
    "Your cart is empty.": "Kikapu chako hakina kitu.",
    "Browse parts": "Tazama vipuri",
    "Total: {amount}": "Jumla: {amount}",
    "Decrease quantity": "Punguza idadi",
    "Increase quantity": "Ongeza idadi",
    "Remove item": "Ondoa bidhaa",
    "Checkout": "Lipia",
    "Clear Cart": "Futa Kikapu",
    "M-Pesa Phone Number": "Nambari ya Simu ya M-Pesa",
    "e.g. 0712345678": "mfano 0712345678",
    "Requesting STK Push...": "Inatuma ombi la malipo...",
    "Back to Cart": "Rudi Kikapuni",
    "Connecting to Safaricom...": "Inaunganisha na Safaricom...",
    "Check your phone": "Angalia simu yako",
    "Enter your M-Pesa PIN on {phone} to pay {amount}.": "Weka PIN yako ya M-Pesa kwenye {phone} ili kulipa {amount}.",
    "Waiting for payment confirmation...": "Inasubiri uthibitisho wa malipo...",
    "Payment received": "Malipo yamepokelewa",
    "Thank you! Your order {reference} is confirmed and will be delivered shortly.":
        "Asante! Agizo lako {reference} limethibitishwa na litakufikia hivi karibuni.",
    "Continue Shopping": "Endelea Kununua",
    "Payment not completed": "Malipo hayajakamilika",
    "Still waiting": "Bado tunasubiri",
    "Try Again": "Jaribu Tena",
    "Please enter a valid Safaricom number, e.g. 0712345678 or 254712345678.":
        "Tafadhali weka nambari sahihi ya Safaricom, mfano 0712345678 au 254712345678.",
    "Failed to start checkout": "Imeshindwa kuanza malipo",
    "Error: {message}": "Hitilafu: {message}",
    "The payment request was cancelled on your phone. Your cart has been kept.":
        "Ombi la malipo lilighairiwa kwenye simu yako. Kikapu chako bado kipo.",
    "The payment did not go through (e.g. wrong PIN, insufficient funds or timeout). Your cart has been kept.":
        "Malipo hayakufaulu (k.m. PIN si sahihi, salio halitoshi au muda umeisha). Kikapu chako bado kipo.",
    "We received a payment that doesn't match the order total. Please contact us with order reference {reference}.":
        "Tumepokea malipo yasiyolingana na jumla ya agizo. Tafadhali wasiliana nasi ukitaja nambari ya agizo {reference}.",
    "We haven't received confirmation yet. If you completed the payment, please contact us with order reference {reference}.":
        "Bado hatujapokea uthibitisho. Ikiwa ulikamilisha malipo, tafadhali wasiliana nasi ukitaja nambari ya agizo {reference}.",

    # --- Checkout errors from the server
    "Enter a valid Safaricom number, e.g. 0712345678 or 254712345678":
        "Weka nambari sahihi ya Safaricom, mfano 0712345678 au 254712345678",
    "Your cart is empty": "Kikapu chako hakina kitu",
    "Too many items in cart": "Bidhaa ni nyingi mno kwenye kikapu",
    "Invalid cart item": "Bidhaa batili kwenye kikapu",
    "Product not found: {id}": "Bidhaa haipatikani: {id}",
    "Invalid quantity": "Idadi si sahihi",
    "Quantity must be between 1 and {max}": "Idadi lazima iwe kati ya 1 na {max}",
    "Only {n} {name} left in stock": "Zimebaki {name} {n} tu",
    "{name} is out of stock": "{name} zimeisha",
    "Choose a valid make and model for {name}": "Chagua aina na modeli sahihi ya gari kwa {name}",
    "Choose {first} and {second} for {name}": "Chagua {first} na {second} kwa {name}",
    "Could not reach M-Pesa, please try again": "Imeshindwa kufikia M-Pesa, tafadhali jaribu tena",
    "M-Pesa did not accept the request": "M-Pesa haikukubali ombi",

    # --- Footer
    "Nairobi Office": "Ofisi ya Nairobi",
    "Phone": "Simu",
    "Email": "Barua pepe",
    "Hours": "Saa za Kazi",
    "Mon - Fri: 8:00 AM - 6:00 PM": "Jumatatu - Ijumaa: Saa 2:00 asubuhi - Saa 12:00 jioni",
    "Sat: Evening Only": "Jumamosi: Jioni Pekee",
    "© {year} Car Parts. All rights reserved.": "© {year} Vipuri vya Magari. Haki zote zimehifadhiwa.",

    # --- Accounts
    "Account": "Akaunti",
    "Log in to browse parts and order.": "Ingia ili kutazama vipuri na kuagiza.",
    "Password": "Nenosiri",
    "New here?": "Mgeni hapa?",
    "Create an account": "Fungua akaunti",
    "Sign up to browse parts and pay with M-Pesa.": "Jisajili ili kutazama vipuri na kulipa kwa M-Pesa.",
    "Full name": "Jina kamili",
    "M-Pesa phone (optional)": "Simu ya M-Pesa (si lazima)",
    "Confirm password": "Thibitisha nenosiri",
    "Create account": "Fungua akaunti",
    "Already have an account?": "Tayari una akaunti?",
    "Please enter your name.": "Tafadhali weka jina lako.",
    "Please enter a valid email address.": "Tafadhali weka barua pepe sahihi.",
    "Password must be at least {n} characters.": "Nenosiri lazima liwe na herufi {n} au zaidi.",
    "Passwords do not match.": "Manenosiri hayalingani.",
    "An account with that email already exists. Please log in.": "Tayari kuna akaunti yenye barua pepe hiyo. Tafadhali ingia.",
    "Incorrect email or password.": "Barua pepe au nenosiri si sahihi.",
    "Please log in to continue": "Tafadhali ingia ili kuendelea",
    "Your session expired, please refresh the page": "Muda wa kipindi umeisha, tafadhali pakia ukurasa upya",

    # --- Error pages
    "Error {code}": "Hitilafu {code}",
    "Something went wrong": "Kuna tatizo",
    "Your session may have expired. Please go back and try again.":
        "Huenda muda wa kipindi chako umeisha. Tafadhali rudi nyuma ujaribu tena.",
    "Access denied": "Huna ruhusa",
    "You don't have permission to view this page.": "Huna ruhusa ya kuona ukurasa huu.",
    "Page not found": "Ukurasa haupatikani",
    "The page you're looking for doesn't exist.": "Ukurasa unaoutafuta haupo.",
    "Back to home": "Rudi nyumbani",

    # --- Admin
    "Dashboard": "Dashibodi",
    "Products & stock": "Bidhaa na hisa",
    "Orders": "Maagizo",
    "Users": "Watumiaji",
    "View shop →": "Tazama duka →",
    "Products": "Bidhaa",
    "Low / out of stock": "Chache / zimeisha",
    "Pending orders": "Maagizo yanayosubiri",
    "Paid orders": "Maagizo yaliyolipwa",
    "Revenue (paid)": "Mapato (yaliyolipwa)",
    "Needs restocking": "Zinahitaji kuongezwa",
    "{n} or fewer left": "Zimebaki {n} au chache",
    "Product": "Bidhaa",
    "Stock": "Hisa",
    "Set stock": "Weka hisa",
    "New stock for {name}": "Hisa mpya ya {name}",
    "Stock for {name}": "Hisa ya {name}",
    "hidden": "imefichwa",
    "Save": "Hifadhi",
    "All products are well stocked.": "Bidhaa zote zina hisa ya kutosha.",
    "Recent orders": "Maagizo ya hivi karibuni",
    "All orders →": "Maagizo yote →",
    "Date": "Tarehe",
    "Reference": "Kumbukumbu",
    "Customer": "Mteja",
    "Items": "Bidhaa",
    "Amount": "Kiasi",
    "Status": "Hali",
    "Receipt": "Risiti",
    "No orders yet.": "Bado hakuna maagizo.",
    "All": "Zote",
    "pending": "inasubiri",
    "paid": "imelipwa",
    "cancelled": "imeghairiwa",
    "failed": "imeshindwa",
    "amount mismatch": "kiasi hakilingani",
    "+ Add product": "+ Ongeza bidhaa",
    "Type": "Aina",
    "Price": "Bei",
    "Shop": "Duka",
    "Visible": "Inaonekana",
    "Hidden": "Imefichwa",
    "Click to hide": "Bofya kuficha",
    "Click to show": "Bofya kuonyesha",
    "Edit": "Hariri",
    "Delete": "Futa",
    "Delete {name}? This cannot be undone.": "Futa {name}? Hatua hii haiwezi kutenduliwa.",
    "No products yet. Add your first one.": "Bado hakuna bidhaa. Ongeza ya kwanza.",
    "Vehicle-specific (customer picks make & model)": "Ya gari maalum (mteja huchagua aina na modeli)",
    "Simple (no options)": "Rahisi (bila chaguo)",
    "Battery (voltage + type)": "Betri (volteji + aina)",
    "Coil springs (thickness + position)": "Springi (unene + upande)",
    "Motor oil (brand + viscosity)": "Oili ya injini (chapa + uzito)",
    "Add product": "Ongeza bidhaa",
    "Edit {name}": "Hariri {name}",
    "Name": "Jina",
    "Vehicle-specific parts ask the customer for make & model; premium makes add to the price.":
        "Vipuri vya gari maalum humwuliza mteja aina na modeli ya gari; magari ya hadhi ya juu huongeza bei.",
    "Base price (KSh)": "Bei ya msingi (KSh)",
    "Display order": "Mpangilio wa kuonyesha",
    "optional": "si lazima",
    "Description (optional)": "Maelezo (si lazima)",
    "Image": "Picha",
    "Image URL": "Kiungo cha picha",
    "…or leave the URL empty and pick a built-in image:": "…au acha kiungo kitupu na uchague picha iliyopo:",
    "Visible in the shop": "Ionekane dukani",
    "Save changes": "Hifadhi mabadiliko",
    "Cancel": "Ghairi",
    "Emails listed in ADMIN_EMAIL are always made admin again when they log in.":
        "Barua pepe zilizo kwenye ADMIN_EMAIL hufanywa msimamizi tena kila zinapoingia.",
    "Joined": "Alijiunga",
    "Role": "Wadhifa",
    "admin": "msimamizi",
    "shopper": "mnunuzi",
    "Make shopper": "Fanya mnunuzi",
    "Make admin": "Fanya msimamizi",
    "you": "wewe",
    "Name is required.": "Jina linahitajika.",
    "Choose a valid product type.": "Chagua aina sahihi ya bidhaa.",
    "Price must be a number between 1 and {max}.": "Bei lazima iwe nambari kati ya 1 na {max}.",
    "Stock must be a whole number between 0 and {max}.": "Hisa lazima iwe nambari kamili kati ya 0 na {max}.",
    "Display order must be a whole number.": "Mpangilio lazima uwe nambari kamili.",
    "Image URL must start with http:// or https://": "Kiungo cha picha lazima kianze na http:// au https://",
    "Paste an image URL or choose one of the built-in images.": "Bandika kiungo cha picha au uchague mojawapo ya picha zilizopo.",
    'Added "{name}".': 'Imeongezwa: "{name}".',
    'Saved "{name}".': 'Imehifadhiwa: "{name}".',
    "{name}: stock set to {stock}.": "{name}: hisa sasa ni {stock}.",
    "{name} is now visible in the shop.": "{name} sasa inaonekana dukani.",
    "{name} is now hidden from the shop.": "{name} sasa imefichwa dukani.",
    'Deleted "{name}". Past orders keep their item names.': 'Imefutwa: "{name}". Maagizo ya zamani yanabaki na majina ya bidhaa.',
    "You can't remove your own admin role.": "Huwezi kujiondolea wadhifa wa msimamizi.",
    "{email} is now an admin.": "{email} sasa ni msimamizi.",
    "{email} is now a shopper.": "{email} sasa ni mnunuzi.",
}

TRANSLATIONS = {'sw': SW}


def get_lang():
    if has_request_context():
        return g.get('lang', DEFAULT_LANG)
    return DEFAULT_LANG


def _(text, **values):
    """Translate text into the current language and fill in {placeholders}."""
    translated = TRANSLATIONS.get(get_lang(), {}).get(text, text)
    return translated.format(**values) if values else translated


def init_i18n(app):
    @app.before_request
    def pick_language():
        lang = request.cookies.get(COOKIE)
        g.lang = lang if lang in LANGUAGES else DEFAULT_LANG

    @app.context_processor
    def inject_i18n():
        return {'_': _, 'lang': get_lang(), 'js_translations': TRANSLATIONS.get(get_lang(), {})}

    @app.route('/lang/<code>')
    def set_language(code):
        target = request.args.get('next', '')
        # Only redirect back to a page on this site
        if not (target.startswith('/') and not target.startswith('//') and '\\' not in target):
            target = url_for('index')
        response = redirect(target)
        if code in LANGUAGES:
            response.set_cookie(COOKIE, code, max_age=365 * 24 * 3600, samesite='Lax',
                                secure=app.config.get('SESSION_COOKIE_SECURE', False))
        return response
