from os import getenv
import os
import ppygis
import psycopg2
import psycopg2.extras
import gpxpy
import gpxpy.gpx
from life_source import Life
from datetime import datetime, timedelta

def dbPoint(point):
    return ppygis.Point(point.latitude, point.longitude, point.elevation, srid=4326).write_ewkb()

def dbPoints(points):
    return ppygis.LineString(map(lambda p: ppygis.Point(p.latitude, p.longitude, p.elevation, srid=4326), points), 4326).write_ewkb()

def dbBounds(bound):
    return ppygis.Polygon([
        ppygis.LineString(
            [   ppygis.Point(bound[0], bound[1], 0, srid=4336),
                ppygis.Point(bound[0], bound[3], 0, srid=4336),
                ppygis.Point(bound[2], bound[1], 0, srid=4336),
                ppygis.Point(bound[2], bound[3], 0, srid=4336)])]).write_ewkb()

def insertLocation(cur, label, point):
    cur.execute("""
            SELECT label, centroid, point_cluster
            FROM locations
            WHERE label=%s
            """, (label, ))
    if cur.rowcount > 0:
        # Updates current location set of points and centroid
        _, centroid, point_cluster = cur.fetchone()
        #centroid = ppygis.Geometry.read_ewkb(centroid)
        point_cluster = ppygis.Geometry.read_ewkb(point_cluster)

        # TODO
        #centroid = ST_Centroid(point_cluster)
        #point_cluster.points.append(ppygis.Point(point.latitude, point.longitude, point.elevation, srid=4326))

        cur.execute("""
                UPDATE locations
                SET point_cluster=%s
                WHERE label=%s
                """, (point_cluster.write_ewkb(), label))

        #cur.execute("""
        #        UPDATE locations
        #        SET centroid=ST_Centroid(point_cluster::geometry)
        #        WHERE label=%s
        #        """, (label, ))
    else:
        # Creates new location
        cur.execute("""
                INSERT INTO locations (label, centroid, point_cluster)
                VALUES (%s, %s, %s)
                """, (label, dbPoint(point), dbPoints([point])))


def insertTrip(trip):
    for segment in trip.segments:
        insertSegment(segment)

    # TODO
    # cur.execute("""
            # INSERT INTO stays(trip_id, location_label, start_date, end_date)
            # VALUES (%s, %s, %s, %s)
            # """, (trip_id, a))



def insertSegment(cur, segment):

    insertLocation(cur, segment.location_from, segment.startPoint)
    insertLocation(cur, segment.location_to, segment.endPoint)

    def toTsmp(d):
        return psycopg2.Timestamp(d.year, d.month, d.day, d.hour, d.minute, d.second)

    tstamps = map(lambda p: p.time, segment.points)
    # TODO: timestamps
    cur.execute("""
            INSERT INTO trips (start_location, end_location, start_date, end_date, bounds, points, timestamps)
            VALUES (%s, %s, %s, %s, NULL, %s, %s)
            RETURNING trip_id
            """,
            (   segment.location_from,
                segment.location_to,
                segment.points[0].time,
                segment.points[-1].time,
                #dbBounds(segment.getBounds()),
                dbPoints(segment.points),
                tstamps
                ))
    trip_id = cur.fetchone()
    trip_id = trip_id[0]

    # for tmode in segment.transportation_modes:
    #     insertTransportationMode(cur, tmode, trip_id, segment)

    return trip_id


def connectDB():
    connectionString = 'dbname=tracemysteps user=PedroFrancisco host=localhost'
    #print connectionString
    try:
      return psycopg2.connect(connectionString)
    except:
      print("Can't connect to database")

def load(gpx):
	conn = connectDB()
	cur = conn.cursor()
	for track in gpx.tracks:
		for segment in track.segments:
			startLabel = ""
			endLabel = ""
			endPoint = ""
			for point in segment.points:
				label = life.where_when(point.time.strftime("%Y_%m_%d"), point.time.strftime("%H%M"))
				if(startLabel == ""):
					startLabel = label
					setattr(segment, 'location_from', label)
					setattr(segment, 'startPoint', point)
				if(label != ""):
					endLabel = label
					endPoint = point
				print 'Point at ({0},{1}) -> {2} {3}'.format(point.latitude, point.longitude, point.elevation, point.time)
				if label is None or len(label) == 0:
					print("No label TODO INSERT TRIP")
				elif not isinstance(label, basestring):
					print("TODO INSERT TRIP {0} {1}".format(label[0], label[1]))
				else:
					insertLocation(cur, label, point)
			setattr(segment, 'location_to', endLabel)
			setattr(segment, 'endPoint', endPoint)
			insertSegment(cur, segment)

	conn.commit()
	cur.close()
	conn.close()				


life = Life("MyTracks.life")
files_directory = 'MyTracks/'

files =[]
for f in os.listdir(files_directory):
    files.append(f)
files.sort()

for f in files:
	if f.endswith(".gpx"):
		filename = os.path.join(files_directory, f)
		print filename
		gpx_file = open(filename, 'r')
		tracks = gpxpy.parse(gpx_file)
		load(tracks)
