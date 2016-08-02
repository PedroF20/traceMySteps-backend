
def getKey(customobj):
    return customobj.getKey()

def copyDirectory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError, e:
        print('Directory not copied. Error: %s' % e)

source_folder = "MyTracks/ProcessedTracks"
destination_folder = "../angular-tracemysteps/ProcessedTracks"

if __name__ == '__main__':
    import shutil
    import gpxpy
    import gpxpy.gpx
    import glob
    import psycopg2
    import ppygis
    import os
    from time import mktime
    import StringIO
    import datetime
    import gpxpy
    import gpxpy.gpx
    import glob
    import os
    import time
    import sys
    print "STARTING..."
    directory_name = 'MyTracks/'
    saving_name = 'ProcessedTracks/'
    saving_directory = os.path.join(directory_name, saving_name)
    DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    print datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    file_count = 0;
    total_size = 0;
    if not os.path.exists(saving_directory):
        os.makedirs(saving_directory)
    current_day = ""
    for entry in sorted(glob.glob(directory_name + "*.[gG][pP][xX]")):

        file = open(entry, 'rb')
        gpx_xml = file.read()
        file.close()

        gpx = gpxpy.parse(gpx_xml)

        for track in gpx.tracks:
            for segment in sorted(track.segments):
                if segment.points[0].time.strftime("%Y-%m-%d") != current_day:
                    name = 0
                else:
                    name += 1

                segment.simplify(5) # RDP

                gpx_write = gpxpy.gpx.GPX()

                # Create first track in our GPX:
                gpx_track = gpxpy.gpx.GPXTrack()

                # Create first segment in our GPX track:
                gpx_segment = gpxpy.gpx.GPXTrackSegment()
                gpx_track.segments.append(segment)
                gpx_write.tracks.append(gpx_track)

                current_day =  segment.points[0].time.strftime("%Y-%m-%d")
                fo = open("{}-part{}.gpx".format(os.path.join(saving_directory,current_day),name), "wb")

                gpx_string = gpx_write.to_xml()
                file_count+=1
                total_size += sys.getsizeof(gpx_string)

                fo.write(gpx_string)
                fo.close()
    print "generated nr files " , file_count
    print "total size "  , total_size
    print datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    copyDirectory(source_folder, destination_folder)
    print "ALL DATA IS PROCESSED AND IMPORTED.\nYOU CAN NOW CLOSE THIS."
