import numpy as np
from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoordinateParameters

# Split dataset into four quadrants and fit separate inverse affine transforms for each.
def fit_by_quadrant(xs, ys, lats, lons):
    # Define boolean masks for each quadrant
    masks = {
        'Q1': (xs >= 0) & (ys >= 0),   # x+, y+
        'Q2': (xs <  0) & (ys >= 0),   # x-, y+
        'Q3': (xs <  0) & (ys <  0),   # x-, y-
        'Q4': (xs >= 0) & (ys <  0)    # x+, y-
    }

    approx_coeffs = {}

    # Q1
    x_q1 = [x for x, mask in zip(xs, masks['Q1']) if mask]
    y_q1 = [y for y, mask in zip(ys, masks['Q1']) if mask]
    lat_q1 = [lat for lat, mask in zip(lats, masks['Q1']) if mask]
    lon_q1 = [lon for lon, mask in zip(lons, masks['Q1']) if mask]
    approx_coeffs['Q1'] = MapCoordinateParameters.fit_transform_params(x_q1, y_q1, lat_q1, lon_q1)

    # Q2
    x_q2 = [x for x, mask in zip(xs, masks['Q2']) if mask]
    y_q2 = [y for y, mask in zip(ys, masks['Q2']) if mask]
    lat_q2 = [lat for lat, mask in zip(lats, masks['Q2']) if mask]
    lon_q2 = [lon for lon, mask in zip(lons, masks['Q2']) if mask]
    approx_coeffs['Q2'] = MapCoordinateParameters.fit_transform_params(x_q2, y_q2, lat_q2, lon_q2)

    # Q3
    x_q3 = [x for x, mask in zip(xs, masks['Q3']) if mask]
    y_q3 = [y for y, mask in zip(ys, masks['Q3']) if mask]
    lat_q3 = [lat for lat, mask in zip(lats, masks['Q3']) if mask]
    lon_q3 = [lon for lon, mask in zip(lons, masks['Q3']) if mask]
    approx_coeffs['Q3'] = MapCoordinateParameters.fit_transform_params(x_q3, y_q3, lat_q3, lon_q3)

    # Q4
    x_q4 = [x for x, mask in zip(xs, masks['Q4']) if mask]
    y_q4 = [y for y, mask in zip(ys, masks['Q4']) if mask]
    lat_q4 = [lat for lat, mask in zip(lats, masks['Q4']) if mask]
    lon_q4 = [lon for lon, mask in zip(lons, masks['Q4']) if mask]
    approx_coeffs['Q4'] = MapCoordinateParameters.fit_transform_params(x_q4, y_q4, lat_q4, lon_q4)  

    return approx_coeffs


def calc_lat_long_by_quadrant(x, y, coefs):
    # Determine quadrant
    if x >= 0 and y >= 0:
        key = 'Q1'
    elif x < 0 and y >= 0:
        key = 'Q2'
    elif x < 0 and y < 0:
        key = 'Q3'
    else:
        key = 'Q4'

    lat_scale, lat_shift, lon_scale, lon_shift = coefs[key]
    lon = (x / lat_scale) + lat_shift
    lat = (y / lon_scale) + lon_shift

    return round(lat, 2), round(lon, 2)

def calc_x_y_by_quadrant(lat, lon, inv_coefs):
    lat_long_center = (32.5, 50.5)  # Center
    


# Example data
x = np.array([249800, 145036, -487890, -116540, 217248, 12900, -139187, -20835, 287353, -36, -118633])
y = np.array([-290796, -228618, -188392, 644819, 629136, 118926, -45225, -143414, -3830, 6, 294801])
lat = np.array([4.5, 10.5, 14.3, 94.7, 93.2, 44, 28.1, 18.7, 32.1, 32.5, 60.9])
long = np.array([92, 64.5, 3.5, 39.3, 71.5, 51.8, 37.1, 48.5, 78.2, 50.5, 39.1])

test_x, test_y = -270145, 128070
true_lat, true_lon = 44.9, 24.5

test_x, test_y = 72480, 288721
test_x, test_y = 197459, 119264
test_x, test_y = 248252, -35658

# Fit models per quadrant and test
coefs = fit_by_quadrant(x, y, lat, long)
pred_lat, pred_lon = calc_lat_long_by_quadrant(test_x, test_y, coefs)
print(f"Predicted lat: {pred_lat}, lon: {pred_lon} for x: {test_x}, y: {test_y}")
