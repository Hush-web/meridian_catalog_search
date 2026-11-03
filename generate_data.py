import json
import random

# 1. THE BLUEPRINTS (Our base products)
# We add "ndc" (a fake barcode) and "label_uses" to make it realistic.
base_products = [
    # PAIN RELIEF
    {"brand": "Advil", "generic": "Ibuprofen", "ingredient": "Ibuprofen 200mg", "form": "Tablet", "category": "Pain Relief", "restricted": False, "label_uses": "Headaches, muscle aches, arthritis"},
    {"brand": "Advil", "generic": "Ibuprofen", "ingredient": "Ibuprofen 200mg", "form": "Liquid Gel", "category": "Pain Relief", "restricted": False, "label_uses": "Fast relief for headaches and body aches"},
    {"brand": "Advil PM", "generic": "Ibuprofen/Diphenhydramine", "ingredient": "Ibuprofen 200mg, Diphenhydramine 38mg", "form": "Capsule", "category": "Pain Relief", "restricted": False, "label_uses": "Nighttime pain relief with sleep aid"},
    {"brand": "Tylenol", "generic": "Acetaminophen", "ingredient": "Acetaminophen 500mg", "form": "Tablet", "category": "Pain Relief", "restricted": False, "label_uses": "Fever reduction and minor aches"},
    {"brand": "Tylenol Extra Strength", "generic": "Acetaminophen", "ingredient": "Acetaminophen 500mg", "form": "Caplet", "category": "Pain Relief", "restricted": False, "label_uses": "Extra strength pain relief"},
    {"brand": "Tylenol PM", "generic": "Acetaminophen/Diphenhydramine", "ingredient": "Acetaminophen 500mg, Diphenhydramine 25mg", "form": "Caplet", "category": "Pain Relief", "restricted": False, "label_uses": "Nighttime pain and sleep aid"},
    {"brand": "Aleve", "generic": "Naproxen Sodium", "ingredient": "Naproxen Sodium 220mg", "form": "Tablet", "category": "Pain Relief", "restricted": False, "label_uses": "All day strong pain relief"},
    {"brand": "Motrin IB", "generic": "Ibuprofen", "ingredient": "Ibuprofen 200mg", "form": "Tablet", "category": "Pain Relief", "restricted": False, "label_uses": "Temporary relief of minor aches and pains"},
    {"brand": "Excedrin", "generic": "Acetaminophen/Aspirin/Caffeine", "ingredient": "Acetaminophen 250mg, Aspirin 250mg, Caffeine 65mg", "form": "Gelcap", "category": "Pain Relief", "restricted": False, "label_uses": "Migraine and headache relief"},
    {"brand": "Bayer", "generic": "Aspirin", "ingredient": "Aspirin 325mg", "form": "Tablet", "category": "Pain Relief", "restricted": False, "label_uses": "Pain relief and fever reducer"},
    
    # ALLERGY & SINUS
    {"brand": "Zyrtec", "generic": "Cetirizine", "ingredient": "Cetirizine HCl 10mg", "form": "Tablet", "category": "Allergy", "restricted": False, "label_uses": "24-hour allergy relief"},
    {"brand": "Zyrtec", "generic": "Cetirizine", "ingredient": "Cetirizine HCl 10mg", "form": "Liquid Gel", "category": "Allergy", "restricted": False, "label_uses": "Indoor and outdoor allergy relief"},
    {"brand": "Claritin", "generic": "Loratadine", "ingredient": "Loratadine 10mg", "form": "Tablet", "category": "Allergy", "restricted": False, "label_uses": "Non-drowsy allergy relief"},
    {"brand": "Claritin RediTabs", "generic": "Loratadine", "ingredient": "Loratadine 10mg", "form": "Chewable", "category": "Allergy", "restricted": False, "label_uses": "Melt-in-mouth allergy relief"},
    {"brand": "Allegra", "generic": "Fexofenadine", "ingredient": "Fexofenadine HCl 180mg", "form": "Tablet", "category": "Allergy", "restricted": False, "label_uses": "24-hour non-drowsy allergy relief"},
    {"brand": "Benadryl", "generic": "Diphenhydramine", "ingredient": "Diphenhydramine HCl 25mg", "form": "Capsule", "category": "Allergy", "restricted": False, "label_uses": "Relief for sneezing, runny nose, itchy eyes"},
    {"brand": "Flonase", "generic": "Fluticasone", "ingredient": "Fluticasone Propionate 50mcg", "form": "Spray", "category": "Allergy", "restricted": False, "label_uses": "Nasal allergy symptom relief"},
    {"brand": "Nasacort", "generic": "Triamcinolone", "ingredient": "Triamcinolone Acetonide 55mcg", "form": "Spray", "category": "Allergy", "restricted": False, "label_uses": "Allergy and sinus congestion relief"},
    {"brand": "Sudafed", "generic": "Pseudoephedrine", "ingredient": "Pseudoephedrine HCl 30mg", "form": "Tablet", "category": "Cold & Flu", "restricted": True, "label_uses": "Nasal and sinus congestion relief"},
    {"brand": "Sudafed PE", "generic": "Phenylephrine", "ingredient": "Phenylephrine HCl 10mg", "form": "Tablet", "category": "Cold & Flu", "restricted": False, "label_uses": "Nasal decongestant relief"},

    # COLD & FLU
    {"brand": "Mucinex", "generic": "Guaifenesin", "ingredient": "Guaifenesin 600mg", "form": "Tablet", "category": "Cold & Flu", "restricted": False, "label_uses": "Thins and loosens mucus"},
    {"brand": "Mucinex DM", "generic": "Guaifenesin/Dextromethorphan", "ingredient": "Guaifenesin 600mg, Dextromethorphan 30mg", "form": "Tablet", "category": "Cold & Flu", "restricted": False, "label_uses": "Controls cough and thins mucus"},
    {"brand": "NyQuil", "generic": "Acetaminophen/Dextromethorphan/Doxylamine", "ingredient": "Acetaminophen 650mg, Dextromethorphan 30mg, Doxylamine 12.5mg", "form": "Liquid", "category": "Cold & Flu", "restricted": False, "label_uses": "Nighttime cold and flu symptom relief"},
    {"brand": "DayQuil", "generic": "Acetaminophen/Dextromethorphan/Phenylephrine", "ingredient": "Acetaminophen 325mg, Dextromethorphan 10mg, Phenylephrine 5mg", "form": "Liquid", "category": "Cold & Flu", "restricted": False, "label_uses": "Non-drowsy daytime cold and flu relief"},
    {"brand": "Theraflu", "generic": "Acetaminophen/Diphenhydramine/Phenylephrine", "ingredient": "Acetaminophen 650mg, Diphenhydramine 25mg, Phenylephrine 10mg", "form": "Powder", "category": "Cold & Flu", "restricted": False, "label_uses": "Hot liquid cold relief"},
    {"brand": "Robitussin", "generic": "Dextromethorphan/Guaifenesin", "ingredient": "Dextromethorphan 20mg, Guaifenesin 200mg", "form": "Liquid", "category": "Cold & Flu", "restricted": False, "label_uses": "Cough and chest congestion relief"},
    {"brand": "Halls", "generic": "Menthol", "ingredient": "Menthol 7mg", "form": "Lozenge", "category": "Cold & Flu", "restricted": False, "label_uses": "Soothes sore throat"},
    {"brand": "Ricola", "generic": "Herbal", "ingredient": "Natural Herbs", "form": "Chewable", "category": "Cold & Flu", "restricted": False, "label_uses": "Soothes sore throats naturally"},
    {"brand": "Vicks VapoRub", "generic": "Camphor/Eucalyptus", "ingredient": "Camphor 4.8%, Eucalyptus Oil 1.2%", "form": "Ointment", "category": "Cold & Flu", "restricted": False, "label_uses": "Topical cough suppressant"},

    # DIGESTIVE HEALTH
    {"brand": "Pepto-Bismol", "generic": "Bismuth Subsalicylate", "ingredient": "Bismuth Subsalicylate 262mg", "form": "Liquid", "category": "Digestive Health", "restricted": False, "label_uses": "Upset stomach, nausea, diarrhea"},
    {"brand": "Pepto-Bismol", "generic": "Bismuth Subsalicylate", "ingredient": "Bismuth Subsalicylate 262mg", "form": "Chewable", "category": "Digestive Health", "restricted": False, "label_uses": "Relief for nausea and upset stomach"},
    {"brand": "Tums", "generic": "Calcium Carbonate", "ingredient": "Calcium Carbonate 500mg", "form": "Chewable", "category": "Digestive Health", "restricted": False, "label_uses": "Fast heartburn relief"},
    {"brand": "Prilosec OTC", "generic": "Omeprazole", "ingredient": "Omeprazole 20mg", "form": "Tablet", "category": "Digestive Health", "restricted": False, "label_uses": "Frequent heartburn relief"},
    {"brand": "Imodium", "generic": "Loperamide", "ingredient": "Loperamide HCl 2mg", "form": "Capsule", "category": "Digestive Health", "restricted": False, "label_uses": "Controls diarrhea symptoms"},
    {"brand": "Zantac 360", "generic": "Famotidine", "ingredient": "Famotidine 20mg", "form": "Tablet", "category": "Digestive Health", "restricted": False, "label_uses": "Prevents and relieves heartburn"},
    {"brand": "Gas-X", "generic": "Simethicone", "ingredient": "Simethicone 125mg", "form": "Softgel", "category": "Digestive Health", "restricted": False, "label_uses": "Relief for gas and bloating"},
    {"brand": "Dramamine", "generic": "Dimenhydrinate", "ingredient": "Dimenhydrinate 50mg", "form": "Tablet", "category": "Digestive Health", "restricted": False, "label_uses": "Prevents motion sickness"},
    {"brand": "Miralax", "generic": "Polyethylene Glycol", "ingredient": "Polyethylene Glycol 3350", "form": "Powder", "category": "Digestive Health", "restricted": False, "label_uses": "Relieves occasional constipation"},

    # FIRST AID & TOPICAL
    {"brand": "Neosporin", "generic": "Neomycin/Polymyxin B/Bacitracin", "ingredient": "Neomycin 3.5mg, Polymyxin B 10,000 units, Bacitracin 400 units", "form": "Ointment", "category": "First Aid", "restricted": False, "label_uses": "Prevents infection in minor cuts"},
    {"brand": "Polysporin", "generic": "Polymyxin B/Bacitracin", "ingredient": "Polymyxin B 10,000 units, Bacitracin 500 units", "form": "Ointment", "category": "First Aid", "restricted": False, "label_uses": "First aid antibiotic ointment"},
    {"brand": "Hydrocortisone 1%", "generic": "Hydrocortisone", "ingredient": "Hydrocortisone 1%", "form": "Cream", "category": "First Aid", "restricted": False, "label_uses": "Temporary relief of itching"},
    {"brand": "Cortizone-10", "generic": "Hydrocortisone", "ingredient": "Hydrocortisone 1%", "form": "Cream", "category": "First Aid", "restricted": False, "label_uses": "Relief for eczema and poison ivy"},
    {"brand": "Bacitracin", "generic": "Bacitracin", "ingredient": "Bacitracin 500 units", "form": "Ointment", "category": "First Aid", "restricted": False, "label_uses": "Prevents infection in minor cuts"},
    {"brand": "Band-Aid", "generic": "Adhesive Bandage", "ingredient": "N/A", "form": "Patch", "category": "First Aid", "restricted": False, "label_uses": "Protects minor cuts and scrapes"},
    {"brand": "Alcohol Prep Pads", "generic": "Isopropyl Alcohol", "ingredient": "Isopropyl Alcohol 70%", "form": "Wipe", "category": "First Aid", "restricted": False, "label_uses": "Cleans skin before injections"},
    {"brand": "Hibiclens", "generic": "Chlorhexidine", "ingredient": "Chlorhexidine Gluconate 4%", "form": "Liquid", "category": "First Aid", "restricted": False, "label_uses": "Surgical hand scrub and skin cleanser"},
    {"brand": "Solarcaine", "generic": "Lidocaine", "ingredient": "Lidocaine 0.5%", "form": "Spray", "category": "First Aid", "restricted": False, "label_uses": "Relieves sunburn and minor burns"},
    {"brand": "Preparation H", "generic": "Phenylephrine", "ingredient": "Phenylephrine HCl 0.25%", "form": "Cream", "category": "First Aid", "restricted": False, "label_uses": "Relieves hemorrhoid discomfort"},
    {"brand": "Monistat 1", "generic": "Tioconazole", "ingredient": "Tioconazole 6.5%", "form": "Ointment", "category": "First Aid", "restricted": False, "label_uses": "Treats vaginal yeast infections"},
    {"brand": "Lamisil AT", "generic": "Terbinafine", "ingredient": "Terbinafine HCl 1%", "form": "Cream", "category": "First Aid", "restricted": False, "label_uses": "Cures athlete's foot"}
]

