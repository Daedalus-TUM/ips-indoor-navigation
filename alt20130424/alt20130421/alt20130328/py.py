from time import *
#sleep(20)

from ctypes import *



class vector3d(Structure):
    _fields_ = [("x", c_double), ("y", c_double), ("z", c_double)]


print "init vector"
test = vector3d()
print "vector initialized"
test.x=5
print test
print test.x

multilat=CDLL('/home/alex/multilateration/multilat.so')

#multilat.main()

numstations = 7


stationtype = c_double * 3 * numstations
radiustype = c_double * numstations
starttype = c_double * 3
stations = stationtype((1,2,3), (100,0,0), (0,100,0), (0,0,100), (-100,5.2,3), (400,500,6000), (400,-5000,600))
radii = radiustype(5,102.2,1503,92,100,6000, 40000)
startpos = starttype(-1.50,-2.50,8.50)
nn = c_int (3)
#print stations

#multilat.testest(nn)
#multilat.testradius(radii, nn)
multilat.teststation(stations, nn)
multilat.teststation2()
#test = vector3d()
test = multilat.main()
print test
test = multilat.wrapper(stations, startpos, radii, nn)
test.restype=vector3d
print test
#multilat.main()
