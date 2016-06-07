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
  centroid GEOGRAPHY(POINTZ, 4326) NOT NULL,
  -- Cluster of points that derived the location
  point_cluster geography(LINESTRINGZ, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
  trip_id SERIAL PRIMARY KEY,

  start_location TEXT REFERENCES locations(label), -- erase NULL
  end_location TEXT REFERENCES locations(label), -- erase NULL

  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, -- IS NOT NULL
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, -- IS NOT NULL

  bounds geography(POLYGONZ, 4326) NULL, -- IS NOT NULL
  points geography(LINESTRINGZ, 4326) NOT NULL, -- IS NOT NULL
  -- LineString requires at least two positions.
  -- LineString defines a line through the points in given order. MultiPoint defines a finite collection of points.

  -- Length of timestamps must be the same as the length of points
  timestamps TIMESTAMP WITHOUT TIME ZONE[] NULL

  -- para efeitos de load, cada track e uma trip
);

CREATE TABLE IF NOT EXISTS trips_transportation_modes (
  mode_id SERIAL PRIMARY KEY,
  trip_id SERIAL REFERENCES trips(trip_id) NOT NULL,

  label TEXT NOT NULL,

  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,

  -- Indexes of Trips(point/timestamp)
  start_index INTEGER NOT NULL,
  end_index INTEGER NOT NULL,
  bounds geography(POLYGONZ, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS stays (
  stay_id SERIAL PRIMARY KEY,
  trip_id SERIAL REFERENCES trips(trip_id),
  location_label TEXT REFERENCES locations(label),
  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL
  -- cada linha de um LIFE e uma stay
);

--INSERT INTO trips (trip_id) VALUES (1);
--INSERT INTO trips_transportation_modes (trip_id, label, start_date, end_date, start_index, end_index, bounds) VALUES (1, 'exemplo', '2015-10-19 10:23:54',
--'2015-10-19 19:23:54', 10, 11, ST_GeomFromText('POLYGON Z((398000.0 7542000.0 279.9, 398000.0 7541990.0 281.0, 398010.0 7541990.0 280.4, 398010.0 7542000.0 279.4, 398000.0 7542000.0 279.9))', 4326));

