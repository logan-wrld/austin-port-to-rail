/**
 * Ship Tracking Module
 * Tracks vessels from AIS data, persists to localStorage, and monitors docking/unloading status
 */

const ShipTracker = {
    // Storage key for localStorage
    STORAGE_KEY: 'port_houston_ship_tracker',
    
    // Ship status constants
    STATUS: {
        INBOUND: 'inbound',
        APPROACHING: 'approaching', 
        DOCKING: 'docking',
        DOCKED: 'docked',
        UNLOADING: 'unloading',
        DEPARTING: 'departing',
        OUTBOUND: 'outbound'
    },

    // Port facility zones for docking detection
    terminalZones: [
        { name: "Barbours Cut", lat: 29.7234, lng: -95.0012, radius: 0.01 },
        { name: "Bayport", lat: 29.6234, lng: -94.9912, radius: 0.01 },
        { name: "Turning Basin", lat: 29.7355, lng: -95.2755, radius: 0.015 },
        { name: "Care Terminal", lat: 29.7156, lng: -95.0234, radius: 0.008 },
        { name: "Jacintoport", lat: 29.7456, lng: -95.0834, radius: 0.008 },
        { name: "Galena Park", lat: 29.7356, lng: -95.2155, radius: 0.01 },
        { name: "Manchester", lat: 29.7256, lng: -95.2555, radius: 0.01 },
        { name: "Galveston Wharves", lat: 29.3108, lng: -94.7872, radius: 0.012 },
        { name: "Texas City", lat: 29.3834, lng: -94.9134, radius: 0.01 }
    ],

    /**
     * Initialize tracker - load existing data from localStorage
     */
    init() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                this.data = JSON.parse(stored);
            } catch (e) {
                console.error('Failed to parse stored ship data:', e);
                this.data = this._createEmptyData();
            }
        } else {
            this.data = this._createEmptyData();
        }
        console.log(`ShipTracker initialized: ${Object.keys(this.data.vessels).length} tracked vessels`);
        return this;
    },

    /**
     * Create empty data structure
     */
    _createEmptyData() {
        return {
            vessels: {},           // mmsi -> vessel data
            history: [],           // Array of status change events
            stats: {
                totalTracked: 0,
                currentlyDocked: 0,
                unloadingNow: 0,
                departedToday: 0,
                lastUpdated: null
            }
        };
    },

    /**
     * Save data to localStorage
     */
    save() {
        this.data.stats.lastUpdated = new Date().toISOString();
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.data));
    },

    /**
     * Calculate distance between two points (in degrees, approximate)
     */
    _distance(lat1, lng1, lat2, lng2) {
        const dLat = lat2 - lat1;
        const dLng = lng2 - lng1;
        return Math.sqrt(dLat * dLat + dLng * dLng);
    },

    /**
     * Determine which terminal a vessel is near (if any)
     */
    getNearestTerminal(lat, lng) {
        for (const terminal of this.terminalZones) {
            const dist = this._distance(lat, lng, terminal.lat, terminal.lng);
            if (dist <= terminal.radius) {
                return terminal;
            }
        }
        return null;
    },

    /**
     * Determine vessel status based on position and speed
     */
    determineStatus(vessel, previousData = null) {
        const speed = vessel.speed || 0;
        const lat = vessel.lat;
        const lng = vessel.lng;
        
        // Check if near a terminal
        const terminal = this.getNearestTerminal(lat, lng);
        
        if (terminal) {
            if (speed < 0.5) {
                // Stationary at terminal
                if (previousData && previousData.status === this.STATUS.DOCKED) {
                    // Already docked - check if unloading (time-based estimation)
                    const dockedAt = new Date(previousData.dockedAt);
                    const now = new Date();
                    const hoursDockedan = (now - dockedAt) / (1000 * 60 * 60);
                    
                    if (hoursDockedan > 0.5 && hoursDockedan < 24) {
                        return { status: this.STATUS.UNLOADING, terminal: terminal.name };
                    } else if (hoursDockedan >= 24) {
                        return { status: this.STATUS.DOCKED, terminal: terminal.name, note: 'Extended stay' };
                    }
                }
                return { status: this.STATUS.DOCKED, terminal: terminal.name };
            } else if (speed < 3) {
                return { status: this.STATUS.DOCKING, terminal: terminal.name };
            }
        }
        
        // Check if in channel/bay area (approaching port)
        if (lat > 29.4 && lat < 29.8 && lng > -95.3 && lng < -94.7) {
            if (speed > 0) {
                // Determine direction based on heading or position
                if (lng < -95.1) {
                    return { status: this.STATUS.DEPARTING, terminal: null };
                }
                return { status: this.STATUS.APPROACHING, terminal: null };
            }
        }
        
        // Further out - inbound or outbound
        if (lat < 29.4) {
            // In Gulf - determine by heading if available
            const heading = vessel.heading || 0;
            if (heading > 270 || heading < 90) {
                return { status: this.STATUS.INBOUND, terminal: null };
            }
            return { status: this.STATUS.OUTBOUND, terminal: null };
        }
        
        return { status: this.STATUS.INBOUND, terminal: null };
    },

    /**
     * Update tracking for a single vessel
     */
    trackVessel(vessel) {
        const mmsi = vessel.mmsi;
        if (!mmsi) return null;
        
        const now = new Date().toISOString();
        const previousData = this.data.vessels[mmsi];
        const statusInfo = this.determineStatus(vessel, previousData);
        
        // Create or update vessel record
        const vesselRecord = {
            mmsi: mmsi,
            name: vessel.name || previousData?.name || `Vessel ${mmsi}`,
            type: vessel.type || previousData?.type || 'Unknown',
            flag: vessel.flag || previousData?.flag || '',
            lat: vessel.lat,
            lng: vessel.lng,
            speed: vessel.speed || 0,
            heading: vessel.heading || 0,
            destination: vessel.destination || previousData?.destination || '',
            status: statusInfo.status,
            terminal: statusInfo.terminal,
            lastSeen: now,
            firstSeen: previousData?.firstSeen || now,
            dockedAt: null,
            unloadingStarted: null,
            positionHistory: previousData?.positionHistory || []
        };
        
        // Track status changes
        if (previousData && previousData.status !== statusInfo.status) {
            // Log status change to history
            this.data.history.push({
                mmsi: mmsi,
                name: vesselRecord.name,
                fromStatus: previousData.status,
                toStatus: statusInfo.status,
                terminal: statusInfo.terminal,
                timestamp: now
            });
            
            // Keep history to last 500 entries
            if (this.data.history.length > 500) {
                this.data.history = this.data.history.slice(-500);
            }
            
            // Update docking/unloading timestamps
            if (statusInfo.status === this.STATUS.DOCKED) {
                vesselRecord.dockedAt = now;
            } else if (statusInfo.status === this.STATUS.UNLOADING) {
                vesselRecord.dockedAt = previousData.dockedAt;
                vesselRecord.unloadingStarted = now;
            }
        } else if (previousData) {
            // Preserve timestamps
            vesselRecord.dockedAt = previousData.dockedAt;
            vesselRecord.unloadingStarted = previousData.unloadingStarted;
        }
        
        // Add position to history (keep last 50 positions)
        vesselRecord.positionHistory.push({
            lat: vessel.lat,
            lng: vessel.lng,
            speed: vessel.speed || 0,
            timestamp: now
        });
        if (vesselRecord.positionHistory.length > 50) {
            vesselRecord.positionHistory = vesselRecord.positionHistory.slice(-50);
        }
        
        // Store updated record
        this.data.vessels[mmsi] = vesselRecord;
        
        return vesselRecord;
    },

    /**
     * Update tracking for multiple vessels (batch update from AIS feed)
     */
    updateFromAIS(vessels) {
        if (!vessels || !Array.isArray(vessels)) return;
        
        const updated = [];
        vessels.forEach(vessel => {
            const record = this.trackVessel(vessel);
            if (record) updated.push(record);
        });
        
        // Update stats
        this._updateStats();
        
        // Save to localStorage
        this.save();
        
        return updated;
    },

    /**
     * Update statistics
     */
    _updateStats() {
        const vessels = Object.values(this.data.vessels);
        const now = new Date();
        const today = now.toDateString();
        
        this.data.stats = {
            totalTracked: vessels.length,
            currentlyDocked: vessels.filter(v => 
                v.status === this.STATUS.DOCKED || v.status === this.STATUS.UNLOADING
            ).length,
            unloadingNow: vessels.filter(v => v.status === this.STATUS.UNLOADING).length,
            inbound: vessels.filter(v => 
                v.status === this.STATUS.INBOUND || v.status === this.STATUS.APPROACHING
            ).length,
            departing: vessels.filter(v => 
                v.status === this.STATUS.DEPARTING || v.status === this.STATUS.OUTBOUND
            ).length,
            departedToday: this.data.history.filter(h => 
                h.toStatus === this.STATUS.DEPARTING && 
                new Date(h.timestamp).toDateString() === today
            ).length,
            lastUpdated: now.toISOString()
        };
    },

    /**
     * Get all tracked vessels
     */
    getAllVessels() {
        return Object.values(this.data.vessels);
    },

    /**
     * Get vessels by status
     */
    getVesselsByStatus(status) {
        return Object.values(this.data.vessels).filter(v => v.status === status);
    },

    /**
     * Get docked vessels
     */
    getDockedVessels() {
        return this.getVesselsByStatus(this.STATUS.DOCKED)
            .concat(this.getVesselsByStatus(this.STATUS.UNLOADING));
    },

    /**
     * Get recent history (last N events)
     */
    getRecentHistory(count = 20) {
        return this.data.history.slice(-count).reverse();
    },

    /**
     * Get statistics
     */
    getStats() {
        return this.data.stats;
    },

    /**
     * Get vessel by MMSI
     */
    getVessel(mmsi) {
        return this.data.vessels[mmsi] || null;
    },

    /**
     * Export data to JSON file
     */
    exportData() {
        const blob = new Blob([JSON.stringify(this.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ship_tracker_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Import data from JSON
     */
    importData(jsonData) {
        try {
            const imported = JSON.parse(jsonData);
            if (imported.vessels && imported.history) {
                this.data = imported;
                this.save();
                return true;
            }
        } catch (e) {
            console.error('Failed to import data:', e);
        }
        return false;
    },

    /**
     * Clear all tracking data
     */
    clearData() {
        this.data = this._createEmptyData();
        this.save();
    },

    /**
     * Remove stale vessels (not seen in X hours)
     */
    cleanupStale(hoursThreshold = 48) {
        const now = new Date();
        const threshold = hoursThreshold * 60 * 60 * 1000;
        
        Object.keys(this.data.vessels).forEach(mmsi => {
            const vessel = this.data.vessels[mmsi];
            const lastSeen = new Date(vessel.lastSeen);
            if (now - lastSeen > threshold) {
                delete this.data.vessels[mmsi];
            }
        });
        
        this._updateStats();
        this.save();
    },

    /**
     * Sync data to backend API
     */
    async syncToServer(apiUrl = 'http://localhost:5001') {
        try {
            const response = await fetch(`${apiUrl}/api/ship-tracker`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...this.data,
                    merge: true  // Merge with existing server data
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Ship tracker synced to server:', result);
                return true;
            }
        } catch (e) {
            console.warn('Failed to sync ship tracker to server:', e.message);
        }
        return false;
    },

    /**
     * Load data from backend API
     */
    async loadFromServer(apiUrl = 'http://localhost:5001') {
        try {
            const response = await fetch(`${apiUrl}/api/ship-tracker`);
            
            if (response.ok) {
                const serverData = await response.json();
                if (serverData.vessels && Object.keys(serverData.vessels).length > 0) {
                    // Merge server data with local data
                    Object.assign(this.data.vessels, serverData.vessels);
                    this.data.history = [
                        ...this.data.history,
                        ...serverData.history.filter(h => 
                            !this.data.history.some(local => 
                                local.mmsi === h.mmsi && local.timestamp === h.timestamp
                            )
                        )
                    ].slice(-500);
                    this._updateStats();
                    this.save();
                    console.log('Ship tracker loaded from server');
                    return true;
                }
            }
        } catch (e) {
            console.warn('Failed to load ship tracker from server:', e.message);
        }
        return false;
    }
};

// Initialize on load
if (typeof window !== 'undefined') {
    ShipTracker.init();
    // Try to load from server after initialization
    setTimeout(() => ShipTracker.loadFromServer(), 2000);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ShipTracker;
}
