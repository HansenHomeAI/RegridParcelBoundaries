// Parcelizer Web App JavaScript

class ParcelizerApp {
    constructor() {
        this.map = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File input change
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Upload area click
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('click', () => fileInput.click());

        // Coordinates processing
        const processBtn = document.getElementById('processCoordinates');
        processBtn.addEventListener('click', () => this.processCoordinates());

        // Enter key for coordinates
        const coordInput = document.getElementById('coordinatesInput');
        coordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.processCoordinates();
            }
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleFileUpload(file);
        }
    }

    async handleFileUpload(file) {
        // Validate file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf', 'image/tiff', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Unsupported file type. Please upload PNG, JPEG, PDF, or TIFF files.');
            return;
        }

        // Validate file size (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            this.showError('File too large. Maximum size is 16MB.');
            return;
        }

        this.showProgress();
        this.clearError();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.displayResults(result.results);
                this.showSuccess(result.message);
                
                // Display parcel boundaries on map if available
                if (result.map_data && result.map_data.features.length > 0) {
                    this.displayParcelBoundaries(result.map_data);
                }
            } else {
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideProgress();
        }
    }

    async processCoordinates() {
        const coordinates = document.getElementById('coordinatesInput').value.trim();
        
        if (!coordinates) {
            this.showError('Please enter coordinates');
            return;
        }

        this.showProgress();
        this.clearError();

        try {
            const response = await fetch('/coordinates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    coordinates: coordinates
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayResults([result.result]);
                this.showSuccess(result.message);
                
                // Try to show coordinates on map
                this.showCoordinatesOnMap(coordinates);
            } else {
                this.showError(result.error || 'Processing failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideProgress();
        }
    }

    displayResults(results) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        
        resultsContent.innerHTML = '';
        
        results.forEach((result, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            let html = `<h3>Result ${index + 1}</h3>`;
            
            if (result.apn) {
                html += `<p><strong>APN:</strong> ${result.apn}</p>`;
            }
            
            if (result.address) {
                html += `<p><strong>Address:</strong> ${result.address}</p>`;
            }
            
            if (result.county) {
                html += `<p><strong>County:</strong> ${result.county}</p>`;
            }
            
            if (result.state) {
                html += `<p><strong>State:</strong> ${result.state}</p>`;
            }
            
            // Show boundary status
            if (result.has_boundary) {
                html += `<p><strong>✓ Parcel Boundary:</strong> Found (${result.vertices_count} vertices)</p>`;
                html += `<p><strong>Parcel ID:</strong> ${result.parcel_id}</p>`;
            } else {
                html += `<p><strong>✗ Parcel Boundary:</strong> Not found</p>`;
                if (result.error) {
                    html += `<p><em>Error: ${result.error}</em></p>`;
                }
            }
            
            resultItem.innerHTML = html;
            resultsContent.appendChild(resultItem);
        });
        
        resultsSection.style.display = 'block';
    }

    showCoordinatesOnMap(coordinates) {
        try {
            const coords = coordinates.split(',');
            const lat = parseFloat(coords[0].trim());
            const lon = parseFloat(coords[1].trim());
            
            if (isNaN(lat) || isNaN(lon)) {
                return;
            }
            
            this.initMap(lat, lon);
        } catch (error) {
            console.error('Error showing coordinates on map:', error);
        }
    }

    initMap(lat, lon) {
        const mapSection = document.getElementById('mapSection');
        
        // Clear existing map
        if (this.map) {
            this.map.remove();
        }
        
        // Create new map
        this.map = L.map('map').setView([lat, lon], 15);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        // Add marker
        L.marker([lat, lon])
            .addTo(this.map)
            .bindPopup(`Coordinates: ${lat}, ${lon}`)
            .openPopup();
        
        mapSection.style.display = 'block';
    }

    displayParcelBoundaries(mapData) {
        const mapSection = document.getElementById('mapSection');
        
        // Clear existing map
        if (this.map) {
            this.map.remove();
        }
        
        // Determine initial center and zoom
        let center = [39.8283, -98.5795]; // Center of US as default
        let zoom = 4;
        
        if (mapData.center) {
            center = mapData.center;
            zoom = 15;
        }
        
        // Create new map
        this.map = L.map('map').setView(center, zoom);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        // Add parcel boundaries
        const geoJsonLayer = L.geoJSON(mapData, {
            style: {
                color: '#3388ff',
                weight: 3,
                opacity: 0.8,
                fillColor: '#3388ff',
                fillOpacity: 0.2
            },
            onEachFeature: (feature, layer) => {
                // Create popup content
                const props = feature.properties;
                let popupContent = '<div class="parcel-popup">';
                
                if (props.parcel_id) {
                    popupContent += `<h4>Parcel ${props.parcel_id}</h4>`;
                }
                
                if (props.apn) {
                    popupContent += `<p><strong>APN:</strong> ${props.apn}</p>`;
                }
                
                if (props.address) {
                    popupContent += `<p><strong>Address:</strong> ${props.address}</p>`;
                }
                
                if (props.county) {
                    popupContent += `<p><strong>County:</strong> ${props.county}</p>`;
                }
                
                if (props.state) {
                    popupContent += `<p><strong>State:</strong> ${props.state}</p>`;
                }
                
                popupContent += '</div>';
                
                layer.bindPopup(popupContent);
            }
        }).addTo(this.map);
        
        // Fit map to show all parcels
        if (mapData.features.length > 0) {
            this.map.fitBounds(geoJsonLayer.getBounds(), {
                padding: [20, 20]
            });
        }
        
        mapSection.style.display = 'block';
    }

    showProgress() {
        const progressBar = document.getElementById('progressBar');
        progressBar.style.display = 'block';
    }

    hideProgress() {
        const progressBar = document.getElementById('progressBar');
        progressBar.style.display = 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    clearError() {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.style.display = 'none';
    }

    showSuccess(message) {
        // You could add a success message div similar to error
        console.log('Success:', message);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ParcelizerApp();
}); 