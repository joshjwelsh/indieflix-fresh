// Indieflix Frontend JavaScript
// API Configuration
// For code-server: use proxy path to backend on port 5000
// For production: relative path works since Flask serves both
const API_BASE_URL = window.location.port === '8080' 
    ? 'http://localhost:8080/proxy/5000/api'
    : '/api';

// State
let allMovies = [];
let selectedTheaters = ['ifc_center', 'metrograph', 'syndicated_bk'];
let currentDateFilter = 'all';
let customDate = null;
let searchQuery = '';
let timeRangeStart = null;
let timeRangeEnd = null;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const moviesContainer = document.getElementById('moviesContainer');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const movieCount = document.getElementById('movieCount');
const dateButtons = document.querySelectorAll('.date-btn');
const customDatePicker = document.getElementById('customDate');
const theaterCheckboxes = document.querySelectorAll('.theater-checkbox input[type="checkbox"]');
const clearTheatersBtn = document.getElementById('clearTheaters');
const selectAllTheatersBtn = document.getElementById('selectAllTheaters');
const timeStartInput = document.getElementById('timeStart');
const timeEndInput = document.getElementById('timeEnd');
const clearTimeBtn = document.getElementById('clearTime');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMovies();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    // Search input with debounce
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchQuery = e.target.value.toLowerCase().trim();
        searchTimeout = setTimeout(() => {
            filterAndDisplayMovies();
        }, 300);
    });

    // Date filter buttons
    dateButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active button
            dateButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Clear custom date when selecting predefined filter
            customDatePicker.value = '';
            customDate = null;
            
            // Update current date filter
            currentDateFilter = btn.dataset.date;
            filterAndDisplayMovies();
        });
    });

    // Custom date picker
    customDatePicker.addEventListener('change', (e) => {
        if (e.target.value) {
            // Deactivate all date buttons
            dateButtons.forEach(b => b.classList.remove('active'));
            
            // Set custom date
            customDate = new Date(e.target.value);
            currentDateFilter = 'custom';
            filterAndDisplayMovies();
        }
    });

    // Theater checkboxes
    theaterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateSelectedTheaters();
            filterAndDisplayMovies();
        });
    });

    // Clear all theaters button
    clearTheatersBtn.addEventListener('click', () => {
        theaterCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        updateSelectedTheaters();
        filterAndDisplayMovies();
    });

    // Select all theaters button
    selectAllTheatersBtn.addEventListener('click', () => {
        theaterCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        updateSelectedTheaters();
        filterAndDisplayMovies();
    });

    // Time filter inputs
    if (timeStartInput) {
        timeStartInput.addEventListener('change', () => {
            timeRangeStart = timeStartInput.value;
            filterAndDisplayMovies();
        });
    }

    if (timeEndInput) {
        timeEndInput.addEventListener('change', () => {
            timeRangeEnd = timeEndInput.value;
            filterAndDisplayMovies();
        });
    }

    // Clear time filter button
    if (clearTimeBtn) {
        clearTimeBtn.addEventListener('click', () => {
            timeRangeStart = null;
            timeRangeEnd = null;
            if (timeStartInput) timeStartInput.value = '';
            if (timeEndInput) timeEndInput.value = '';
            filterAndDisplayMovies();
        });
    }
}

