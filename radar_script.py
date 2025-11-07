#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Radar Fetcher Script
Fetches RainViewer radar tiles for a specific lat/lon and saves the plot image.
"""

import math
import datetime
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

# ===============================
# CONFIGURATION
# ===============================
ZOOM = 7  # Must be 2–9 (lower = wider coverage)
LAT, LON = 15.7, 121.7  # Your chosen location (example: Luzon, Philippines)
AUTO_SAVE = True  # Set to True to save PNG automatically

# ===============================
# FUNCTIONS
# ===============================

def get_latest_timestamp():
    """Get the latest available RainViewer radar timestamp."""
    r = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
    r.raise_for_status()
    return r.json()["radar"]["past"][-1]["time"]


def get_radar_tile_by_latlon(timestamp, zoom, lat, lon, color=6, tile_size=256, smooth=0, snow=0):
    """Fetch radar tile by lat/lon directly from RainViewer."""
    url = (
        f"https://tilecache.rainviewer.com/v2/radar/"
        f"{timestamp}/{tile_size}/{zoom}/{lat}/{lon}/{color}/{smooth}_{snow}.png"
    )
    print(f"Fetching: {url}")
    r = requests.get(url, timeout=15)
    if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
        return Image.open(BytesIO(r.content)).convert("RGBA")
    else:
        print("Failed to load tile. Status:", r.status_code)
    return None


def plot_tile_on_map(img, lat, lon, zoom, timestamp, save=True):
    """Plot radar tile on map and optionally save as PNG."""
    delta = 360 / (2 ** zoom)
    lat_min, lat_max = lat - delta / 2, lat + delta / 2
    lon_min, lon_max = lon - delta / 2, lon + delta / 2

    plt.rcParams.update({
        'axes.facecolor': '#0e1111',
        'text.color': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white'
    })

    fig, ax = plt.subplots(
        figsize=(10, 10),
        dpi=300,
        facecolor='#0e1111',
        subplot_kw=dict(projection=ccrs.PlateCarree())
    )

    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    ax.imshow(
        img,
        origin='upper',
        extent=[lon_min, lon_max, lat_min, lat_max],
        transform=ccrs.PlateCarree(),
        alpha=0.8,
        zorder=1
    )

    # Land/background and overlays
    ax.add_feature(cfeature.LAND, facecolor='#3a3a3a', zorder=0)
    ax.coastlines(resolution='10m', color='black', linewidth=0.8, zorder=5)
    ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.6, zorder=5)
    ax.add_feature(
        cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='10m',
            facecolor='none'
        ),
        edgecolor='gray', linewidth=0.5, linestyle='--', zorder=5
    )

    # Grid ticks
    xticks = np.linspace(lon_min, lon_max, 9)
    yticks = np.linspace(lat_min, lat_max, 9)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True, number_format='.1f'))
    ax.yaxis.set_major_formatter(LatitudeFormatter(number_format='.1f'))

    # Title and save
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    plt.title(f"Radar @ {dt.strftime('%Y-%m-%d %H:%MZ')}", color='white')

    if save:
        filename = f"radar_{dt.strftime('%Y%m%d_%H%M')}_z{zoom}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved image as {filename}")

    plt.close(fig)


# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    print("Fetching latest radar image...")
    try:
        timestamp = get_latest_timestamp()
        img = get_radar_tile_by_latlon(timestamp, ZOOM, LAT, LON)
        if img:
            plot_tile_on_map(img, LAT, LON, ZOOM, timestamp, save=AUTO_SAVE)
        else:
            print("No image available.")
    except Exception as e:
        print("Error:", e)
