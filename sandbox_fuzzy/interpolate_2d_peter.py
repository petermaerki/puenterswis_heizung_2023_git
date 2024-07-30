# import numpy as np
# from scipy.interpolate import griddata

# import matplotlib.pyplot as plt

# grid_x = [-1.0, 0.0, 1.0]
# grid_y = [1.0, 0.0]
# X, Y = np.meshgrid(grid_x,grid_y)

# values=[(40.0,40.0, 45.0),(40.0, 45.0, 50.0)]
# grid = griddata(points, values, method='cubid')

# def func(x, y):
#     return x*(1-x)*np.cos(4*np.pi*x) * np.sin(4*np.pi*y**2)**2

# grid_x, grid_y = np.mgrid[0:1:100j, 0:1:200j]

# rng = np.random.default_rng()
# points = rng.random((1000, 2))
# values = func(points[:,0], points[:,1])

# grid_z0 = griddata(points, values, (grid_x, grid_y), method='nearest')
# grid_z1 = griddata(points, values, (grid_x, grid_y), method='linear')
# grid_z2 = griddata(points, values, (grid_x, grid_y), method='cubic')

# plt.subplot(221)
# plt.imshow(func(grid_x, grid_y).T, extent=(0,1,0,1), origin='lower')
# plt.plot(points[:,0], points[:,1], 'k.', ms=1)
# plt.title('Original')
# plt.subplot(222)
# plt.imshow(grid_z0.T, extent=(0,1,0,1), origin='lower')
# plt.title('Nearest')
# plt.subplot(223)
# plt.imshow(grid_z1.T, extent=(0,1,0,1), origin='lower')
# plt.title('Linear')
# plt.subplot(224)
# plt.imshow(grid_z2.T, extent=(0,1,0,1), origin='lower')
# plt.title('Cubic')
# plt.gcf().set_size_inches(6, 6)
# plt.show()

# print(grid_z2.T)


# from numpy import linspace, meshgrid


# x = [0,4,17]
# y = [-7,25,116]
# z = [50,112,47]



# def grid(x, y, z, resX=100, resY=100):
#     #"Convert 3 column data to matplotlib grid"
#     xi = linspace(min(x), max(x), resX)
#     yi = linspace(min(y), max(y), resY)
#     Z = griddata(x, y, z, xi, yi)
#     X, Y = meshgrid(xi, yi)
#     return X, Y, Z


# X, Y, Z = grid(x, y, z)

# print(X, Y, Z)

# import numpy as np
# from scipy.interpolate import interp2d

# Beispiel Daten
# x = np.array([1, 2, 3, 4])
# y = np.array([5, 6, 7, 8])
# z = np.array([[10, 20, 30, 40],
#               [50, 60, 70, 80],
#               [90, 100, 110, 120],
#               [130, 140, 150, 160]])

# # Erstelle die Interpolationsfunktion
# interp_func = interp2d(x, y, z, kind='linear')

# # Definiere neue Koordinaten für die Interpolation
# new_x = np.array([1.5, 2.5, 3.5])
# new_y = np.array([5.5, 6.5, 7.5])

# # Führe die Interpolation durch
# result = interp_func(new_x, new_y)

#print(result)

# x = np.array([-1, 0, 1])
# y = np.array([1, 0])
# z = np.array([[40.0,40.0, 45.0],[40.0, 45.0, 50.0]])

# interp_func = interp2d(x, y, z, kind='linear')


# print(interp_func(-1, 0))

# https://scipy.github.io/devdocs/notebooks/interp_transition_guide.html

import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import SmoothBivariateSpline, LinearNDInterpolator

x = np.array([1,1,1,2,2,2,4,4,4])
y = np.array([1,2,3,1,2,3,1,2,3])
z = np.array([0,7,8,3,4,7,1,3,4])

xy = np.c_[x, y]   # or just list(zip(x, y))
lut2 = LinearNDInterpolator(xy, z)

X = np.linspace(min(x), max(x))
Y = np.linspace(min(y), max(y))
X, Y = np.meshgrid(X, Y)

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

ax.plot_wireframe(X, Y, lut2(X, Y))
ax.scatter(x, y, z,  'o', color='k', s=48)
fig.show()