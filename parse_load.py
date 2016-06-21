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

def getBounds(segment, lowerIndex = 0, upperIndex = -1):
        """Computes the bounds of the segment, or part of it
        Args:
            lowerIndex: Optional, start index. Default is 0
            upperIndex: Optional, end index. Default is -1,
                the last point
        Returns:
            Array with two arrays. The first one with the
            minimum latitude and longitude, the second with
            the maximum latitude and longitude of the segment
            slice
        """
        pointSet = segment.points[lowerIndex:upperIndex]

        minLat = float("inf")
        minLon = float("inf")
        maxLat = -float("inf")
        maxLon = -float("inf")

        for point in pointSet:
            minLat = min(minLat, point.latitude)
            minLon = min(minLon, point.longitude)
            maxLat = max(maxLat, point.latitude)
            maxLon = max(maxLon, point.longitude)

        return (minLat, minLon, maxLat, maxLon)

def getTrackBounds(track):
        minLat = float("inf")
        minLon = float("inf")
        maxLat = -float("inf")
        maxLon = -float("inf")
        for segment in track.segments:
            milat, milon, malat, malon = getBounds(segment)
            minLat = min(milat, minLat)
            minLon = min(milon, minLon)
            maxLat = max(malat, maxLat)
            maxLon = max(malon, maxLon)
        return minLat, minLon, maxLat, maxLon

def insertLocation(cur, label, point):
    print label
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
        print label
        cur.execute("""
                INSERT INTO locations (label, centroid, point_cluster)
                VALUES (%s, %s, %s)
                """, (label, dbPoint(point), dbPoints([point])))
        print label


def insertTransportationMode(cur, tmode, trip_id, segment):
    label = tmode['label']
    fro = tmode['from']
    to = tmode['to']
    cur.execute("""
            INSERT INTO trips_transportation_modes(trip_id, label, start_date, end_date, start_index, end_index, bounds)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (   trip_id, label,
                segment.points[fro].time,
                segment.points[to].time,
                fro, to,
                dbBounds(getBounds(segment, fro, to))))


def insertTrip(cur, trip):
    for segment in trip.segments:
        insertSegment(cur, segment)

    # TODO
    # cur.execute("""
            # INSERT INTO stays(trip_id, location_label, start_date, end_date)
            # VALUES (%s, %s, %s, %s)
            # """, (trip_id, a))


def insertStay(cur, trip_id, location_label, start_date, end_date):

    return stay_id


def insertSegment(cur, segment):
    insertLocation(cur, segment.location_from, segment.startPoint)
    insertLocation(cur, segment.location_to, segment.endPoint)

    def toTsmp(d):
        return psycopg2.Timestamp(d.year, d.month, d.day, d.hour, d.minute, d.second)

    tstamps = map(lambda p: p.time, segment.points)
    cur.execute("""
            INSERT INTO trips (start_location, end_location, start_date, end_date, bounds, points, timestamps)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING trip_id
            """,
            (   segment.location_from,
                segment.location_to,
                segment.points[0].time,
                segment.points[-1].time,
                dbBounds(getBounds(segment)),
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
                if(startLabel == "" and label is not None and not isinstance(label, tuple)):
                    startLabel = label
                    setattr(segment, 'location_from', label)
                    setattr(segment, 'startPoint', point)
                if(label != "" and label is not None and not isinstance(label, tuple)):
                    endLabel = label
                    endPoint = point
                print 'Point at ({0},{1}) -> {2} {3}'.format(point.latitude, point.longitude, point.elevation, point.time)
                if label is None or len(label) == 0:
                    print("No label")
                elif isinstance(label, basestring):
                    insertLocation(cur, label, point)
                else:
                    print("Label is not string. skipping")
            setattr(segment, 'location_to', endLabel)
            setattr(segment, 'endPoint', endPoint)
        insertTrip(cur, track)
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