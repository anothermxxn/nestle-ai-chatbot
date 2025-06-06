import aiohttp
import asyncio
import logging
import math
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from backend.config.store_locator import (
        OSRM_API_CONFIG,
        OSRM_ENDPOINTS,
        OVERPASS_API_CONFIG,
        CANADIAN_RETAILERS,
        EXCLUDE_KEYWORDS,
        VALID_SHOP_TYPES,
        VALID_AMENITY_TYPES,
        GOOGLE_MAPS_CONFIG
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
        GOOGLE_MAPS_CONFIG
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

    def _format_store_data(self, element: Dict, distance: float, duration: float) -> StoreLocation:
        """Format raw Overpass data into StoreLocation object."""
        lat, lon = self._extract_coordinates(element)
        
        tags = element.get("tags", {})
        
        name = tags.get("name", "Unknown Store")
        
        address_parts = []
        if tags.get("addr:housenumber"):
            address_parts.append(tags["addr:housenumber"])
        if tags.get("addr:street"):
            address_parts.append(tags["addr:street"])
        if tags.get("addr:city"):
            address_parts.append(tags["addr:city"])
        if tags.get("addr:postcode"):
            address_parts.append(tags["addr:postcode"])
        address = ", ".join(address_parts) if address_parts else f"Near {lat:.4f}, {lon:.4f}"
        
        phone = tags.get("phone", tags.get("contact:phone"))
        hours = tags.get("opening_hours")
        
        brand = None
        name_lower = name.lower()
        for retailer in CANADIAN_RETAILERS:
            if retailer.lower() in name_lower:
                brand = retailer
                break
        
        google_maps_url = self._generate_google_maps_url(lat, lon, name)
        
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

    def _generate_google_maps_url(self, lat: float, lon: float, name: str) -> str:
        """Generate Google Maps URL for the store location."""
        base_url = GOOGLE_MAPS_CONFIG["base_url"]
        return f"{base_url}?q={lat},{lon}+({name.replace(' ', '+')})&z={GOOGLE_MAPS_CONFIG['default_zoom']}"

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
                store = self._format_store_data(element, distance, duration)
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
                "google_maps_url": store.google_maps_url
            }
            formatted_stores.append(formatted_store)
        
        return formatted_stores