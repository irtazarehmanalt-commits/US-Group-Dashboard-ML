"""Denim fit-classification taxonomy, transcribed from the internal
"Women Jeans" / "Men Jeans" reference spreadsheet. Used to tag every scraped
jeans product with a Fit Category / Fit Sub-Category by matching its name
against the known alternate naming conventions retailers use for that fit.

Women's and men's jeans use overlapping fit-category names (e.g. "Straight",
"Skinny") but different sub-category breakdowns, so classify_fit() takes a
section ("women"/"men") and looks the name up against the matching table -
picking whichever category a page's URL targets (see BRAND_TARGETS in
batch_scrape.py) tells us which table to use.
"""

WOMEN_JEANS_TAXONOMY = [
    {"fit_category": "Baggy", "fit_sub_category": "Super Baggy",
     "possible_names": ["Super Baggy", "Oversized Jeans", "90s Baggy", "Puddle Jeans", "Baggy Wide"]},
    {"fit_category": "Baggy", "fit_sub_category": "Baggy",
     "possible_names": ["Skater Fit", "Loose Baggy", "Baggy"]},
    {"fit_category": "Baggy", "fit_sub_category": "Semi Baggy",
     "possible_names": ["Smart Baggy", "Baggy Straight", "Semi Baggy"]},
    {"fit_category": "Loose", "fit_sub_category": "Standard Loose",
     "possible_names": ["Loose Fit", "Easy Fit", "Roomy Jean"]},
    {"fit_category": "Loose", "fit_sub_category": "Loose Straight",
     "possible_names": ["Relaxed Loose", "Wide Straight Fit"]},
    {"fit_category": "Relaxed", "fit_sub_category": "Standard Relaxed",
     "possible_names": ["Relaxed Fit", "Classic Relaxed", "Comfort Fit"]},
    {"fit_category": "Relaxed", "fit_sub_category": "Athletic Relaxed",
     "possible_names": ["Athletic Fit", "Muscle Fit", "Roomy Thigh Relaxed"]},
    {"fit_category": "Straight", "fit_sub_category": "Regular Straight",
     "possible_names": ["Classic Straight", "Original Fit", "Standard Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "Slim Straight",
     "possible_names": ["Modern Straight", "Narrow Straight", "Straight Slim"]},
    {"fit_category": "Straight", "fit_sub_category": "Other Straights",
     "possible_names": ["Workwear Straight", "Selvedge Straight", "Vintage Straight"]},
    {"fit_category": "Flare", "fit_sub_category": "Women's Flare",
     "possible_names": ["Retro Flare", "70s Flare", "Wide Bell Bottom"]},
    {"fit_category": "Bootcut", "fit_sub_category": "Classic Bootcut",
     "possible_names": ["Cowboy Cut", "Standard Bootcut", "Western Fit", "Boot Flare"]},
    {"fit_category": "Bootcut", "fit_sub_category": "Slim Bootcut",
     "possible_names": ["Slim Fit Bootcut", "Modern Bootcut"]},
    {"fit_category": "Slim", "fit_sub_category": "Standard Slim",
     "possible_names": ["Slim Fit", "Tailored Slim", "Slim Leg"]},
    {"fit_category": "Slim", "fit_sub_category": "Slim Stretch",
     "possible_names": ["Performance Slim", "Motion Slim", "Flex Slim"]},
    {"fit_category": "Tapered", "fit_sub_category": "Regular Taper",
     "possible_names": ["Standard Taper", "Tapered Fit", "Regular Tapered", "Comfort Fit"]},
    {"fit_category": "Tapered", "fit_sub_category": "Slim Taper",
     "possible_names": ["Slim Tapered", "Narrow Taper"]},
    {"fit_category": "Tapered", "fit_sub_category": "Loose Taper",
     "possible_names": ["Baggy Tapered", "Relaxed Tapered", "Tapered Wide"]},
    {"fit_category": "Barrel", "fit_sub_category": "Barrel Fit",
     "possible_names": ["Barrel Leg", "Curve Leg", "Horseshoe Fit"]},
    {"fit_category": "Barrel", "fit_sub_category": "Balloon Fit",
     "possible_names": ["Balloon Leg", "Tapered Barrel"]},
    {"fit_category": "Skinny", "fit_sub_category": "Standard Skinny",
     "possible_names": ["Skinny Fit", "Slim Skinny"]},
    {"fit_category": "Skinny", "fit_sub_category": "Super Skinny",
     "possible_names": ["Extreme Skinny", "Stacked Skinny"]},
    {"fit_category": "Utility", "fit_sub_category": "Carpenter",
     "possible_names": ["Carpenter Straight", "Hammer Loop Jean", "Painter Jean"]},
    {"fit_category": "Utility", "fit_sub_category": "Cargo",
     "possible_names": ["Cargo Pocket Jean", "Combat Denim", "Tactical Utility"]},
    {"fit_category": "Utility", "fit_sub_category": "Double Knee",
     "possible_names": ["Reinforced Utility", "Double Front Jean"]},
]

MEN_JEANS_TAXONOMY = [
    {"fit_category": "Wide Leg", "fit_sub_category": "HR Wide",
     "possible_names": ["High Rise Wide Leg", "High Waist Wide Leg"]},
    {"fit_category": "Wide Leg", "fit_sub_category": "MR Wide",
     "possible_names": ["Mid Waist Wide Leg", "Mid Rise Wide Leg"]},
    {"fit_category": "Wide Leg", "fit_sub_category": "LR Wide",
     "possible_names": ["Low Rise Wide Leg", "Low Waist Wide Leg"]},
    {"fit_category": "Wide Leg", "fit_sub_category": "Comfort Wide",
     "possible_names": ["Stretch Wide Leg", "Comfort Wide Leg"]},
    {"fit_category": "Wide Leg", "fit_sub_category": "Other Wides",
     "possible_names": ["Baggy Wide Leg", "Wide Leg Paperbag", "Belted Wide leg",
                         "Pleated Wide", "Turn Up Wide Leg", "Jogger Wide"]},
    {"fit_category": "Straight", "fit_sub_category": "HR Straight",
     "possible_names": ["High Rise Straight", "High Waist Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "MR Straight",
     "possible_names": ["Mid Waist Straight", "Mid Rise Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "LR Straight",
     "possible_names": ["Low Rise Straight", "Low Waist Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "Comfort Straight",
     "possible_names": ["Comfort Straight", "Relaxed Straight", "Stretch Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "Stove Pipe",
     "possible_names": ["Stove Pipe Straight"]},
    {"fit_category": "Straight", "fit_sub_category": "Other Straights",
     "possible_names": ["Raw Hem Straight", "Turn Up Straight", "Fold Up Straight",
                         "Pleated Straight"]},
    {"fit_category": "Flare", "fit_sub_category": "HR Flare",
     "possible_names": ["High Waist Flare", "High Rise Flare"]},
    {"fit_category": "Flare", "fit_sub_category": "MR Flare",
     "possible_names": ["Mid Rise Flare", "Mid Waist Flare"]},
    {"fit_category": "Flare", "fit_sub_category": "LR Flare",
     "possible_names": ["Low Rise Flare", "Low Waist Flare"]},
    {"fit_category": "Flare", "fit_sub_category": "Other Flares",
     "possible_names": ["Cropped Flare", "Kick Flare", "Split Hem Flare"]},
    {"fit_category": "Skinny", "fit_sub_category": "HR Skinny",
     "possible_names": ["High Rise Skinny", "High Waist Skinny"]},
    {"fit_category": "Skinny", "fit_sub_category": "MR Skinny",
     "possible_names": ["Mid Rise Skinny", "Mid Waist Skinny"]},
    {"fit_category": "Skinny", "fit_sub_category": "LR Skinny",
     "possible_names": ["Low Rise Skinny", "Low Waist Skinny"]},
    {"fit_category": "Skinny", "fit_sub_category": "Super Skinny",
     "possible_names": ["Super Skinny Leg", "Spray-on Skinny", "Extreme Skinny"]},
    {"fit_category": "Skinny", "fit_sub_category": "Other Skinnies",
     "possible_names": ["Jeggings", "Ankle Skinny", "Raw Hem Skinny", "Sculpt Skinny"]},
    {"fit_category": "Slim", "fit_sub_category": "HR Slim",
     "possible_names": ["High Rise Slim", "High Waist Slim"]},
    {"fit_category": "Slim", "fit_sub_category": "MR Slim",
     "possible_names": ["Mid Rise Slim", "Mid Waist Slim"]},
    {"fit_category": "Slim", "fit_sub_category": "LR Slim",
     "possible_names": ["Low Rise Slim", "Low Waist Slim"]},
    {"fit_category": "Slim", "fit_sub_category": "Other Slims",
     "possible_names": ["Cigarette Jean", "Slim Fit Jean", "Slim Straight"]},
    {"fit_category": "Bootcut", "fit_sub_category": "HR Bootcut",
     "possible_names": ["High Rise Bootcut", "High Waist Bootcut"]},
    {"fit_category": "Bootcut", "fit_sub_category": "MR Bootcut",
     "possible_names": ["Mid Rise Bootcut", "Mid Waist Bootcut"]},
    {"fit_category": "Bootcut", "fit_sub_category": "LR Bootcut",
     "possible_names": ["Low Rise Bootcut", "Low Waist Bootcut"]},
    {"fit_category": "Bootcut", "fit_sub_category": "Other Bootcuts",
     "possible_names": ["Slim Bootcut", "Baby Bootcut", "Split Hem Bootcut", "Cropped Bootcut"]},
    {"fit_category": "Mom Fit", "fit_sub_category": "Classic Mom",
     "possible_names": ["High Rise Mom Jean", "Classic Mom Fit", "Heritage Mom"]},
    {"fit_category": "Mom Fit", "fit_sub_category": "Slim Mom",
     "possible_names": ["Slim Mom Jean", "Narrow Mom Fit"]},
    {"fit_category": "Mom Fit", "fit_sub_category": "Comfort Mom",
     "possible_names": ["Stretch Mom Jean", "Relaxed Mom Fit"]},
    {"fit_category": "Barrel Fit", "fit_sub_category": "Barrel Leg",
     "possible_names": ["Barrel Leg Jean", "Horseshoe Jean", "Curve Leg"]},
    {"fit_category": "Barrel Fit", "fit_sub_category": "Balloon Leg",
     "possible_names": ["Balloon Jean", "Tapered Barrel Fit"]},
    {"fit_category": "Baggy Fit", "fit_sub_category": "Loose Baggy",
     "possible_names": ["Baggy Jean", "Oversized Jean", "Loose Fit"]},
    {"fit_category": "Baggy Fit", "fit_sub_category": "Puddle",
     "possible_names": ["Puddle Jean", "Extra Long Baggy"]},
    {"fit_category": "Baggy Fit", "fit_sub_category": "Other Baggy",
     "possible_names": ["90s Baggy", "Low Rise Baggy"]},
    {"fit_category": "Utility", "fit_sub_category": "Cargo",
     "possible_names": ["Cargo Wide Leg", "Multi-pocket Jean", "Combat Jean"]},
    {"fit_category": "Utility", "fit_sub_category": "Carpenter",
     "possible_names": ["Carpenter Straight", "Hammer Loop Jean", "Utility Jean"]},
    {"fit_category": "Relaxed", "fit_sub_category": "Dad Fit",
     "possible_names": ["90s Dad Jean", "Loose Dad Fit"]},
    {"fit_category": "Relaxed", "fit_sub_category": "Boyfriend",
     "possible_names": ["Relaxed Boyfriend", "Slim Boyfriend", "Ex-Boyfriend Jean"]},
]


def classify_fit(product_name: str, section: str) -> tuple[str | None, str | None]:
    """Match a scraped product's name against the fit taxonomy for its
    section ("women" or "men"). Returns (fit_category, fit_sub_category), or
    (None, None) if nothing matched. When multiple phrases match, the longest
    (most specific) one wins - e.g. "Super Skinny" beats a bare "Skinny" match
    on the same name."""
    if not product_name:
        return None, None
    taxonomy = WOMEN_JEANS_TAXONOMY if section == "women" else MEN_JEANS_TAXONOMY
    name_lower = product_name.lower()

    best_row, best_len = None, 0
    for row in taxonomy:
        for phrase in row["possible_names"]:
            if phrase.lower() in name_lower and len(phrase) > best_len:
                best_row, best_len = row, len(phrase)

    if best_row is None:
        return None, None
    return best_row["fit_category"], best_row["fit_sub_category"]
