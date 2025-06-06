/**
 * Get coordinates directly from IP address using geolocation services
 * @returns {Promise<{lat: number, lon: number, city?: string, region?: string} | null>} Coordinates and location info or null if not found
 */
export const ipToCoordinates = async () => {
  try {
    const ipServices = [
      {
        url: 'https://ipapi.co/json/',
        parseData: (data) => {
          if (data.country_code === 'CA' && data.latitude && data.longitude) {
            return {
              lat: parseFloat(data.latitude),
              lon: parseFloat(data.longitude),
              city: data.city,
              region: data.region
            };
          }
          return null;
        }
      },
      {
        url: 'https://ip-api.com/json/',
        parseData: (data) => {
          if (data.status === 'success' && data.countryCode === 'CA' && data.lat && data.lon) {
            return {
              lat: parseFloat(data.lat),
              lon: parseFloat(data.lon),
              city: data.city,
              region: data.regionName
            };
          }
          return null;
        }
      }
    ];

    for (const service of ipServices) {
      try {
        const response = await fetch(service.url, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          timeout: 5000
        });
        
        if (!response.ok) continue;
        
        const data = await response.json();
        const locationData = service.parseData(data);
        
        if (locationData) {
          return locationData;
        }
      } catch {
        continue;
      }
    }
    
    // All services failed
    return null;
    
  } catch (error) {
    console.error('Error getting coordinates from IP:', error);
    return null;
  }
};

/**
 * Convert Canadian FSA (Forward Sortation Area) to coordinates using OpenStreetMap Nominatim
 * @param {string} fsa - Canadian FSA code (e.g., "L4S", "M5V") 
 * @returns {Promise<{lat: number, lon: number} | null>} Coordinates or null if not found
 */
export const fsaToCoordinates = async (fsa) => {
  if (!fsa || typeof fsa !== "string") {
    return null;
  }

  const cleanFsa = fsa.trim().toUpperCase();

  try {
    const query = `${cleanFsa}, Canada`;
    const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=ca&addressdetails=1&limit=1&q=${encodeURIComponent(query)}`;
    
    const response = await fetch(nominatimUrl, {
      headers: {
        "User-Agent": "Nestle-Chatbot" 
      }
    });

    if (!response.ok) {
      console.error(`Nominatim API error: ${response.status}`);
      return null;
    }

    const data = await response.json();
    
    if (data && data.length > 0) {
      const result = data[0];
      const coordinates = {
        lat: parseFloat(result.lat),
        lon: parseFloat(result.lon)
      };
      
      return coordinates;
    } else {
      console.warn(`No coordinates found for FSA: ${cleanFsa}`);
      return null;
    }
    
  } catch (error) {
    console.error(`Error geocoding FSA ${cleanFsa}:`, error);
    return null;
  }
}; 