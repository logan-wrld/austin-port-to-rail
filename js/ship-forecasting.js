/**
 * Ship Arrival Forecasting Module
 * Calculates ETA, distances, and congestion predictions for Port of Houston
 */

const ShipForecasting = {
    // Port of Houston entrance coordinates
    portLocation: {
        lat: 29.7604,
        lon: -95.0077,
        name: "Port of Houston"
    },

    // Average daily port capacity (configurable)
    avgDailyCapacity: 15,

    /**
     * Convert degrees to radians
     */
    toRadians(degrees) {
        return degrees * Math.PI / 180;
    },

    /**
     * Calculate distance between two points in nautical miles
     * Uses Haversine formula for accuracy
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 3440.065; // Earth's radius in nautical miles
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    },

    /**
     * Simple distance calculation (flat earth approximation for short distances)
     */
    calculateDistanceSimple(lat1, lon1, lat2, lon2) {
        const latDiff = (lat2 - lat1) * 60; // 1° lat ≈ 60 nm
        const lonDiff = (lon2 - lon1) * 60 * Math.cos(this.toRadians(lat1));
        return Math.sqrt(latDiff * latDiff + lonDiff * lonDiff);
    },

    /**
     * Calculate arrival info for a single ship
     * @param {Object} ship - Ship object with lat, lon, speed properties
     * @returns {Object} - Distance, ETA, and forecast window
     */
    calculateArrival(ship) {
        const distance = this.calculateDistance(
            ship.lat, ship.lon,
            this.portLocation.lat, this.portLocation.lon
        );

        // Default speed if not provided (10 knots is typical for cargo ships approaching port)
        const speed = ship.speed || 10;
        
        // ETA in hours
        const etaHours = distance / speed;
        
        // Determine forecast window
        let window, windowClass;
        if (etaHours <= 24) {
            window = "0-24h";
            windowClass = "urgent";
        } else if (etaHours <= 48) {
            window = "24-48h";
            windowClass = "soon";
        } else if (etaHours <= 72) {
            window = "48-72h";
            windowClass = "upcoming";
        } else {
            window = "72h+";
            windowClass = "distant";
        }

        // Calculate arrival time
        const arrivalTime = new Date(Date.now() + etaHours * 60 * 60 * 1000);

        return {
            shipName: ship.name || "Unknown",
            distance: Math.round(distance * 10) / 10, // Round to 1 decimal
            distanceUnit: "nm",
            speed: speed,
            speedUnit: "knots",
            etaHours: Math.round(etaHours * 10) / 10,
            window: window,
            windowClass: windowClass,
            arrivalTime: arrivalTime,
            arrivalTimeFormatted: arrivalTime.toLocaleString()
        };
    },

    /**
     * Calculate distance between two ships
     */
    distanceBetweenShips(ship1, ship2) {
        return this.calculateDistance(ship1.lat, ship1.lon, ship2.lat, ship2.lon);
    },

    /**
     * Analyze arrival frequency and gaps between ships
     * @param {Array} ships - Array of ship objects
     * @returns {Object} - Frequency statistics
     */
    analyzeFrequency(ships) {
        if (!ships || ships.length === 0) {
            return { avgTimeBetweenArrivals: 0, arrivalsPerDay: 0, gaps: [] };
        }

        // Calculate arrivals for all ships
        const arrivals = ships.map(ship => ({
            ...ship,
            ...this.calculateArrival(ship)
        }));

        // Sort by ETA
        arrivals.sort((a, b) => a.etaHours - b.etaHours);

        // Calculate gaps between consecutive arrivals
        const gaps = [];
        for (let i = 1; i < arrivals.length; i++) {
            gaps.push({
                ship1: arrivals[i - 1].shipName,
                ship2: arrivals[i].shipName,
                gapHours: Math.round((arrivals[i].etaHours - arrivals[i - 1].etaHours) * 10) / 10
            });
        }

        // Average gap
        const avgGap = gaps.length > 0 
            ? gaps.reduce((sum, g) => sum + g.gapHours, 0) / gaps.length 
            : 0;

        return {
            avgTimeBetweenArrivals: Math.round(avgGap * 10) / 10,
            arrivalsPerDay: avgGap > 0 ? Math.round((24 / avgGap) * 10) / 10 : 0,
            gaps: gaps,
            sortedArrivals: arrivals
        };
    },

    /**
     * Generate 72-hour forecast with congestion prediction
     * @param {Array} ships - Array of ship objects
     * @returns {Object} - Forecast windows with ship counts and surge scores
     */
    generateForecast(ships) {
        const arrivals = ships.map(ship => this.calculateArrival(ship));

        // Count ships in each window
        const windows = {
            "0-24h": { ships: [], count: 0, surgeScore: 0 },
            "24-48h": { ships: [], count: 0, surgeScore: 0 },
            "48-72h": { ships: [], count: 0, surgeScore: 0 },
            "72h+": { ships: [], count: 0, surgeScore: 0 }
        };

        arrivals.forEach(arrival => {
            windows[arrival.window].ships.push(arrival);
            windows[arrival.window].count++;
        });

        // Calculate surge scores (ships expected vs daily capacity)
        // Each window represents 24 hours
        const dailyCapacity = this.avgDailyCapacity;
        
        for (const key of ["0-24h", "24-48h", "48-72h"]) {
            const count = windows[key].count;
            windows[key].surgeScore = Math.round((count / dailyCapacity) * 100) / 100;
            
            if (windows[key].surgeScore > 1.5) {
                windows[key].congestionLevel = "high";
                windows[key].congestionAlert = "⚠️ High congestion risk";
            } else if (windows[key].surgeScore > 1.0) {
                windows[key].congestionLevel = "moderate";
                windows[key].congestionAlert = "⚡ Moderate congestion likely";
            } else if (windows[key].surgeScore > 0.7) {
                windows[key].congestionLevel = "normal";
                windows[key].congestionAlert = "✓ Normal traffic";
            } else {
                windows[key].congestionLevel = "low";
                windows[key].congestionAlert = "✓ Light traffic";
            }
        }

        return {
            windows: windows,
            totalShips: arrivals.length,
            avgDailyCapacity: dailyCapacity,
            generatedAt: new Date().toLocaleString()
        };
    },

    /**
     * Calculate ship spacing matrix (distances between all pairs)
     * @param {Array} ships - Array of ship objects
     * @returns {Array} - Matrix of distances
     */
    calculateShipSpacing(ships) {
        const spacing = [];
        
        for (let i = 0; i < ships.length; i++) {
            for (let j = i + 1; j < ships.length; j++) {
                const distance = this.distanceBetweenShips(ships[i], ships[j]);
                spacing.push({
                    ship1: ships[i].name || `Ship ${i + 1}`,
                    ship2: ships[j].name || `Ship ${j + 1}`,
                    distance: Math.round(distance * 10) / 10,
                    unit: "nm"
                });
            }
        }

        // Sort by distance
        spacing.sort((a, b) => a.distance - b.distance);
        
        return spacing;
    },

    /**
     * Get summary statistics for dashboard display
     */
    getSummary(ships) {
        const forecast = this.generateForecast(ships);
        const frequency = this.analyzeFrequency(ships);
        const spacing = this.calculateShipSpacing(ships);

        return {
            totalTracked: ships.length,
            next24h: forecast.windows["0-24h"].count,
            next48h: forecast.windows["24-48h"].count,
            next72h: forecast.windows["48-72h"].count,
            avgArrivalGap: frequency.avgTimeBetweenArrivals + " hrs",
            arrivalsPerDay: frequency.arrivalsPerDay,
            closestShips: spacing.length > 0 ? spacing[0] : null,
            congestionRisk: forecast.windows["0-24h"].congestionLevel,
            forecast: forecast,
            frequency: frequency
        };
    }
};

// Export for use in other modules (if using ES modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ShipForecasting;
}
