from time import *
#sleep(20)

from ctypes import *



class vector3d(Structure):
    _fields_ = [("x", c_double), ("y", c_double), ("z", c_double)]


multilat=CDLL('/home/ga34yoz/ips/multilat.so')

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
#multilat.teststation(stations, nn)
#multilat.teststation2()
test = vector3d()
#test = multilat.main()
#print test
x = c_double
y = c_double
z = c_double
multilat.wrapperx.restype=c_double
multilat.wrappery.restype=c_double
multilat.wrapperz.restype=c_double
#multilat.wrapper.restype=vector3d()
#print test
#test = multilat.wrapper(stations, startpos, radii, nn)
x = multilat.wrapperx(stations, startpos, radii, nn)
y = multilat.wrappery(stations, startpos, radii, nn)
z = multilat.wrapperz(stations, startpos, radii, nn)

print x
print y
print z

test.restype=vector3d
print test
#multilat.main()