# 2. THE STORES (Our pharmacies)
pharmacies = [
    {"pharmacy_id": "pharm_1", "name": "CVS Austin", "inventory": []},
    {"pharmacy_id": "pharm_2", "name": "Walgreens Dallas", "inventory": []},
    {"pharmacy_id": "pharm_3", "name": "Local Pharmacy Houston", "inventory": []}
]

def generate_catalog():
    catalog = []
    for i in range(1, 301):
        base = base_products[i % len(base_products)]
        
        # Add a random size/strength to make the 6 copies slightly different
        sizes = ["Small", "Medium", "Large", "Value Pack"]
        random_size = random.choice(sizes)
        
        product = {
            "product_id": f"prod_{i:03d}",
            "brand": base["brand"],
            "generic_name": base["generic"],
            "active_ingredients": base["ingredient"],
            "form": base["form"],
            "category": base["category"],
            "restricted": base["restricted"],
            "label_uses": base["label_uses"],
            "pack_size": random_size, # <--- New field!
            "ndc": f"12345-{random.randint(100, 999)}-{random.randint(10, 99)}"
        }
        catalog.append(product)
    return catalog

def generate_inventory(catalog):
    """Store manager: decides what each pharmacy stocks and at what price."""
    for pharmacy in pharmacies:
        for product in catalog:
            # Roll a dice. If the number is less than 0.6 (60% chance), they stock it.
            if random.random() < 0.6:
                inventory_item = {
                    "product_id": product["product_id"],
                    "price": round(random.uniform(4.99, 29.99), 2), # Random price between $4.99 and $29.99
                    "stock": random.randint(5, 100) # Random stock between 5 and 100
                }
                pharmacy["inventory"].append(inventory_item)
    return pharmacies

# --- RUN THE FACTORY ---
if __name__ == "__main__":
    print("Generating catalog...")
    master_catalog = generate_catalog()
    
    print("Generating pharmacy inventories...")
    pharmacy_data = generate_inventory(master_catalog)
    
    # Save the catalog to a file
    with open("catalog.json", "w") as f:
        json.dump(master_catalog, f, indent=4)
        
    # Save the pharmacies to a file
    with open("pharmacies.json", "w") as f:
        json.dump(pharmacy_data, f, indent=4)
        
    print("Done! Created catalog.json (300 products) and pharmacies.json (3 stores).")