-- RainSense Farmer Database Schema (SQLite / PostgreSQL compatible)

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_locations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    district TEXT,
    state TEXT,
    crop TEXT,
    notes TEXT,
    rain_alert INTEGER DEFAULT 1,
    nearby_alert INTEGER DEFAULT 1,
    heavy_rain_alert INTEGER DEFAULT 1,
    soil_alert INTEGER DEFAULT 1,
    alert_distance_km REAL DEFAULT 15.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weather_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    precipitation REAL,
    source TEXT DEFAULT 'Open-Meteo',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality TEXT DEFAULT 'GOOD'
);

CREATE TABLE IF NOT EXISTS rainfall_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    rainfall_1h REAL DEFAULT 0.0,
    rainfall_3h REAL DEFAULT 0.0,
    rainfall_6h REAL DEFAULT 0.0,
    rainfall_24h REAL DEFAULT 0.0,
    rainfall_72h REAL DEFAULT 0.0,
    rainfall_rate REAL DEFAULT 0.0,
    source TEXT DEFAULT 'Open-Meteo / Satellite',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS soil_moisture (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    surface_moisture REAL,
    root_moisture REAL,
    status TEXT,
    source TEXT DEFAULT 'Open-Meteo / Model Estimate',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    rain_occurrence INTEGER,
    rainfall_amount REAL,
    probability REAL,
    confidence REAL,
    factors_json TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    location_id TEXT,
    alert_type TEXT,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS data_sources (
    name TEXT PRIMARY KEY,
    status TEXT DEFAULT 'ONLINE',
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    details TEXT
);

CREATE TABLE IF NOT EXISTS model_versions (
    version TEXT PRIMARY KEY,
    algorithm TEXT,
    accuracy REAL,
    f1_score REAL,
    mae REAL,
    rmse REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
