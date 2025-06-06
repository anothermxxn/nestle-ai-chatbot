import aiohttp
import logging
import math
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus

try:
    from backend.config.store_locator import (
        OSRM_API_CONFIG,
        OSRM_ENDPOINTS,
        OVERPASS_API_CONFIG,
        CANADIAN_RETAILERS,
        EXCLUDE_KEYWORDS,
        VALID_SHOP_TYPES,
        VALID_AMENITY_TYPES,
    )
except ImportError:
    from config.store_locator import (
        OSRM_API_CONFIG,
        OSRM_ENDPOINTS,
        OVERPASS_API_CONFIG,
        CANADIAN_RETAILERS,
        EXCLUDE_KEYWORDS,
        VALID_SHOP_TYPES,
        VALID_AMENITY_TYPES,
    )

logger = logging.getLogger(__name__)

@dataclass
class StoreLocation:
    """Data class for store location information."""
    name: str
    address: str
    lat: float
    lon: float
    distance: float
    duration: float
    phone: Optional[str] = None
    hours: Optional[str] = None
    brand: Optional[str] = None
    google_maps_url: str = ""

class StoreLocatorService:
    """Service for finding nearby retail stores using OSRM routing and OpenStreetMap data."""
    
    def __init__(self):
        self.osrm_base_url = OSRM_API_CONFIG["base_url"]
        self.osrm_endpoints = OSRM_ENDPOINTS
        self.timeout = OSRM_API_CONFIG["timeout"]
        self.default_radius = OSRM_API_CONFIG["default_radius_km"]
        self.max_results = OSRM_API_CONFIG["max_results"]
        self.max_candidates = OSRM_API_CONFIG["max_candidates"]
        self.routing_profile = OSRM_API_CONFIG["routing_profile"]
        self.overpass_url = OVERPASS_API_CONFIG["url"]
        self.exclude_keywords = EXCLUDE_KEYWORDS

    def _build_overpass_query(self, lat: float, lon: float, radius_km: float) -> str:
        """Build Overpass query to find retail stores in the area."""
        # Calculate bounding box
        lat_delta = radius_km / 111.0 
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        south = lat - lat_delta
        west = lon - lon_delta
        north = lat + lat_delta
        east = lon + lon_delta

        retailers_pattern = "|".join(CANADIAN_RETAILERS)
        
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          // Grocery stores and supermarkets with retailer names
          node["shop"="supermarket"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          way["shop"="supermarket"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          
          // General shops with retailer names
          node["shop"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          way["shop"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          
          // Department stores
          node["shop"="department_store"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          way["shop"="department_store"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          
          // Convenience stores  
          node["shop"="convenience"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
          way["shop"="convenience"]["name"~"^({retailers_pattern})", i]({south},{west},{north},{east});
        );
        out center;
        """
        
        return query

    def _is_valid_store(self, element: Dict) -> bool:
        """Filter out non-store locations based on name and tags."""
        tags = element.get("tags", {})
        name = tags.get("name", "").lower()
        
        # Check if name contains excluded keywords
        for keyword in self.exclude_keywords:
            if keyword in name:
                return False
        
        # Must have a shop or amenity tag to be a valid store
        if not (tags.get("shop") or tags.get("amenity")):
            return False
            
        # Additional validation for known store types
        shop_type = tags.get("shop", "")
        amenity_type = tags.get("amenity", "")
        
        if shop_type and shop_type not in VALID_SHOP_TYPES:
            return False
            
        if amenity_type and amenity_type not in VALID_AMENITY_TYPES:
            return False
        
        return True

    def _calculate_haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float, include_duration: bool = False) -> tuple[float, float] | float:
        """
        Calculate Haversine distance between two coordinates.
        
        Args:
            lat1: Origin latitude
            lon1: Origin longitude  
            lat2: Destination latitude
            lon2: Destination longitude
            include_duration: If True, returns (distance, duration)
            
        Returns:
            Distance in meters, or tuple of (distance, duration) if include_duration=True
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c  # meters
        
        if include_duration:
            duration = distance / (30 * 1000 / 3600)  # seconds (assumes 30 km/h average speed)
            return distance, duration
        
        return distance
    
    def _extract_coordinates(self, element: Dict) -> tuple[float, float]:
        """
        Extract latitude and longitude from OpenStreetMap element.
        
        Args:
            element: OSM element with coordinate data
            
        Returns:
            Tuple of (latitude, longitude)
        """
        if element.get("type") == "way":
            lat = element.get("center", {}).get("lat", 0)
            lon = element.get("center", {}).get("lon", 0)
        else:
            lat = element.get("lat", 0)
            lon = element.get("lon", 0)
        
        return lat, lon

    async def _calculate_routing_distance(self, origin_lat: float, origin_lon: float, 
                                        dest_lat: float, dest_lon: float, 
                                        transport_mode: str = "driving") -> tuple[float, float]:
        """Calculate routing distance and duration using OSRM."""
        endpoint = self.osrm_endpoints.get(transport_mode, self.osrm_endpoints["driving"])
        
        coordinates = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = f"{endpoint}/{coordinates}"
        
        params = {
            "overview": OSRM_API_CONFIG["overview"],
            "steps": OSRM_API_CONFIG["steps"],
            "geometries": "geojson"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        # Fallback to straight-line distance if routing fails
                        return self._calculate_haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon, include_duration=True)
                    
                    data = await response.json()
                    
                    if data.get("code") != "Ok" or not data.get("routes"):
                        return self._calculate_haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon, include_duration=True)
                    
                    route = data["routes"][0]
                    distance = route["distance"]  # meters
                    duration = route["duration"]  # seconds
                    
                    return distance, duration
                    
        except Exception as e:
            logger.error(f"OSRM routing error: {e}")
            return self._calculate_haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon, include_duration=True)

    async def _get_store_locations(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Get potential store locations from Overpass API."""
        query = self._build_overpass_query(lat, lon, radius_km)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.overpass_url,
                    data=query,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"Overpass API error: HTTP {response.status}")
                        return []
                    
                    result = await response.json()
                    elements = result.get("elements", [])
                    
                    # Filter valid stores
                    valid_stores = []
                    for element in elements:
                        if self._is_valid_store(element):
                            valid_stores.append(element)
                    
                    return valid_stores
                    
        except Exception as e:
            logger.error(f"Error querying Overpass API: {e}")
            return []

    async def _reverse_geocode_address(self, lat: float, lon: float) -> str:
        """
        Get address from coordinates using reverse geocoding.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Address string or None if reverse geocoding fails
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "json",
                "lat": lat,
                "lon": lon,
                "zoom": 18,
                "addressdetails": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers={"User-Agent": "Nestle-Chatbot/1.0"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Try to build a compact address from the response
                        address_parts = []
                        address = data.get("address", {})
                        
                        # Extract city
                        city = (address.get("city") or 
                               address.get("town") or 
                               address.get("village") or 
                               address.get("municipality"))
                        
                        # Extract postal code
                        postal_code = address.get("postcode")
                        
                        # Create compact format: "City, Postal Code"
                        if city and postal_code:
                            return f"{city}, {postal_code}"
                        elif city:
                            return city
                        else:
                            # Fallback to street + city if available
                            if address.get("road"):
                                address_parts.append(address["road"])
                            
                            if city:
                                address_parts.append(city)
                            elif postal_code:
                                address_parts.append(postal_code)
                            
                            if address_parts:
                                return ", ".join(address_parts)
                        
                            # Final fallback to display_name if available
                            return data.get("display_name")
            
        except Exception as e:
            logger.debug(f"Reverse geocoding failed for {lat}, {lon}: {e}")
            return None

    async def _format_store_data(self, element: Dict, distance: float, duration: float) -> StoreLocation:
        """Format raw Overpass data into StoreLocation object."""
        lat, lon = self._extract_coordinates(element)
        
        tags = element.get("tags", {})
        
        name = tags.get("name", "Unknown Store")
        
        # Try to enhance store data with Google Maps first (for phone and hours)
        google_enhanced = await self._enhance_store_with_google_maps(name, lat, lon)
        
        # For address, prioritize compact format from reverse geocoding
        address = None
        
        # Try reverse geocoding first for compact city + postal code format
        reverse_address = await self._reverse_geocode_address(lat, lon)
        if reverse_address:
            address = reverse_address
        else:
            # Fallback: Try Google Maps address if available
            if google_enhanced["address"]:
                address = google_enhanced["address"]
            else:
                # Fallback: Try to build from structured OSM data
                address_parts = []
                if tags.get("addr:city"):
                    address_parts.append(tags["addr:city"])
                if tags.get("addr:postcode"):
                    address_parts.append(tags["addr:postcode"])
                
                if address_parts:
                    address = ", ".join(address_parts)
                else:
                    # Last resort: use a more user-friendly coordinate display
                    address = f"{name} (Location: {lat:.3f}, {lon:.3f})"
        
        # Prioritize Google Maps phone, then OSM data
        phone = google_enhanced["phone"] or tags.get("phone") or tags.get("contact:phone")
        
        # Prioritize Google Maps hours, then OSM data
        hours = google_enhanced["hours"] or tags.get("opening_hours")
        
        brand = None
        name_lower = name.lower()
        for retailer in CANADIAN_RETAILERS:
            if retailer.lower() in name_lower:
                brand = retailer
                break
        
        # Ensure we always have a valid Google Maps URL
        google_maps_url = google_enhanced.get("url")
        
        # If Google Maps scraping failed or returned empty/invalid URL, use fallback generation
        if not google_maps_url or google_maps_url == "":
            # Create a more specific search query with store name and location
            if address:
                search_query = f"{name}, {address}"
            else:
                search_query = f"{name} near {lat},{lon}"
            
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(search_query)}"
            logger.debug(f"Using enhanced search URL for store '{name}': {google_maps_url}")
        else:
            logger.debug(f"Using scraped Google Maps URL for store '{name}': {google_maps_url}")
        
        return StoreLocation(
            name=name,
            address=address,
            lat=lat,
            lon=lon,
            distance=distance,
            duration=duration,
            phone=phone,
            hours=hours,
            brand=brand,
            google_maps_url=google_maps_url
        )

    async def find_nearby_stores(self, lat: float, lon: float, radius_km: Optional[float] = None, 
                               transport_mode: str = "driving") -> List[StoreLocation]:
        """Find nearby retail stores using OSRM routing for accurate distances."""
        if radius_km is None:
            radius_km = self.default_radius
        
        # Get potential store locations from Overpass API
        logger.info(f"Searching for stores within {radius_km}km using {transport_mode} routing...")
        store_elements = await self._get_store_locations(lat, lon, radius_km)
        
        if not store_elements:
            logger.info("No stores found in the area")
            return []
        
        logger.info(f"Found {len(store_elements)} potential stores")
        
        # Pre-filter by straight-line distance
        stores_with_distance = []
        for element in store_elements:
            store_lat, store_lon = self._extract_coordinates(element)
            
            if store_lat and store_lon:
                straight_distance = self._calculate_haversine_distance(lat, lon, store_lat, store_lon)
                if straight_distance <= radius_km * 1000:
                    stores_with_distance.append((element, straight_distance, store_lat, store_lon))
        
        # Sort by straight-line distance and take only the closest candidates
        stores_with_distance.sort(key=lambda x: x[1])
        closest_candidates = stores_with_distance[:self.max_candidates]
        
        logger.info(f"Pre-filtered to {len(closest_candidates)} closest candidates for routing calculation...")
        
        # Calculate routing distance
        stores_with_routing = []
        for element, straight_distance, store_lat, store_lon in closest_candidates:
            try:
                distance, duration = await self._calculate_routing_distance(
                    lat, lon, store_lat, store_lon, transport_mode
                )
                store = await self._format_store_data(element, distance, duration)
                stores_with_routing.append(store)
                
            except Exception as e:
                logger.error(f"Routing calculation failed for store: {e}")
                continue
        
        # Sort by routing distance and return top results
        stores_with_routing.sort(key=lambda x: x.distance)
        final_results = stores_with_routing[:self.max_results]
        
        logger.info(f"Found {len(final_results)} stores with accurate routing distances")
        return final_results
    
    def format_stores_for_response(self, stores: List[StoreLocation]) -> List[Dict]:
        """
        Format store locations for response display.
        
        Args:
            stores (List[StoreLocation]): List of StoreLocation objects
            
        Returns:
            List[Dict]: Formatted store information for response
        """
        if not stores:
            return []
        
        formatted_stores = []
        for store in stores:
            formatted_store = {
                "name": store.name,
                "address": store.address,
                "distance": f"{store.distance/1000:.1f} km",
                "duration": f"{int(store.duration/60)} min",
                "phone": store.phone,
                "hours": store.hours,
                "url": store.google_maps_url,
                "lat": store.lat,
                "lon": store.lon  # Use consistent "lon" naming
            }
            formatted_stores.append(formatted_store)
        
        return formatted_stores

    async def _enhance_store_with_google_maps(self, store_name: str, lat: float, lon: float) -> Dict[str, Optional[str]]:
        """
        Enhance store information by scraping Google Maps search results.
        
        Args:
            store_name: Name of the store
            lat: Store latitude
            lon: Store longitude
            
        Returns:
            Dictionary with enhanced store information (address, phone, hours)
        """
        enhanced_data = {
            "address": None,
            "phone": None,
            "hours": None,
            "city": None,
            "postal_code": None,
            "url": None
        }
        
        try:
            # Construct Google Maps search URL with specific location information
            search_query = f"{store_name} near {lat},{lon}"
            # Use search URL format that reliably finds the specific location
            search_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(search_query)}"
            
            # Always include the search URL as primary choice
            enhanced_data["url"] = search_url
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as response:
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse the content for store details and URL
                        parsed_data = self._parse_google_maps_content(content, store_name)
                        enhanced_data.update(parsed_data)
                        
                        # If no specific store URL was found, keep search URL as fallback
                        if not enhanced_data.get("url"):
                            enhanced_data["url"] = search_url
                    else:
                        logger.debug(f"Google Maps search failed with status {response.status} for {store_name}")
            
        except Exception as e:
            logger.debug(f"Error enhancing store data from Google Maps for {store_name}: {e}")
            
        # Final safety check - ensure we always have a URL
        if not enhanced_data.get("url"):
            # Last resort: create a search URL with store name and coordinates
            search_query = f"{store_name} near {lat},{lon}"
            enhanced_data["url"] = f"https://www.google.com/maps/search/?api=1&query={quote_plus(search_query)}"
            logger.debug(f"Applied final safety URL for {store_name}")
            
        return enhanced_data

    def _parse_google_maps_content(self, content: str, store_name: str) -> Dict[str, Optional[str]]:
        """
        Parse Google Maps HTML content to extract store information.
        
        Args:
            content: HTML content from Google Maps search
            store_name: Store name for validation
            
        Returns:
            Dictionary with parsed store information
        """
        enhanced_data = {
            "address": None,
            "phone": None,
            "hours": None,
            "city": None,
            "postal_code": None,
            "url": None
        }
        
        try:
            # Extract full address first
            full_address = None
            address_patterns = [
                r'"address":"([^"]+)"',
                r'data-value="([^"]*\d+[^"]*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)[^"]*)"',
                r'"formattedAddress":"([^"]+)"',
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    address = match.group(1).strip()
                    # Clean up common escape sequences
                    address = address.replace("\\u003c", "<").replace("\\u003e", ">")
                    address = address.replace("\\u0026", "&").replace("\\n", " ")
                    if len(address) > 10 and any(word in address.lower() for word in ["street", "st", "avenue", "ave", "road", "rd", "boulevard", "blvd"]):
                        full_address = address
                        break
            
            # Extract city and postal code from full address or specific patterns
            if full_address:
                # Try to extract city and postal code from full address
                # Canadian postal code pattern: Letter-Number-Letter Number-Letter-Number
                postal_match = re.search(r'([A-Z]\d[A-Z]\s*\d[A-Z]\d)', full_address, re.IGNORECASE)
                if postal_match:
                    enhanced_data["postal_code"] = postal_match.group(1).upper()
                
                # Extract city - typically before postal code or province
                city_patterns = [
                    r',\s*([^,]+?)\s*(?:ON|BC|AB|SK|MB|QC|NB|NS|PE|NL|NT|YT|NU)[\s,]',  # Before province
                    r',\s*([^,]+?)\s*[A-Z]\d[A-Z]',  # Before postal code
                    r',\s*([^,]+?)(?:\s*,\s*Canada)?$',  # Last part before country
                ]
                
                for pattern in city_patterns:
                    city_match = re.search(pattern, full_address, re.IGNORECASE)
                    if city_match:
                        city = city_match.group(1).strip()
                        if len(city) > 2 and not re.match(r'^[A-Z]\d[A-Z]', city):  # Not a postal code
                            enhanced_data["city"] = city
                            break
            
            # Look for specific city and postal code patterns if not found in address
            if not enhanced_data["city"]:
                city_patterns = [
                    r'"city":"([^"]+)"',
                    r'"locality":"([^"]+)"',
                    r'"address_components":[^}]*"long_name":"([^"]+)"[^}]*"types":\["locality"',
                ]
                
                for pattern in city_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        enhanced_data["city"] = match.group(1).strip()
                        break
            
            if not enhanced_data["postal_code"]:
                postal_patterns = [
                    r'"postal_code":"([^"]+)"',
                    r'"postalCode":"([^"]+)"',
                    r'([A-Z]\d[A-Z]\s*\d[A-Z]\d)',  # Canadian postal code pattern
                ]
                
                for pattern in postal_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        postal = match.group(1).strip().upper()
                        if re.match(r'^[A-Z]\d[A-Z]\s*\d[A-Z]\d$', postal):
                            enhanced_data["postal_code"] = postal
                            break
            
            # Create compact address from city and postal code
            if enhanced_data["city"] and enhanced_data["postal_code"]:
                enhanced_data["address"] = f"{enhanced_data['city']}, {enhanced_data['postal_code']}"
            elif enhanced_data["city"]:
                enhanced_data["address"] = enhanced_data["city"]
            elif full_address:
                # Fallback to shortened version of full address
                # Take city part if we can identify it
                parts = full_address.split(",")
                if len(parts) >= 2:
                    # Take last 2 parts which usually contain city and province/postal
                    enhanced_data["address"] = ", ".join(parts[-2:]).strip()
                else:
                    enhanced_data["address"] = full_address
            
            # Extract phone number
            phone_patterns = [
                r'"phoneNumber":"([^"]+)"',
                r'"telephone":"([^"]+)"',
                r'(\(\d{3}\)\s*\d{3}-\d{4})',
                r'(\d{3}-\d{3}-\d{4})',
                r'(\+1\s*\d{3}\s*\d{3}\s*\d{4})',
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, content)
                if match:
                    phone = match.group(1).strip()
                    # Validate phone number format
                    if re.match(r"^[\+\(\)\d\s-]+$", phone) and len(phone) >= 10:
                        enhanced_data["phone"] = phone
                        break
            
            # Extract hours information
            hours_patterns = [
                r'"hours":"([^"]+)"',
                r'"openingHours":"([^"]+)"',
                r'"operatingHours":"([^"]+)"',
                r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^"]*\d+:\d+[^"]*(?:AM|PM))',
            ]
            
            for pattern in hours_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    hours = match.group(1).strip()
                    # Clean up and validate hours
                    hours = hours.replace("\\n", " ").replace("\\u003c", "<").replace("\\u003e", ">")
                    if any(day in hours.lower() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                        enhanced_data["hours"] = hours
                        break
            
            # Extract actual store URL from search results
            url_patterns = [
                # Store page URLs in search results - most common pattern
                r'href="(/maps/place/[^"]*/@[^"]*)"',
                r'"(/maps/place/[^"]*/@[^"]*)"',
                # Complete URLs with coordinates
                r'"(https://www\.google\.com/maps/place/[^"]*/@[^"]*)"',
                # Place data URLs with real coordinates
                r'href="([^"]*maps/place/[^"]*/@[\d\.-]+,[\d\.-]+[^"]*)"',
            ]
            
            store_url = None
            for i, pattern in enumerate(url_patterns):
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    url = matches[0]
                    if i <= 1:  # Relative URLs
                        store_url = f"https://www.google.com{url}"
                    elif i >= 2:  # Complete URLs
                        store_url = url
                    
                    # Validate the URL has real coordinates (not 0,0)
                    if store_url and ("maps/place/" in store_url) and ("@0,0" not in store_url):
                        enhanced_data["url"] = store_url
                        break
            
        except Exception as e:
            logger.debug(f"Error parsing Google Maps content: {e}")
            
        return enhanced_data