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
    r"^cookie policy$",
    r"^privacy policy$", 
    r"^terms of service$",
    r"^terms and conditions$",
    r"^gdpr compliance$",
    r"^data protection policy$",
    r"^copyright notice$",
    r"^manage consent preferences$",
    r"^cookie consent tool$",
    r"^information we collect",
    r"^strictly necessary cookies$",
    r"^performance cookies$",
    r"^social media cookies$",
    r"^targeting cookies$",
    r"^functional cookies$"
]

MIN_CONTENT_LENGTH = 15

FOOD_INDICATORS = [
    "chocolate", "cream", "ice", "coffee", "recipe", "baking", "cooking",
    "dessert", "cake", "cookie", "sweet", "flavor", "ingredient", "sauce",
    "syrup", "butter", "sugar", "vanilla", "caramel", "strawberry", "berry",
    "fruit", "nut", "almond", "coconut", "lemon", "orange", "mint", "crispy",
    "smooth", "rich", "delicious", "frozen", "fresh", "organic", "natural"
]

GENERIC_TERMS = ["new", "great", "good", "best", "more", "other", "all", "some"]

STOP_WORDS = {
    # Web/technical terms that LLMs might miss
    "www", "http", "https", "html", "com", "org", "net", "ca", "uk", "php", "asp", "jsp",
    "url", "href", "src", "alt", "css", "js", "javascript", "cdn", "api", "json", "xml",
    
    # Tracking and analytics terms (often in web content)
    "cookies", "cookie", "tracking", "analytics", "gdpr", "consent", "privacy",
    "gtm", "ga", "utm", "pixel", "beacon", "tag", "manager", "dataLayer",
    
    # Web UI/UX terms that might appear in scraped content
    "onclick", "onload", "href", "target", "blank", "nofollow", "noopener",
    "viewport", "responsive", "breakpoint", "modal", "tooltip", "dropdown",
    
    # Social media platform-specific terms
    "facebook", "twitter", "pinterest", "instagram", "linkedin", "youtube",
    "tiktok", "snapchat", "whatsapp", "telegram", "discord", "reddit",
    
    # E-commerce and web platform terms
    "shopify", "woocommerce", "magento", "wordpress", "drupal", "joomla",
    "prestashop", "bigcommerce", "squarespace", "wix", "webflow",
    
    # Web performance and technical terms
    "cdn", "ssl", "tls", "cors", "csrf", "xss", "sql", "nosql", "mongodb",
    "redis", "elasticsearch", "nginx", "apache", "cloudflare", "aws",
    
    # Cookie and consent management specific terms
    "onetrust", "cookiebot", "trustarc", "quantcast", "iubenda", "cookiepro",
    "necessary", "functional", "targeting", "performance", "essential",
    
    # Web scraping artifacts that might slip through
    "noscript", "iframe", "embed", "object", "param", "canvas", "svg",
    "webp", "avif", "base64", "blob", "data", "mime", "charset", "utf",
    
    # Generic web content management terms
    "cms", "admin", "dashboard", "backend", "frontend", "api", "endpoint",
    "webhook", "cron", "cache", "session", "token", "auth", "oauth"
}

WEB_COOKIE_INDICATORS = [
    "tracking cookies", "analytics cookies", "advertising cookies", 
    "gdpr compliance", "cookie consent", "privacy policy",
    "data protection", "personal data", "collect personal information",
    "third party cookies", "performance cookies", "functional cookies",
    "targeting cookies", "essential cookies", "browser cookies",
    "website cookies", "cookie preferences", "cookie settings",
    "opt out of cookies", "manage cookie preferences",
    "strictly necessary cookies", "manage consent preferences", "consent tool",
    "cookie consent tool", "always active", "cookie notice", "cookie banner",
    "cookie policy", "social media cookies", "decline accept",
    "consent preferences", "cookie details", "cookie information",
    "cookies are necessary", "cannot be switched off", "personally identifiable",
    "cookie compliance", "data collection", "information we collect",
    "tracking your browser", "profile of your interests", "sharing tools",
    "these cookies", "allow these cookies", "block or alert",
    "privacy preferences", "cookie types", "website functionality"
]

FOOD_COOKIE_INDICATORS = [
    "recipe", "ingredients", "chocolate chip", "baking", "oven temperature",
    "flour", "sugar", "butter", "vanilla extract", "cream",
    "crispy cookies", "chewy cookies", "sweet treats", "dessert recipe", 
    "cookie dough", "bake cookies", "homemade cookies", "cookie recipe",
    "chocolate cookies", "oatmeal cookies", "sugar cookies", "cookie jar"
]

CONSENT_MANAGEMENT_PATTERNS = [
    "manage consent", "consent preferences", "consent tool", "cookie consent",
    "strictly necessary", "always active", "cannot be switched off",
    "privacy preferences", "decline accept", "cookie details",
    "information we collect", "personal data", "tracking your browser",
    "allow these cookies", "cookies details", "performance cookies",
    "targeting cookies", "functional cookies", "social media cookies"
]

PRIVACY_CONTENT_INDICATORS = [
    "gdpr compliance", "data protection", "cookie banner", "cookie notice",
    "third party cookies", "essential cookies", "analytics cookies"
] 

SOCIAL_MEDIA_INDICATORS = [
    "facebook", "twitter", "pinterest", "email", "yummly", "instagram", "linkedin"
]

ERROR_INDICATORS = ["404 |"]

# Processing settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
MARKDOWN_CHUNK_SIZE = 800
MARKDOWN_CHUNK_OVERLAP = 80
MAX_KEYWORDS_PER_CHUNK = 10

# Scraping settings
MAX_PAGES_DEFAULT = 1000
MAX_PAGES_LARGE = 10000
SCRAPER_CONCURRENCY = 5

# N-gram extraction settings
NGRAM_RANGE = (2, 3)
MAX_NGRAMS = 10
MAX_PHRASE_LENGTH = 4