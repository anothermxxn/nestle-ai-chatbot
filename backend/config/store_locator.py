# OpenStreetMap OSRM Configuration
OSRM_API_CONFIG = {
    "base_url": "https://router.project-osrm.org",
    "timeout": 15,
    "default_radius_km": 10,
    "max_results": 3,
    "routing_profile": "driving",  # driving, walking, cycling
    "overview": "false",
    "steps": "false",
    "max_candidates": 15
}

# Alternative OSRM endpoints for different transport modes
OSRM_ENDPOINTS = {
    "driving": "https://router.project-osrm.org/route/v1/driving",
    "walking": "https://router.project-osrm.org/route/v1/foot", 
}

# OpenStreetMap Overpass API Configuration
OVERPASS_API_CONFIG = {
    "url": "https://overpass-api.de/api/interpreter",
    "timeout": 15
}

# Google Maps Integration
GOOGLE_MAPS_CONFIG = {
    "base_url": "https://www.google.com/maps/search/",
    "search_params": "api=1",
    "default_zoom": 15,
    "enable_place_id_search": False
} 

# Canadian Retail Chains
CANADIAN_RETAILERS = [
    # Major Grocery Chains
    "Walmart",
    "Loblaws", 
    "Metro",
    "Sobeys",
    "Real Canadian Superstore",
    "No Frills",
    "Zehrs",
    "Fortinos",
    "Your Independent Grocer",
    "Save-On-Foods",
    "FreshCo",
    "Food Basics",
    
    # Warehouse/Membership Stores
    "Costco",
    
    # Pharmacy Chains
    "Shoppers Drug Mart",
    
    # General Merchandise
    "Canadian Tire",
    "Giant Tiger",
    "Dollarama"
]

# Keywords to filter out non-store locations
EXCLUDE_KEYWORDS = [
    "parking", "office", "dental", "eye care", "centre", "center", 
    "concourse", "hall", "building", "tower", "station", "atm",
    "pharmacy", "clinic", "medical", "hospital", "court", "legal",
    "warehouse", "distribution", "corporate", "headquarters", "admin",
    "mall", "plaza", "complex", "garage", "lot", "storage"
]

# Valid OpenStreetMap shop types for retail stores
VALID_SHOP_TYPES = [
    "supermarket", "convenience", "department_store", "general",
    "grocery", "retail", "mall", "yes"
]

# Valid OpenStreetMap amenity types for retail stores  
VALID_AMENITY_TYPES = [
    "marketplace", "shopping_centre"
]