// Update selected theaters array
function updateSelectedTheaters() {
    selectedTheaters = Array.from(theaterCheckboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
}

// Load Movies from API
async function loadMovies() {
    try {
        showLoading(true);
        hideError();

        const response = await fetch(`${API_BASE_URL}/movies?recent=true&limit=200`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch movies');
        }

        const data = await response.json();
        
        if (data.success) {
            allMovies = data.movies;
            filterAndDisplayMovies();
        } else {
            throw new Error(data.error || 'Unknown error');
        }

        showLoading(false);
    } catch (error) {
        console.error('Error loading movies:', error);
        showError();
        showLoading(false);
    }
}

// Filter and Display Movies
function filterAndDisplayMovies() {
    let filteredMovies = allMovies;

    // Filter by date
    if (currentDateFilter === 'today') {
        filteredMovies = filteredMovies.filter(movie => isShowingOnDate(movie.dates, new Date()));
    } else if (currentDateFilter === 'tomorrow') {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        filteredMovies = filteredMovies.filter(movie => isShowingOnDate(movie.dates, tomorrow));
    } else if (currentDateFilter === 'custom' && customDate) {
        filteredMovies = filteredMovies.filter(movie => isShowingOnDate(movie.dates, customDate));
    }

    // Filter by selected theaters (multi-select)
    // If no theaters selected, show nothing
    filteredMovies = filteredMovies.filter(movie => 
        selectedTheaters.includes(movie.theater_id)
    );

    // Filter by time range
    if (timeRangeStart || timeRangeEnd) {
        filteredMovies = filteredMovies.filter(movie => 
            hasShowtimeInRange(movie.dates, timeRangeStart, timeRangeEnd)
        );
    }

    // Filter by search query
    if (searchQuery) {
        filteredMovies = filteredMovies.filter(movie =>
            movie.title.toLowerCase().includes(searchQuery) ||
            (movie.director && movie.director.toLowerCase().includes(searchQuery))
        );
    }

    // Update movie count
    movieCount.textContent = filteredMovies.length;

    // Display movies (already sorted by backend SQL)
    displayMovies(filteredMovies);
}

// Check if movie has showtime in specified time range
function hasShowtimeInRange(datesString, startTime, endTime) {
    if (!datesString) return false;
    if (!startTime && !endTime) return true;
    
    // Extract times from the dates string
    // Format: "2024-10-12 (18:15, 20:45)" or "2024-10-12 (6:30 PM, 9:00 PM)"
    const timesMatch = datesString.match(/\(([^)]+)\)/);
    if (!timesMatch) return false;
    
    const times = timesMatch[1].split(',').map(t => t.trim());
    
    // Convert time strings to minutes for comparison
    for (const timeStr of times) {
        const minutes = parseTimeToMinutes(timeStr);
        if (minutes === null) continue;
        
        const startMinutes = startTime ? parseTimeToMinutes(startTime) : 0;
        const endMinutes = endTime ? parseTimeToMinutes(endTime) : 1440; // End of day
        
        if (minutes >= startMinutes && minutes <= endMinutes) {
            return true;
        }
    }
    
    return false;
}

// Parse time string to minutes since midnight
function parseTimeToMinutes(timeStr) {
    if (!timeStr) return null;
    
    // Handle 24-hour format (HH:MM)
    let match = timeStr.match(/^(\d{1,2}):(\d{2})$/);
    if (match) {
        const hours = parseInt(match[1]);
        const minutes = parseInt(match[2]);
        return hours * 60 + minutes;
    }
    
    // Handle 12-hour format with AM/PM (H:MM AM/PM or HH:MM AM/PM)
    match = timeStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (match) {
        let hours = parseInt(match[1]);
        const minutes = parseInt(match[2]);
        const period = match[3].toUpperCase();
        
        if (period === 'PM' && hours !== 12) hours += 12;
        if (period === 'AM' && hours === 12) hours = 0;
        
        return hours * 60 + minutes;
    }
    
    return null;
}

// Check if movie is showing on a specific date
function isShowingOnDate(datesString, targetDate) {
    if (!datesString) return false;
    
    // Convert target date to YYYY-MM-DD format for comparison
    const targetYear = targetDate.getFullYear();
    const targetMonth = String(targetDate.getMonth() + 1).padStart(2, '0');
    const targetDay = String(targetDate.getDate()).padStart(2, '0');
    const targetDateStr = `${targetYear}-${targetMonth}-${targetDay}`;
    
    // If it says "Now Playing" or similar, assume it's showing on any date
    if (datesString.toLowerCase().includes('now playing') || 
        datesString.toLowerCase().includes('ongoing') ||
        datesString.toLowerCase().includes('daily')) {
        return true;
    }
    
    // Extract YYYY-MM-DD date from the beginning of the dates string
    // Format is like "2024-10-12 (18:15, 20:45)" or just "2024-10-12"
    const dateMatch = datesString.match(/^(\d{4}-\d{2}-\d{2})/);
    
    if (dateMatch) {
        const movieDateStr = dateMatch[1];
        return movieDateStr === targetDateStr;
    }
    
    // Fallback for old format (for backwards compatibility)
    const targetMonthName = targetDate.toLocaleDateString('en-US', { month: 'short' });
    const targetDayNum = targetDate.getDate();
    const targetShortStr = `${targetMonthName} ${targetDayNum}`;
    
    if (datesString.includes(targetShortStr)) {
        return true;
    }
    
    return false;
}

