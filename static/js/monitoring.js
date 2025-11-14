// Forest Monitoring System JavaScript

class ForestMonitoringSystem {
    constructor() {
        this.map = null;
        this.drawnItems = new L.FeatureGroup();
        this.currentArea = null;
        this.areas = [];
        this.monitoringData = [];
        this.alerts = [];
        
        this.init();
    }
    
    init() {
        this.initMap();
        this.initEventListeners();
        this.loadAreas();
        this.loadVegetationIndices();
        this.loadAlerts();
        this.setDefaultDates();
    }
    
    initMap() {
        // Check if map container exists
        const mapContainer = document.getElementById('map');
        if (!mapContainer) {
            console.error('Map container not found');
            return;
        }
        
        // Initialize map
        this.map = L.map('map', {
            center: [0, 0],
            zoom: 2,
            zoomControl: true
        });
        
        // Add base layer with proper options
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
            minZoom: 1,
            noWrap: false
        }).addTo(this.map);
        
        // Force map to invalidate size after initialization
        setTimeout(() => {
            if (this.map) {
                this.map.invalidateSize();
            }
        }, 100);
        
        // Add drawn items layer
        this.map.addLayer(this.drawnItems);
        
        // Initialize draw control
        this.initDrawControl();
    }
    
    initDrawControl() {
        const drawControl = new L.Control.Draw({
            edit: {
                featureGroup: this.drawnItems
            },
            draw: {
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    drawError: {
                        color: '#e1e100',
                        message: '<strong>Error!</strong> Shape edges cannot cross!'
                    },
                    shapeOptions: {
                        color: '#bada55'
                    }
                },
                rectangle: {
                    shapeOptions: {
                        color: '#bada55'
                    }
                },
                polyline: false,
                circle: false,
                marker: false,
                circlemarker: false
            }
        });
        
        this.map.addControl(drawControl);
        
        // Handle draw events
        this.map.on(L.Draw.Event.CREATED, (e) => {
            const layer = e.layer;
            this.drawnItems.addLayer(layer);
            this.currentArea = layer;
            this.showAddAreaModal();
        });
        
        this.map.on(L.Draw.Event.EDITED, (e) => {
            // Handle edit events if needed
        });
        
        this.map.on(L.Draw.Event.DELETED, (e) => {
            // Handle delete events if needed
        });
    }
    
    initEventListeners() {
        // Draw area button
        document.getElementById('drawAreaBtn').addEventListener('click', () => {
            this.enableDrawing();
        });
        
        // Clear map button
        document.getElementById('clearMapBtn').addEventListener('click', () => {
            this.clearMap();
        });
        
        // Analyze area button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeArea();
        });
        
        // Add area button
        document.getElementById('addAreaBtn').addEventListener('click', () => {
            this.showAddAreaModal();
        });
        
        // Save area button
        document.getElementById('saveAreaBtn').addEventListener('click', () => {
            this.saveArea();
        });
        
        // Load monitoring data button
        document.getElementById('loadMonitoringDataBtn').addEventListener('click', () => {
            this.loadMonitoringData();
        });
        
        // Refresh alerts button
        document.getElementById('refreshAlertsBtn').addEventListener('click', () => {
            this.loadAlerts();
        });
    }
    
    enableDrawing() {
        // Enable drawing mode
        const drawControl = this.map._layers[Object.keys(this.map._layers)[0]];
        if (drawControl && drawControl._toolbars) {
            drawControl._toolbars.draw._modes.polygon.handler.enable();
        }
    }
    
    clearMap() {
        this.drawnItems.clearLayers();
        this.currentArea = null;
    }
    
    showAddAreaModal() {
        if (!this.currentArea) {
            alert('Please draw an area first');
            return;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('addAreaModal'));
        modal.show();
    }
    
    async saveArea() {
        if (!this.currentArea) {
            alert('No area selected');
            return;
        }
        
        const name = document.getElementById('areaName').value;
        const description = document.getElementById('areaDescription').value;
        
        if (!name) {
            alert('Please enter a name for the area');
            return;
        }
        
        try {
            // Get GeoJSON from the drawn area
            // toGeoJSON() returns a Feature object, which is what we want
            const geometry = this.currentArea.toGeoJSON();
            
            // Validate that we have a valid geometry
            if (!geometry || !geometry.geometry) {
                alert('Invalid geometry. Please draw the area again.');
                return;
            }
            
            const response = await fetch('/api/areas/create_from_geojson/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    geometry_geojson: geometry  // Send the full Feature object
                })
            });
            
            if (response.ok) {
                const area = await response.json();
                // Ensure this.areas is an array
                if (!Array.isArray(this.areas)) {
                    this.areas = [];
                }
                this.areas.push(area);
                this.updateAreasList();
                this.updateMonitoringAreaSelect();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addAreaModal'));
                modal.hide();
                
                // Clear form
                document.getElementById('areaName').value = '';
                document.getElementById('areaDescription').value = '';
                
                alert('Area saved successfully');
            } else {
                const error = await response.json();
                alert('Error saving area: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error saving area:', error);
            alert('Error saving area: ' + error.message);
        }
    }
    
    async loadAreas() {
        try {
            const response = await fetch('/api/areas/');
            if (response.ok) {
                const data = await response.json();
                // Handle paginated response
                this.areas = data.results || data;
                this.updateAreasList();
                this.updateMonitoringAreaSelect();
                this.addAreasToMap();
            }
        } catch (error) {
            console.error('Error loading areas:', error);
        }
    }
    
    updateAreasList() {
        const areasList = document.getElementById('areasList');
        areasList.innerHTML = '';
        
        this.areas.forEach(area => {
            const areaCard = document.createElement('div');
            areaCard.className = 'card area-card';
            areaCard.innerHTML = `
                <div class="card-body">
                    <h6 class="card-title">${area.name}</h6>
                    <p class="card-text small text-muted">${area.description || 'No description'}</p>
                    <small class="text-muted">
                        Area: ${area.area_hectares ? area.area_hectares.toFixed(2) + ' ha' : 'N/A'}
                    </small>
                </div>
            `;
            
            areaCard.addEventListener('click', () => {
                this.zoomToArea(area);
            });
            
            areasList.appendChild(areaCard);
        });
    }
    
    updateMonitoringAreaSelect() {
        const select = document.getElementById('monitoringAreaSelect');
        select.innerHTML = '<option value="">Select an area...</option>';
        
        this.areas.forEach(area => {
            const option = document.createElement('option');
            option.value = area.id;
            option.textContent = area.name;
            select.appendChild(option);
        });
    }
    
    addAreasToMap() {
        this.areas.forEach(area => {
            if (area.geometry_geojson) {
                const layer = L.geoJSON(area.geometry_geojson, {
                    style: {
                        color: '#3388ff',
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: 0.2
                    }
                }).bindPopup(`<b>${area.name}</b><br>${area.description || ''}`);
                
                this.drawnItems.addLayer(layer);
            }
        });
    }
    
    zoomToArea(area) {
        if (area.geometry_geojson) {
            const layer = L.geoJSON(area.geometry_geojson);
            this.map.fitBounds(layer.getBounds());
        }
    }
    
    async loadVegetationIndices() {
        try {
            const response = await fetch('/api/vegetation-indices/');
            if (response.ok) {
                const data = await response.json();
                // Handle paginated response
                const indices = data.results || data;
                this.updateVegetationIndexSelects(indices);
            }
        } catch (error) {
            console.error('Error loading vegetation indices:', error);
        }
    }
    
    updateVegetationIndexSelects(indices) {
        const selects = ['vegetationIndexSelect', 'monitoringIndexSelect'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (!select) return;
            
            const currentValue = select.value;
            
            // Clear all existing options
            select.innerHTML = '';
            
            // Add default option for monitoringIndexSelect
            if (selectId === 'monitoringIndexSelect') {
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select an index...';
                select.appendChild(defaultOption);
            }
            
            // Add all vegetation indices
            indices.forEach(index => {
                const option = document.createElement('option');
                option.value = index.name;
                option.textContent = `${index.name} - ${index.full_name}`;
                select.appendChild(option);
            });
            
            // Restore previous selection if it still exists
            if (currentValue) {
                const optionExists = Array.from(select.options).some(opt => opt.value === currentValue);
                if (optionExists) {
                    select.value = currentValue;
                }
            } else if (selectId === 'vegetationIndexSelect' && indices.length > 0) {
                // Set default to first index (NDVI if available, otherwise first)
                const ndviIndex = indices.find(idx => idx.name === 'NDVI');
                select.value = ndviIndex ? 'NDVI' : indices[0].name;
            }
        });
    }
    
    async analyzeArea() {
        if (!this.currentArea) {
            alert('Please draw an area first');
            return;
        }
        
        const vegetationIndex = document.getElementById('vegetationIndexSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!vegetationIndex || !startDate || !endDate) {
            alert('Please select vegetation index and date range');
            return;
        }
        
        // Clear previous results
        this.clearPreviousResults();
        
        // Show loading
        const analyzeBtn = document.getElementById('analyzeBtn');
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        analyzeBtn.disabled = true;
        
        try {
            // First, we need to save the area if it hasn't been saved yet
            let areaId = null;
            
            // Check if current area is already saved
            if (this.currentArea && this.currentArea.savedAreaId) {
                areaId = this.currentArea.savedAreaId;
            } else {
                // Save the area first
                const areaName = prompt('Enter a name for this area:');
                if (!areaName) {
                    return;
                }
                
                const geometry = this.currentArea.toGeoJSON();
                
                // Validate geometry
                if (!geometry || !geometry.geometry) {
                    alert('Invalid geometry. Please draw the area again.');
                    analyzeBtn.innerHTML = originalText;
                    analyzeBtn.disabled = false;
                    return;
                }
                
                const saveResponse = await fetch('/api/areas/create_from_geojson/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        name: areaName,
                        description: 'Area created for analysis',
                        geometry_geojson: geometry  // Send the full Feature object
                    })
                });
                
                if (!saveResponse.ok) {
                    const error = await saveResponse.json();
                    alert('Error saving area: ' + (error.error || 'Unknown error'));
                    return;
                }
                
                const savedArea = await saveResponse.json();
                areaId = savedArea.id;
                this.currentArea.savedAreaId = areaId;
                
                // Add to areas list
                if (!Array.isArray(this.areas)) {
                    this.areas = [];
                }
                this.areas.push(savedArea);
                this.updateAreasList();
                this.updateMonitoringAreaSelect();
            }
            
            const response = await fetch('/api/monitoring-data/calculate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    area_of_interest_id: areaId,
                    vegetation_index_name: vegetationIndex,
                    start_date: startDate,
                    end_date: endDate,
                    satellite: 'SENTINEL2'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                alert(`Analysis complete! Processed ${result.data.length} records.`);
                
                // Load and display the monitoring data
                await this.loadMonitoringDataForArea(areaId);
                
                // Display real-time map visualization if available
                if (result.map_html) {
                    this.displayRealtimeMap(result.map_html);
                }
            } else {
                const error = await response.json();
                alert('Error analyzing area: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error analyzing area:', error);
            alert('Error analyzing area: ' + error.message);
        } finally {
            // Restore button
            const analyzeBtn = document.getElementById('analyzeBtn');
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
        }
    }
    
    clearPreviousResults() {
        // Clear previous monitoring data layers from map
        this.map.eachLayer((layer) => {
            if (layer instanceof L.LayerGroup && layer !== this.areasLayer) {
                this.map.removeLayer(layer);
            }
        });
        
        // Clear legend
        const legend = document.getElementById('mapLegend');
        if (legend) {
            legend.remove();
        }
        
        // Clear monitoring data
        this.monitoringData = [];
        
        // Clear monitoring data display
        const container = document.getElementById('monitoringData');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    async loadMonitoringData() {
        const areaId = document.getElementById('monitoringAreaSelect').value;
        const indexName = document.getElementById('monitoringIndexSelect').value;
        
        if (!areaId || !indexName) {
            alert('Please select both area and vegetation index');
            return;
        }
        
        try {
            const response = await fetch(`/api/areas/${areaId}/monitoring_data/?vegetation_index=${indexName}`);
            if (response.ok) {
                const data = await response.json();
                this.monitoringData = data.results || data;
                this.displayMonitoringData();
            }
        } catch (error) {
            console.error('Error loading monitoring data:', error);
        }
    }
    
    async loadMonitoringDataForArea(areaId) {
        try {
            const response = await fetch(`/api/areas/${areaId}/monitoring_data/`);
            if (response.ok) {
                const data = await response.json();
                this.monitoringData = data.results || data;
                this.displayMonitoringData();
                this.displayMonitoringDataOnMap();
            }
        } catch (error) {
            console.error('Error loading monitoring data for area:', error);
        }
    }
    
    displayMonitoringData() {
        const container = document.getElementById('monitoringData');
        container.innerHTML = '';
        
        if (this.monitoringData.length === 0) {
            container.innerHTML = '<p class="text-muted">No monitoring data available</p>';
            return;
        }
        
        // Create table
        const table = document.createElement('table');
        table.className = 'table table-sm monitoring-data-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Mean</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Std Dev</th>
                    <th>Pixels</th>
                </tr>
            </thead>
            <tbody>
                ${this.monitoringData.map(data => `
                    <tr>
                        <td>${new Date(data.acquisition_date).toLocaleDateString()}</td>
                        <td>${data.mean_value.toFixed(4)}</td>
                        <td>${data.min_value.toFixed(4)}</td>
                        <td>${data.max_value.toFixed(4)}</td>
                        <td>${data.std_value.toFixed(4)}</td>
                        <td>${data.pixel_count}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        container.appendChild(table);
        
        // Create chart
        this.createMonitoringChart();
    }
    
    createMonitoringChart() {
        const canvas = document.createElement('canvas');
        canvas.id = 'monitoringChart';
        canvas.style.maxHeight = '300px';
        
        const container = document.getElementById('monitoringData');
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const dates = this.monitoringData.map(d => new Date(d.acquisition_date));
        const meanValues = this.monitoringData.map(d => d.mean_value);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates.map(d => d.toLocaleDateString()),
                datasets: [{
                    label: 'Mean Value',
                    data: meanValues,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
    
    displayMonitoringDataOnMap() {
        if (!this.monitoringData || this.monitoringData.length === 0) {
            return;
        }
        
        // Group data by vegetation index
        const dataByIndex = {};
        this.monitoringData.forEach(data => {
            if (!dataByIndex[data.vegetation_index_name]) {
                dataByIndex[data.vegetation_index_name] = [];
            }
            dataByIndex[data.vegetation_index_name].push(data);
        });
        
        // Create cartographically sound color schemes for vegetation indices
        const vegetationColorSchemes = {
            'NDVI': {
                colors: ['#8B0000', '#FF0000', '#FFFF00', '#00FF00', '#006400'],
                name: 'NDVI (Normalized Difference Vegetation Index)',
                description: 'Vegetation health and density'
            },
            'EVI': {
                colors: ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#228B22'],
                name: 'EVI (Enhanced Vegetation Index)',
                description: 'Enhanced vegetation monitoring'
            },
            'SAVI': {
                colors: ['#8B0000', '#FF6347', '#FFA500', '#9ACD32', '#32CD32'],
                name: 'SAVI (Soil Adjusted Vegetation Index)',
                description: 'Soil-adjusted vegetation index'
            },
            'NDMI': {
                colors: ['#000080', '#4169E1', '#87CEEB', '#F0E68C', '#FFD700'],
                name: 'NDMI (Normalized Difference Moisture Index)',
                description: 'Vegetation moisture content'
            },
            'NBR': {
                colors: ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#006400'],
                name: 'NBR (Normalized Burn Ratio)',
                description: 'Fire severity and burn area detection'
            },
            'NDWI': {
                colors: ['#000080', '#4169E1', '#87CEEB', '#98FB98', '#90EE90'],
                name: 'NDWI (Normalized Difference Water Index)',
                description: 'Water content in vegetation'
            },
            'GNDVI': {
                colors: ['#8B0000', '#FF0000', '#FFFF00', '#00FF00', '#006400'],
                name: 'GNDVI (Green Normalized Difference Vegetation Index)',
                description: 'Green vegetation monitoring'
            },
            'OSAVI': {
                colors: ['#8B0000', '#FF6347', '#FFA500', '#9ACD32', '#32CD32'],
                name: 'OSAVI (Optimized Soil Adjusted Vegetation Index)',
                description: 'Optimized soil-adjusted vegetation'
            },
            'NDRE': {
                colors: ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#228B22'],
                name: 'NDRE (Normalized Difference Red Edge)',
                description: 'Red edge vegetation monitoring'
            },
            'CIRE': {
                colors: ['#8B0000', '#FF6347', '#FFD700', '#9ACD32', '#32CD32'],
                name: 'CIRE (Chlorophyll Index Red Edge)',
                description: 'Chlorophyll content monitoring'
            },
            'LAI': {
                colors: ['#FFFFFF', '#FFE4B5', '#9ACD32', '#228B22', '#006400'],
                name: 'LAI (Leaf Area Index)',
                description: 'Leaf area density'
            }
        };
        
        let colorIndex = 0;
        
        Object.keys(dataByIndex).forEach(indexName => {
            const data = dataByIndex[indexName];
            
            // Get the most recent data point for this index
            const latestData = data.sort((a, b) => new Date(b.acquisition_date) - new Date(a.acquisition_date))[0];
            
            // Get cartographically appropriate color scheme
            const colorScheme = vegetationColorSchemes[indexName] || {
                colors: ['#8B0000', '#FF0000', '#FFFF00', '#00FF00', '#006400'],
                name: indexName,
                description: 'Vegetation index'
            };
            
            // Calculate color based on vegetation value
            // LAI has a different range (0-6), normalize accordingly
            let normalizedValue;
            if (indexName === 'LAI') {
                normalizedValue = Math.max(0, Math.min(1, latestData.mean_value / 6.0));
            } else {
                normalizedValue = Math.max(0, Math.min(1, latestData.mean_value));
            }
            const color = this.interpolateColor(colorScheme.colors, normalizedValue);
            
            // Create a layer group for this vegetation index
            const layerGroup = L.layerGroup();
            
            // Create a polygon that matches the drawn area with cartographic styling
            const polygon = L.polygon(this.currentArea.getLatLngs()[0], {
                color: '#2C3E50', // Dark border for contrast
                weight: 2,
                opacity: 0.9,
                fillColor: color,
                fillOpacity: 0.6 + (normalizedValue * 0.3), // Opacity based on vegetation value
                dashArray: '5, 5' // Subtle dashed border for professional look
            });
            
            // Add cartographically styled popup with data
            polygon.bindPopup(`
                <div style="min-width: 280px; font-family: 'Segoe UI', Arial, sans-serif;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px; margin: -10px -10px 10px -10px; border-radius: 5px 5px 0 0;">
                        <h6 style="margin: 0; font-weight: 600;">${colorScheme.name}</h6>
                        <small style="opacity: 0.9;">${colorScheme.description}</small>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 10px; margin: 0 -10px; border-left: 4px solid ${color};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <strong style="color: #2c3e50;">Latest Analysis</strong>
                            <span style="background: ${color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">
                                ${latestData.mean_value.toFixed(3)}
                            </span>
                        </div>
                        <p style="margin: 4px 0; color: #555;"><strong>Date:</strong> ${latestData.acquisition_date}</p>
                        <p style="margin: 4px 0; color: #555;"><strong>Range:</strong> ${latestData.min_value.toFixed(3)} - ${latestData.max_value.toFixed(3)}</p>
                        <p style="margin: 4px 0; color: #555;"><strong>Std Dev:</strong> ${latestData.std_value.toFixed(3)}</p>
                        <p style="margin: 4px 0; color: #555;"><strong>Pixels:</strong> ${latestData.pixel_count.toLocaleString()}</p>
                    </div>
                    
                    ${data.length > 1 ? `
                        <div style="margin-top: 10px;">
                            <strong style="color: #2c3e50; font-size: 0.9em;">Historical Data (${data.length} points):</strong>
                            <div style="max-height: 120px; overflow-y: auto; margin-top: 5px;">
                                ${data.map(d => `
                                    <div style="display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #eee; font-size: 0.85em;">
                                        <span style="color: #666;">${d.acquisition_date}</span>
                                        <span style="font-weight: 500; color: #2c3e50;">${d.mean_value.toFixed(3)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `);
            
            layerGroup.addLayer(polygon);
            
        // Add to map
        layerGroup.addTo(this.map);
        
        // Add to legend
        this.addToLegend(colorScheme, color, layerGroup, latestData.mean_value, normalizedValue);
        
        // Add cartographic elements
        this.addCartographicElements();
        });
    }
    
    interpolateColor(colors, value) {
        // Interpolate between colors based on value (0-1)
        const steps = colors.length - 1;
        const scaledValue = value * steps;
        const index = Math.floor(scaledValue);
        const fraction = scaledValue - index;
        
        if (index >= steps) return colors[colors.length - 1];
        if (index < 0) return colors[0];
        
        const color1 = this.hexToRgb(colors[index]);
        const color2 = this.hexToRgb(colors[index + 1]);
        
        const r = Math.round(color1.r + (color2.r - color1.r) * fraction);
        const g = Math.round(color1.g + (color2.g - color1.g) * fraction);
        const b = Math.round(color1.b + (color2.b - color1.b) * fraction);
        
        return `rgb(${r}, ${g}, ${b})`;
    }
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    addToLegend(colorScheme, color, layerGroup, meanValue = null, normalizedValue = null) {
        // Create or update legend
        let legend = document.getElementById('mapLegend');
        if (!legend) {
            legend = document.createElement('div');
            legend.id = 'mapLegend';
            legend.className = 'map-legend';
            legend.style.cssText = `
                position: absolute;
                bottom: 30px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1000;
                max-width: 320px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border: 1px solid #e1e8ed;
            `;
            legend.innerHTML = `
                <div style="border-bottom: 2px solid #667eea; padding-bottom: 8px; margin-bottom: 12px;">
                    <h6 style="margin: 0; color: #2c3e50; font-weight: 600; font-size: 14px;">Vegetation Analysis</h6>
                    <small style="color: #7f8c8d;">Click to toggle layers</small>
                </div>
            `;
            this.map.getContainer().appendChild(legend);
        }
        
        // Create color scale indicator
        const colorScale = this.createColorScale(colorScheme.colors, colorScheme.name);
        
        // Add legend item
        const legendItem = document.createElement('div');
        legendItem.style.cssText = `
            margin: 8px 0; 
            cursor: pointer; 
            padding: 10px; 
            border-radius: 6px; 
            border: 1px solid #e1e8ed;
            transition: all 0.2s ease;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        `;
        
        const valueCategory = this.getVegetationCategory(normalizedValue, colorScheme.name);
        
        legendItem.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="display: inline-block; width: 24px; height: 24px; background: ${color}; border-radius: 4px; margin-right: 10px; border: 2px solid #2c3e50; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
                    <div>
                        <div style="font-weight: 600; color: #2c3e50; font-size: 13px;">${colorScheme.name}</div>
                        <div style="font-size: 11px; color: #7f8c8d;">${valueCategory}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: #2c3e50; font-size: 14px;">${meanValue.toFixed(3)}</div>
                    <div style="font-size: 10px; color: #95a5a6;">Value</div>
                </div>
            </div>
            ${colorScale}
        `;
        
        // Add hover effect
        legendItem.addEventListener('mouseenter', () => {
            legendItem.style.backgroundColor = '#e8f4fd';
            legendItem.style.borderColor = '#667eea';
            legendItem.style.transform = 'translateY(-1px)';
            legendItem.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        });
        legendItem.addEventListener('mouseleave', () => {
            legendItem.style.backgroundColor = 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)';
            legendItem.style.borderColor = '#e1e8ed';
            legendItem.style.transform = 'translateY(0)';
            legendItem.style.boxShadow = 'none';
        });
        
        // Add click handler to toggle layer
        legendItem.addEventListener('click', () => {
            if (this.map.hasLayer(layerGroup)) {
                this.map.removeLayer(layerGroup);
                legendItem.style.opacity = '0.6';
                legendItem.style.textDecoration = 'line-through';
                legendItem.style.backgroundColor = '#f1f2f6';
            } else {
                this.map.addLayer(layerGroup);
                legendItem.style.opacity = '1';
                legendItem.style.textDecoration = 'none';
                legendItem.style.backgroundColor = 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)';
            }
        });
        
        legend.appendChild(legendItem);
    }
    
    createColorScale(colors, name) {
        const scaleContainer = document.createElement('div');
        scaleContainer.style.cssText = 'margin-top: 8px; padding: 6px; background: #f8f9fa; border-radius: 4px;';
        
        const scaleBar = document.createElement('div');
        scaleBar.style.cssText = `
            height: 8px; 
            background: linear-gradient(to right, ${colors.join(', ')}); 
            border-radius: 4px; 
            margin-bottom: 4px;
            border: 1px solid #ddd;
        `;
        
        const labels = document.createElement('div');
        labels.style.cssText = 'display: flex; justify-content: space-between; font-size: 9px; color: #7f8c8d;';
        labels.innerHTML = '<span>Low</span><span>High</span>';
        
        scaleContainer.appendChild(scaleBar);
        scaleContainer.appendChild(labels);
        
        return scaleContainer.outerHTML;
    }
    
    getVegetationCategory(value, indexName) {
        if (indexName === 'NDVI' || indexName === 'EVI' || indexName === 'SAVI' || indexName === 'GNDVI' || indexName === 'OSAVI' || indexName === 'NDRE' || indexName === 'CIRE') {
            if (value < 0.2) return 'Bare soil/Water';
            if (value < 0.4) return 'Sparse vegetation';
            if (value < 0.6) return 'Moderate vegetation';
            if (value < 0.8) return 'Dense vegetation';
            return 'Very dense vegetation';
        } else if (indexName === 'NDMI' || indexName === 'NDWI') {
            if (value < 0.2) return 'Low moisture';
            if (value < 0.4) return 'Moderate moisture';
            if (value < 0.6) return 'High moisture';
            return 'Very high moisture';
        } else if (indexName === 'NBR') {
            if (value < 0.1) return 'High burn severity';
            if (value < 0.27) return 'Moderate burn severity';
            if (value < 0.44) return 'Low burn severity';
            if (value < 0.66) return 'Unburned';
            return 'Enhanced regrowth';
        } else if (indexName === 'LAI') {
            if (value < 1.0) return 'Very sparse canopy';
            if (value < 2.0) return 'Sparse canopy';
            if (value < 3.0) return 'Moderate canopy';
            if (value < 4.0) return 'Dense canopy';
            return 'Very dense canopy';
        }
        return 'Vegetation index';
    }
    
    addCartographicElements() {
        // Add north arrow
        if (!document.getElementById('northArrow')) {
            const northArrow = document.createElement('div');
            northArrow.id = 'northArrow';
            northArrow.style.cssText = `
                position: absolute;
                top: 20px;
                right: 20px;
                background: white;
                padding: 8px;
                border-radius: 50%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                z-index: 1000;
                border: 2px solid #2c3e50;
                cursor: pointer;
            `;
            northArrow.innerHTML = `
                <div style="font-size: 20px; color: #2c3e50; font-weight: bold; text-align: center; line-height: 1;">
                    ↑<br><small style="font-size: 8px;">N</small>
                </div>
            `;
            this.map.getContainer().appendChild(northArrow);
            
            // Add click handler to reset map orientation
            northArrow.addEventListener('click', () => {
                this.map.setView(this.map.getCenter(), this.map.getZoom());
            });
        }
        
        // Add scale bar
        if (!document.getElementById('scaleBar')) {
            const scaleBar = document.createElement('div');
            scaleBar.id = 'scaleBar';
            scaleBar.style.cssText = `
                position: absolute;
                bottom: 20px;
                left: 20px;
                background: white;
                padding: 8px 12px;
                border-radius: 4px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                z-index: 1000;
                border: 1px solid #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #2c3e50;
            `;
            
            const updateScaleBar = () => {
                const center = this.map.getCenter();
                const zoom = this.map.getZoom();
                const metersPerPixel = 156543.03392 * Math.cos(center.lat * Math.PI / 180) / Math.pow(2, zoom);
                const scale = this.getScaleForMeters(metersPerPixel);
                scaleBar.innerHTML = `
                    <div style="display: flex; align-items: center;">
                        <div style="width: 60px; height: 2px; background: #2c3e50; margin-right: 8px;"></div>
                        <span style="font-weight: bold;">${scale}</span>
                    </div>
                `;
            };
            
            updateScaleBar();
            this.map.on('zoomend', updateScaleBar);
            this.map.getContainer().appendChild(scaleBar);
        }
        
        // Add coordinate display
        if (!document.getElementById('coordinateDisplay')) {
            const coordDisplay = document.createElement('div');
            coordDisplay.id = 'coordinateDisplay';
            coordDisplay.style.cssText = `
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                z-index: 1000;
                pointer-events: none;
            `;
            this.map.getContainer().appendChild(coordDisplay);
            
            this.map.on('mousemove', (e) => {
                const lat = e.latlng.lat.toFixed(6);
                const lng = e.latlng.lng.toFixed(6);
                coordDisplay.innerHTML = `Lat: ${lat}° | Lng: ${lng}°`;
            });
        }
    }
    
    getScaleForMeters(metersPerPixel) {
        const scales = [
            { meters: 1, label: '1m' },
            { meters: 2, label: '2m' },
            { meters: 5, label: '5m' },
            { meters: 10, label: '10m' },
            { meters: 20, label: '20m' },
            { meters: 50, label: '50m' },
            { meters: 100, label: '100m' },
            { meters: 200, label: '200m' },
            { meters: 500, label: '500m' },
            { meters: 1000, label: '1km' },
            { meters: 2000, label: '2km' },
            { meters: 5000, label: '5km' },
            { meters: 10000, label: '10km' },
            { meters: 20000, label: '20km' },
            { meters: 50000, label: '50km' },
            { meters: 100000, label: '100km' }
        ];
        
        const pixelWidth = 60; // Width of scale bar in pixels
        const metersForScale = metersPerPixel * pixelWidth;
        
        for (let i = scales.length - 1; i >= 0; i--) {
            if (metersForScale >= scales[i].meters) {
                return scales[i].label;
            }
        }
        return '1m';
    }
    
    displayRealtimeMap(mapHtml) {
        // Create a modal to display the real-time map
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'realtimeMapModal';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Real-time Satellite Data Visualization</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="realtimeMapContainer" style="height: 600px; width: 100%;">
                            ${mapHtml}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.appendChild(modal);
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Clean up modal when closed
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts/');
            if (response.ok) {
                const data = await response.json();
                // Handle paginated response
                this.alerts = data.results || data;
                this.displayAlerts();
            }
        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }
    
    displayAlerts() {
        const container = document.getElementById('alertsList');
        container.innerHTML = '';
        
        if (this.alerts.length === 0) {
            container.innerHTML = '<p class="text-muted">No alerts available</p>';
            return;
        }
        
        this.alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert-item alert-${this.getAlertSeverityClass(alert.severity)}`;
            alertDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${alert.area_of_interest_name}</strong> - ${alert.vegetation_index_name}
                        <br>
                        <small>${alert.message}</small>
                        <br>
                        <small class="text-muted">${new Date(alert.created_at).toLocaleString()}</small>
                    </div>
                    <div>
                        <span class="badge bg-${this.getAlertSeverityClass(alert.severity)}">${alert.severity}</span>
                        ${!alert.is_resolved ? '<button class="btn btn-sm btn-outline-primary ms-2" onclick="monitoringSystem.resolveAlert(' + alert.id + ')">Resolve</button>' : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(alertDiv);
        });
    }
    
    getAlertSeverityClass(severity) {
        const classes = {
            'LOW': 'info',
            'MEDIUM': 'warning',
            'HIGH': 'danger',
            'CRITICAL': 'danger'
        };
        return classes[severity] || 'info';
    }
    
    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                this.loadAlerts(); // Refresh alerts
            } else {
                alert('Error resolving alert');
            }
        } catch (error) {
            console.error('Error resolving alert:', error);
            alert('Error resolving alert: ' + error.message);
        }
    }
    
    setDefaultDates() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('startDate').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
    }
    
    getCSRFToken() {
        return window.csrfToken || (() => {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    return value;
                }
            }
            return '';
        })();
    }
}

// Initialize the system when the page loads
let monitoringSystem;
document.addEventListener('DOMContentLoaded', () => {
    monitoringSystem = new ForestMonitoringSystem();
});
