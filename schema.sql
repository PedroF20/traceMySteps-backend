DROP DATABASE IF EXISTS tracemysteps;
CREATE DATABASE tracemysteps;
\connect tracemysteps;

CREATE EXTENSION postgis;
-- SELECT postgis_full_version();

DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS locations CASCADE;

-- CREATE TYPE _timestamp as TIMESTAMP WITHOUT TIME ZONE
-- CREATE TYPE _bounds as GEOGRAPHY(POLYGON, 4326)
-- CREATE TYPE _line as GEOGRAPHY(POINTLINE, 4326)
-- CREATE TYPE location_id as bigint

CREATE TABLE IF NOT EXISTS trips (
  trip_id SERIAL PRIMARY KEY,

  start_location bigint NULL,
  end_location bigint NULL,

  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,

  bounds geography(POLYGON, 4326) NOT NULL,
  points geography(LINESTRING, 4326) NOT NULL,  -- LINESTRING OR MULTIPOINT?
  -- LineString requires at least two positions.
  -- LineString defines a line through the points in given order. MultiPoint defines a finite collection of points.

  -- Length of timestamps must be the same as the lenght of points
  timestamps TIMESTAMP WITHOUT TIME ZONE[] NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
  label TEXT PRIMARY KEY,
  -- Point representative of the location
  centroid GEOGRAPHY(POINTZ, 4326) NOT NULL,
  -- Cluster of points that derived the location
  point_cluster geography(MULTIPOINT, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS stays (
  stay_id SERIAL PRIMARY KEY,
  trip_id SERIAL REFERENCES trips(trip_id),
  location_label TEXT REFERENCES locations(label),
  start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL
);