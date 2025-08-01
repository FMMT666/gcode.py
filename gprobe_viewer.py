import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import matplotlib as mpl
from scipy.interpolate import griddata
from collections import defaultdict


SLIDER_START        = 10

ERROR_MAX_OFFSET_Z  = 9.99    # TODO maximum offset across the probing range
ERROR_DEVIATION_Z   = 0.05    # TODO maximum deviation (min, max) at one (x,y) position


def usage():
    print("---\nUsage: python CNC-ProbeView <datafile> [minmax]")
    print()
    print("The data file should contain at least three columns: x, y, z values.")
    print("If multiple (x, y) pairs exist, e.g. from multi-probe data,")
    print("use the 'minmax' option to enable min/max display.")


def load( fname ):
    try:
        data = np.loadtxt(fname, usecols=(0, 1, 2))
    except:
        print( f"Error loading from {fname}.")
        return None

    return data


def analyze_max_deviation( data ):
    x, y, z = data[:,0], data[:,1], data[:,2]

    # in case multiple (x,y) value pairs exist, use the average for z
    points = defaultdict(list)
    for xi, yi, zi in zip(x, y, z):
        points[(xi, yi)].append(zi)

    atLeastOneError = False
    print("ERROR PROBE DEVIATION Z:")
    for (xi, yi), zi_list in points.items():
        if len(zi_list) > 1:
            deviation = max(zi_list) - min(zi_list)
            if deviation > ERROR_DEVIATION_Z:
                atLeastOneError = True
                print( f" ({xi}, {yi}): min={min(zi_list):.4f}, max={max(zi_list):.4f}, diff={deviation:.4f}")
    if not atLeastOneError:
        print(" NONE")


        

def plot( data, enable_minmax = False ):
    mpl.rcParams["axes3d.mouserotationstyle"] = "azel"

    x, y, z = data[:,0], data[:,1], data[:,2]

    # in case multiple (x,y) value pairs exist, use the average for z
    points = defaultdict(list)
    for xi, yi, zi in zip(x, y, z):
        points[(xi, yi)].append(zi)
    xy = [tuple(key) for key in points.keys()]

    xy_all = list(zip(x, y))
    if enable_minmax and len(xy_all) > len(set(xy_all)) :
        print("detected possible multi-probe data; enabling min/max display")
        z_min  = np.array([np.min (points[key]) for key in xy])
        z_max  = np.array([np.max (points[key]) for key in xy])
        minmax = True

    z_mean = np.array([np.mean(points[key]) for key in xy])

    x_unique, y_unique = zip(*xy)

    # a cool grid
    grid_x, grid_y = np.meshgrid(
        np.linspace(x.min(), x.max(), 100),
        np.linspace(y.min(), y.max(), 100)
    )

    if enable_minmax:
        grid_z_min  = griddata(xy, z_min,  (grid_x, grid_y), method='linear')
        grid_z_max  = griddata(xy, z_max,  (grid_x, grid_y), method='linear')

    grid_z_mean = griddata(xy, z_mean, (grid_x, grid_y), method='cubic')

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=25, azim=-120)
    plt.subplots_adjust(left=0.00, right=1.00, bottom=0.00, top=0.95)
    ax.set_box_aspect([1, 1, 0.5])

    # x and y with equal scaling, range limited to data
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()
    xy_range = max(x_max - x_min, y_max - y_min)
    x_center = (x_max + x_min) / 2
    y_center = (y_max + y_min) / 2
    xy_min = min(x_center - xy_range/2, y_center - xy_range/2)
    xy_max = max(x_center + xy_range/2, y_center + xy_range/2)
    ax.set_xlim(x_center - xy_range/2, x_center + xy_range/2)
    ax.set_ylim(y_center - xy_range/2, y_center + xy_range/2)

    # scale z to 1 (assuming metric units)
    z_min = z.min()
    z_max = z.max()
    ax.set_zlim(z_min, 1 / SLIDER_START)

    # plot data
    if enable_minmax:
        surf = ax.plot_surface(grid_x, grid_y, grid_z_min, cmap='Greens', edgecolor='none', alpha=0.7)
        surf = ax.plot_surface(grid_x, grid_y, grid_z_max, cmap='Reds', edgecolor='none', alpha=0.7)

    surf = ax.plot_surface(grid_x, grid_y, grid_z_mean, cmap='inferno', edgecolor='none', alpha=0.7)

    ax.scatter(x, y, z, c='k', s=10, alpha=0.8)  # Schwarz, klein, halbtransparent

    # some labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.title('CNC Probe Data')

    # and a nice slider for the z-range
    ax_slider = plt.axes([0.98, 0.2, 0.015, 0.6])
    slider = Slider(ax_slider, 'z-scale', 1, 50, valinit=10, valstep=1, orientation='vertical')

    def update(val):
        factor = slider.val
        ax.set_zlim(z_min, 1 / factor)
        fig.canvas.draw_idle()

    slider.on_changed(update)
    plt.show()

if __name__ == "__main__":
    enable_minmax = False

    if len(sys.argv) > 1:
        fname = sys.argv[1]
    else:
        usage()
        print("Continuing with demo data ...")
        fname = "gprobe_demo.txt"
        enable_minmax = True

    if len(sys.argv) > 2 and sys.argv[2].lower() == 'minmax':
        enable_minmax = True

    data = load( fname )

    if data is not None:

        analyze_max_deviation( data )
        plot( data, enable_minmax )
