DROP DATABASE IF EXISTS tracemysteps;
CREATE DATABASE tracemysteps;
\connect tracemysteps;

CREATE EXTENSION postgis;
-- SELECT postgis_full_version();

DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS trips_transportation_modes CASCADE;

CREATE TABLE IF NOT EXISTS locations (
  label TEXT PRIMARY KEY,
  -- Point representative of the location
  centroid GEOGRAPHY(POINTZ, 4326) NULL,
  -- Cluster of points that derived the location
  point_cluster geography(LINESTRINGZ, 4326) NULL,
  
  visit_frequency INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS trips (
  trip_id SERIAL PRIMARY KEY,

  start_location TEXT REFERENCES locations(label),
  end_location TEXT REFERENCES locations(label),

  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,

  bounds geography(POLYGONZ, 4326) NOT NULL,
  points geography(LINESTRINGZ, 4326) NOT NULL,
  -- LineString requires at least two positions.
  -- LineString defines a line through the points in given order. MultiPoint defines a finite collection of points.

  -- Length of timestamps must be the same as the length of points
  timestamps TIMESTAMP WITH TIME ZONE[] NULL,

  start_of_trip DATE NOT NULL

  -- para efeitos de load, cada track e uma trip
);


CREATE TABLE IF NOT EXISTS stays (
  stay_id SERIAL PRIMARY KEY,
  trip_id INTEGER REFERENCES trips(trip_id) NULL, -- pode ser dispensavel isto aqui.
  -- nao temos que necessariamente saber as viagens associadas as stays
  -- pois as pessoas ao observarem as viagens vao lembrar se das localizacoes
  -- e por conseguinte sabem que tiveram no sitio x e foram para o sitio y
  -- essa associacao nao e importante aqui  
  location_label TEXT REFERENCES locations(label),
  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  time_spent INTEGER NOT NULL,
  ddmmyy DATE NOT NULL
  -- cada linha de um LIFE e uma stay
);


CREATE TABLE IF NOT EXISTS trips_transportation_modes (
  mode_id TEXT PRIMARY KEY, -- String
  trip_id INTEGER REFERENCES trips(trip_id) NOT NULL,

  label TEXT NOT NULL,

  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,

  -- Indexes of Trips(point/timestamp)
  start_index INTEGER NOT NULL,
  end_index INTEGER NOT NULL,
  bounds geography(POLYGONZ, 4326) NOT NULL
);