// Display Movies in Grid
function displayMovies(movies) {
    if (movies.length === 0) {
        moviesContainer.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: 3rem;">
                <p style="font-size: 1.2rem; color: var(--text-light);">
                    ${searchQuery ? 'No movies found matching your search.' : 'No movies available.'}
                </p>
            </div>
        `;
        return;
    }

    moviesContainer.innerHTML = movies.map(movie => createMovieCard(movie)).join('');
}

// Create Movie Card HTML
function createMovieCard(movie) {
    const theaterName = movie.theater || 'Unknown Theater';
    const title = movie.title || 'Untitled';
    const posterUrl = movie.poster_url || null;
    const runtime = movie.runtime || null;
    const tmdbRating = movie.tmdb_rating || null;
    const genres = movie.genres || null;
    const castMembers = movie.cast_members || null;
    const tmdbOverview = movie.tmdb_overview || null;
    
    const director = movie.director ? `<div class="detail-row">
        <span class="detail-label">Director:</span>
        <span class="detail-value">${escapeHtml(movie.director)}</span>
    </div>` : '';
    const year = movie.year ? `<div class="detail-row">
        <span class="detail-label">Year:</span>
        <span class="detail-value">${movie.year}</span>
    </div>` : '';
    const runtimeDisplay = runtime ? `<div class="detail-row">
        <span class="detail-label">Runtime:</span>
        <span class="detail-value">${formatRuntime(runtime)}</span>
    </div>` : '';
    const dates = movie.dates ? `<div class="detail-row">
        <span class="detail-label">Showing:</span>
        <span class="detail-value">${escapeHtml(movie.dates)}</span>
    </div>` : '';
    const description = movie.description ? `
        <div class="movie-description">
            ${escapeHtml(movie.description)}
        </div>
    ` : '';
    const location = movie.location || '';
    const website = movie.website || '#';

    // Build hover overlay content if TMDB data exists
    const hasEnrichment = genres || castMembers || tmdbOverview || tmdbRating;
    const hoverOverlay = hasEnrichment ? `
        <div class="movie-overlay">
            <div class="overlay-content">
                ${tmdbOverview ? `<p class="overlay-plot">${escapeHtml(tmdbOverview)}</p>` : ''}
                ${genres ? `<p class="overlay-info"><strong>Genres:</strong> ${escapeHtml(genres)}</p>` : ''}
                ${castMembers ? `<p class="overlay-info"><strong>Cast:</strong> ${escapeHtml(castMembers)}</p>` : ''}
                ${tmdbRating ? `<p class="overlay-info"><strong>Rating:</strong> ${tmdbRating}/10</p>` : ''}
            </div>
        </div>
    ` : '';

    return `
        <div class="movie-card">
            ${posterUrl ? `
                <div class="movie-poster">
                    <img src="${posterUrl}" alt="${escapeHtml(title)} poster" loading="lazy">
                </div>
            ` : ''}
            
            <div class="movie-content">
                <div class="movie-header">
                    <span class="theater-badge">${escapeHtml(theaterName)}</span>
                    <h3 class="movie-title">${escapeHtml(title)}</h3>
                </div>
                
                <div class="movie-details">
                    ${director}
                    ${year}
                    ${runtimeDisplay}
                    ${dates}
                </div>
                
                ${description}
                
                <div class="movie-footer">
                    <a href="${website}" target="_blank" rel="noopener noreferrer" class="location-link">
                        📍 ${escapeHtml(location)}
                    </a>
                </div>
            </div>
            
            ${hoverOverlay}
        </div>
    `;
}

// Format runtime from minutes to human readable
function formatRuntime(minutes) {
    if (!minutes) return '';
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours > 0) {
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    }
    return `${mins}m`;
}

// Helper Functions
function showLoading(show) {
    loadingState.style.display = show ? 'block' : 'none';
    moviesContainer.style.display = show ? 'none' : 'grid';
}

function showError() {
    errorState.style.display = 'block';
    moviesContainer.style.display = 'none';
}

function hideError() {
    errorState.style.display = 'none';
}

function formatDate(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
        return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh every 5 minutes
setInterval(() => {
    console.log('Auto-refreshing movie data...');
    loadMovies();
}, 5 * 60 * 1000);
