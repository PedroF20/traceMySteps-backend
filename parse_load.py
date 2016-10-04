from os import getenv
import os
import ppygis
import psycopg2
import psycopg2.extras
import gpxpy
import gpxpy.gpx
import datetime
import life_source
import numpy as np
import life_source
from life_source import Life


life = Life("MyTracks.life")

# We use the already processed tracks. Since the RDP simplification aims at 
# reducing the dataset size, the overall spatial information
# about the places and routes taken still remains intact.
files_directory = 'MyTracks/ProcessedTracks/'


def load_from_life(cur):
    # Insert stays
    for day in life.days:
        date = day.date
        for span in day.spans:
            time_spent = span.length()
            print time_spent
            start = datetime.datetime.strptime("%s %s" % (date, life_source.minutes_to_military(span.start)), "%Y_%m_%d %H%M")
            ddmmyy = datetime.datetime.strptime(date, '%Y_%m_%d').strftime('%Y-%m-%d')
            end = datetime.datetime.strptime("%s %s" % (date, life_source.minutes_to_military(span.end)), "%Y_%m_%d %H%M")
            if type(span.place) is str:
                insertLocation(cur, span.place, None)
                insertStay(cur, span.place, start, end, time_spent, ddmmyy)

def dbPoint(point):
    return ppygis.Point(point.latitude, point.longitude, point.elevation, srid=4326).write_ewkb()


def pointsFromDb(gis_points):
    result = []
    for point in gis_points.points:
        result.append(ppygis.Point(point.x, point.y, point.z, srid=4326))
    return result


def dbPoints(points):
    return ppygis.LineString(map(lambda p: ppygis.Point(p.latitude, p.longitude, p.elevation, srid=4326), points), 4326).write_ewkb()


def computeCentroid(points):
    xs = map(lambda p: p.x, points)
    ys = map(lambda p: p.y, points)
    centroid = ppygis.Point(np.mean(xs), np.mean(ys), 0, srid=4326)
    return centroid


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


def getStartTime(segment):
    return segment.points[0].time


def getTrackStartTime(track):
    lastTime = None
    for segment in track.segments:
        if lastTime is None:
            lastTime = getStartTime(segment)
        elif lastTime > getStartTime(segment):
            lastTime = getStartTime(segment)
    return lastTime


def getEndTime(segment):
    return segment.points[-1].time


def insertLocation(cur, label, point):
    print label
    cur.execute("""
            SELECT label, centroid, point_cluster
            FROM locations
            WHERE label=%s
            """, (label, ))
    if cur.rowcount > 0  and point is None:
        print "ignore"
    elif cur.rowcount > 0:
        # Updates current location set of points and centroid
        _, centroid, point_cluster = cur.fetchone()
        point_cluster = ppygis.Geometry.read_ewkb(point_cluster)

        # # Update point cluster by appending the new point
        # cur.execute("""
        #             UPDATE locations
        #             SET point_cluster = ST_AddPoint(point_cluster::geometry, %s, 1)
        #             WHERE label=%s
        #             """, (dbPoint(point), label))

        # # Get the updated point cluster in order to calculate centroid
        # cur.execute("""
        #             SELECT label, centroid, point_cluster
        #             FROM locations
        #             WHERE label=%s
        #             """, (label, ))
        # _, centroid, point_cluster = cur.fetchone()
        # point_cluster = ppygis.Geometry.read_ewkb(point_cluster)

        if point_cluster is not None:
            centroid = computeCentroid(pointsFromDb(point_cluster))

            cur.execute("""
                    UPDATE locations
                    SET centroid=%s, point_cluster=%s
                    WHERE label=%s
                    """, (centroid.write_ewkb(), point_cluster.write_ewkb(), label))
                    # SET centroid=ST_Force3D(ST_Centroid(%s))
    else:
        # Creates new location
        if label == "":
            # ignore
            print "ignore label vazia"
        elif(point is not None):
            visit_frequency = len(life.when_at(label))
            print visit_frequency
            cur.execute("""
                    INSERT INTO locations (label, centroid, point_cluster, visit_frequency)
                    VALUES (%s, %s, %s, %s)
                    """, (label, dbPoint(point), dbPoints([point]), visit_frequency))
        else:
            cur.execute("""
                    INSERT INTO locations (label)
                    VALUES (%s)
                    """, (label, ))


# Might not be using transportation modes
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
    ids = []
    for segment in trip.segments:
        ids.append(insertSegment(cur, segment))

    # insertStays(cur, trip, ids)


def insertStay(cur, label, start_date, end_date, time_spent, date):
    if label != "":
        cur.execute("""
            INSERT INTO stays(location_label, start_date, end_date, time_spent, ddmmyy)
            VALUES (%s, %s, %s, %s, %s)
            """, (label, start_date, end_date, time_spent, date))


def insertSegment(cur, segment):
    # if hasattr(segment, 'location_from'): # SCALABILITY TEST
        insertLocation(cur, segment.location_from, segment.startPoint)
        insertLocation(cur, segment.location_to, segment.endPoint)

        def toTsmp(d):
            return psycopg2.Timestamp(d.year, d.month, d.day, d.hour, d.minute, d.second)

        #tstamps = map(lambda p: p.time, segment.points)
        tstamps = [p.time for p in segment.points]

        trip_start = segment.points[0].time.strftime("%Y-%m-%d")
        

        cur.execute("""
                INSERT INTO trips (start_location, end_location, start_date, end_date, bounds, points, timestamps, start_of_trip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING trip_id
                """,
                (   segment.location_from,
                    segment.location_to,
                    segment.points[0].time,
                    segment.points[-1].time,
                    dbBounds(getBounds(segment)),
                    dbPoints(segment.points),
                    tstamps,
                    trip_start
                    ))
        trip_id = cur.fetchone()
        trip_id = trip_id[0]

        return trip_id
    # else:
    #     pass


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


files =[]
for f in os.listdir(files_directory):
    files.append(f)
files.sort()

#Temporary
print datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
start_date = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

for f in files:
	if f.endswith(".gpx"):
		filename = os.path.join(files_directory, f)
		print filename
		gpx_file = open(filename, 'r')
		tracks = gpxpy.parse(gpx_file)
		load(tracks)
# load life
conn = connectDB()
cur = conn.cursor()
load_from_life(cur)
conn.commit()
cur.close()
conn.close()

#Temporary
end_date = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

print "ALL DATA IS PROCESSED.\nYOU CAN NOW CLOSE THIS."
print start_date
print "-------------------"
print end_date