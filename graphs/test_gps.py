from geographiclib.geodesic import Geodesic
import math
geod = Geodesic.WGS84  # define the WGS84 ellipsoid
g = geod.Inverse(42.9985426517204061, -78.7769937515258789, 42.9997667340993388, -78.776991069316864)
print "The distance is {:.3f} m.".format(g['s12'])



