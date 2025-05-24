import os

def get_project_root():
    """Get the project root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(current_dir, "..", ".."))

PROJECT_ROOT = get_project_root()
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

DEFAULT_BASE_URL = "https://www.madewithnestle.ca"
DEFAULT_LINKS_FILE = os.path.join(DATA_DIR, "collected_links.json")
DEFAULT_VECTOR_CHUNKS_FILE = os.path.join(PROCESSED_DATA_DIR, "vector_chunks.json")
DEFAULT_CONTENT_INDEX_FILE = os.path.join(PROCESSED_DATA_DIR, "content_index.json")

FOOD_COMPOUND_TERMS = [
    # Ice cream and frozen desserts
    "ice cream", "ice creams", "soft serve", "hard pack", "gelato", "sorbet",
    "frozen yogurt", "frozen dessert", "frozen desserts", "ice cream cake",
    "ice cream sandwich", "ice cream cone", "ice cream bar", "ice cream sundae",
    "vanilla ice cream", "chocolate ice cream", "strawberry ice cream",
    
    # Chocolate varieties  
    "milk chocolate", "dark chocolate", "white chocolate", "chocolate chip",
    "chocolate chips", "chocolate bar", "chocolate bars", "chocolate cake",
    "chocolate mousse", "chocolate sauce", "chocolate syrup", "hot chocolate",
    "chocolate brownie", "chocolate cookie", "chocolate cookies",
    
    # Coffee products
    "instant coffee", "ground coffee", "coffee beans", "coffee machine",
    "coffee maker", "coffee shop", "iced coffee", "cold brew", "espresso",
    "cappuccino", "latte", "macchiato", "coffee crisp", "coffee mate",
    
    # Cream and dairy
    "whipped cream", "heavy cream", "light cream", "sour cream", "cream cheese",
    "real dairy", "dairy free", "non dairy",
    
    # Baking ingredients
    "baking powder", "baking soda", "vanilla extract", "almond extract",
    "brown sugar", "powdered sugar", "maple syrup", "corn syrup", 
    "coconut oil", "olive oil", "vegetable oil",
    
    # Recipe terms
    "prep time", "cook time", "total time", "serving size", "recipe card",
    "step by step", "easy recipe", "quick recipe", "healthy recipe",
    
    # Nutrition terms
    "calorie count", "nutrition facts", "dietary fiber", "saturated fat",
    "trans fat", "vitamin c", "vitamin d", "vitamin b", "omega 3",
    
    # Meal types
    "breakfast cereal", "lunch box", "dinner party", "snack time",
    "meal planning", "meal prep", "family dinner", "quick meal",
    
    # Cooking methods
    "slow cooker", "pressure cooker", "air fryer", "food processor",
    "stand mixer", "hand mixer", "baking sheet", "mixing bowl",
    
    # Product categories
    "frozen meals", "ready meals", "baby food", "pet food", "health food",
    "organic food", "gluten free", "sugar free", "fat free", "low fat"
]

BRAND_COMPOUND_TERMS = [
    "kit kat", "quality street", "after eight", "coffee crisp", "big turk",
    "lean cuisine", "haagen dazs", "del monte", "real dairy", "coffee mate",
    "natures bounty", "san pellegrino"
]

ALL_COMPOUND_TERMS = FOOD_COMPOUND_TERMS + BRAND_COMPOUND_TERMS

FOOD_DOMAINS = [
    # Ingredients
    "chocolate", "vanilla", "strawberry", "caramel", "coconut", "almond", "peanut",
    "butter", "cream", "milk", "sugar", "honey", "maple", "cinnamon", "mint",
    
    # Food types
    "cookie", "cake", "pie", "bread", "pasta", "sauce", "soup", "salad",
    "sandwich", "pizza", "burger", "cereal", "yogurt", "cheese", "fruit",
    
    # Cooking terms
    "recipe", "baking", "cooking", "grilling", "frying", "boiling", "mixing",
    "seasoning", "marinating", "sautéing", "roasting", "preparation",
    
    # Descriptors
    "crispy", "creamy", "sweet", "salty", "spicy", "fresh", "frozen", "organic",
    "delicious", "tasty", "flavorful", "rich", "smooth", "crunchy",
    
    # Nutrition
    "calories", "protein", "fiber", "vitamins", "minerals", "healthy", "nutrition",
    "ingredients", "serving", "portion"
]

EXCLUDE_SECTION_PATTERNS = [
    r"information we collect about you",
    r"performance cookies",
    r"cookie policy",
    r"privacy policy",
    r"terms of service",
    r"terms and conditions",
    r"cookie settings",
    r"manage cookies",
    r"privacy notice",
    r"data protection",
    r"gdpr",
    r"legal notice",
    r"copyright notice",
    r"all rights reserved",
    r"newsletter signup",
    r"follow us",
    r"social media",
    r"share this",
    r"share on facebook",
    r"share on twitter", 
    r"share on pinterest",
    r"facebook.*twitter.*pinterest",
    r"skip to main content",
    r"contact us",
    r"customer service",
    r"site map",
    r"help center",
    r"accessibility",
    r"modern slavery statement"
]

MIN_CONTENT_LENGTH = 50

FOOD_INDICATORS = [
    "chocolate", "cream", "ice", "coffee", "recipe", "baking", "cooking",
    "dessert", "cake", "cookie", "sweet", "flavor", "ingredient", "sauce",
    "syrup", "butter", "sugar", "vanilla", "caramel", "strawberry", "berry",
    "fruit", "nut", "almond", "coconut", "lemon", "orange", "mint", "crispy",
    "smooth", "rich", "delicious", "frozen", "fresh", "organic", "natural"
]

GENERIC_TERMS = ["new", "great", "good", "best", "more", "other", "all", "some"]

STOP_WORDS = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "a", "an"}

WEB_COOKIE_INDICATORS = [
    "tracking", "analytics", "advertising", "gdpr", "consent", 
    "privacy policy", "data protection", "personal information",
    "third party", "performance cookies", "functional cookies",
    "targeting cookies", "essential cookies", "browser",
    "website", "collect information", "your preferences",
    "opt out", "manage cookies", "cookie settings"
]

FOOD_COOKIE_INDICATORS = [
    "recipe", "ingredients", "chocolate", "baking", "oven",
    "flour", "sugar", "butter", "vanilla", "cream",
    "crispy", "chewy", "sweet", "dessert", "treat"
]

SOCIAL_MEDIA_INDICATORS = [
    "facebook", "twitter", "pinterest", "email", "yummly", "instagram", "linkedin"
]

ERROR_INDICATORS = [
    "404 error",
    "page not found",
    "page doesn't exist",
    "page has been removed",
    "red mugger strikes",
    "stole the page you were looking for"
]

ERROR_CODES = ["400", "401", "403", "404", "500", "502", "503"]

NAV_PATTERNS = [
    r"^(home|about|contact|products|services|blog)$",
    r"^\s*>\s*",  # Breadcrumb navigation
    r"^[<>←→\s]+$"  # Navigation arrows/symbols
]

# Processing settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
MARKDOWN_CHUNK_SIZE = 800
MARKDOWN_CHUNK_OVERLAP = 80
MAX_KEYWORDS_PER_CHUNK = 10
BATCH_SIZE = 100

# Scraping settings
MAX_PAGES_DEFAULT = 1000
MAX_PAGES_LARGE = 10000
SCRAPER_CONCURRENCY = 5

# N-gram extraction settings
NGRAM_RANGE = (2, 3)
MAX_NGRAMS = 10
MAX_PHRASE_LENGTH = 4 