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
 * Convert Canadian FSA (Forward Sortation Area) to coordinates
 * @param {string} fsa - Canadian FSA code
 * @returns {Promise<{success: boolean, coordinates?: {lat: number, lon: number}, error?: string}>} Result with success status and coordinates or error
 */
export const fsaToCoordinates = async (fsa) => {
  if (!fsa || typeof fsa !== "string") {
    return {
      success: false,
      error: "Invalid FSA format"
    };
  }

  const cleanFsa = fsa.trim().toUpperCase();

  const geocodingServices = [
    {
      name: 'Photon-Canada',
      url: `https://photon.komoot.io/api/?q=${encodeURIComponent(`${cleanFsa} Canada`)}&limit=5&bbox=-141,41.7,-52.6,83.1`,
      headers: {},
      parseData: (data) => {
        if (data && data.features && data.features.length > 0) {
          const canadianFeatures = data.features.filter(feature => 
            feature.properties && 
            (feature.properties.country === 'Canada' || 
             feature.properties.countrycode === 'CA' ||
             feature.properties.country_code === 'CA')
          );
          
          const featuresToCheck = canadianFeatures.length > 0 ? canadianFeatures : data.features;
          
          for (const feature of featuresToCheck) {
            if (feature.geometry && feature.geometry.coordinates) {
              const coordinates = feature.geometry.coordinates;
              return {
                lat: coordinates[1],
                lon: coordinates[0]
              };
            }
          }
        }
        return null;
      }
    },
    {
      name: 'Photon-Simple',
      url: `https://photon.komoot.io/api/?q=${encodeURIComponent(cleanFsa)}&limit=3&bbox=-141,41.7,-52.6,83.1`,
      headers: {},
      parseData: (data) => {
        if (data && data.features && data.features.length > 0) {
          for (const feature of data.features) {
            if (feature.geometry && feature.geometry.coordinates) {
              const coordinates = feature.geometry.coordinates;
              return {
                lat: coordinates[1],
                lon: coordinates[0]
              };
            }
          }
        }
        return null;
      }
    }
  ];

  try {
    for (const service of geocodingServices) {
      try {
        const response = await fetch(service.url, {
          headers: service.headers,
          timeout: 8000
        });

        if (!response.ok) {
          continue;
        }

        const data = await response.json();      
        const coordinates = service.parseData(data);
        
        if (coordinates && coordinates.lat && coordinates.lon && 
            !isNaN(coordinates.lat) && !isNaN(coordinates.lon)) {
          return {
            success: true,
            coordinates: coordinates
          };
        }
      } catch {
        continue;
      }
    }
    
    // All services failed
    console.warn(`All geocoding services failed for FSA ${cleanFsa}.`);
    return {
      success: false,
      error: `Unable to locate coordinates for postal code ${cleanFsa}. Please try a different postal code.`
    };
  } catch (error) {
    console.error('Error in geocoding:', error);
    return {
      success: false,
      error: `Failed to validate location for postal code ${cleanFsa}. Please try again.`
    };
  }
};
