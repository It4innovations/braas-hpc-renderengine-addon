# BRaaS-HPC RenderEngine

## Overview

BRaaS-HPC RenderEngine is a Blender addon that enables high-performance remote rendering using HPC (High-Performance Computing) infrastructure. The addon connects Blender to a remote rendering server via TCP/IP, offloading computationally intensive rendering tasks to powerful HPC systems while maintaining real-time viewport interaction in Blender.

This addon is designed for scientific visualization, volumetric rendering, and scenarios requiring substantial computational resources beyond what local workstations can provide.

## What is this for?

- **Remote HPC Rendering:** Leverage supercomputing resources for real-time viewport rendering
- **Scientific Visualization:** Render complex volumetric data and scientific datasets
- **High-Performance Computing Integration:** Connect Blender directly to HPC rendering servers
- **Real-Time Preview:** View rendered results in the Blender viewport with live updates
- **Custom Rendering Pipelines:** Execute custom rendering commands via script integration

## Features

- **TCP/IP Server Connection:** Connect to remote rendering servers via configurable host and port
- **Viewport Integration:** Real-time rendering directly in Blender's 3D viewport
- **Flexible Pixel Formats:** Support for 8-bit (RGBA BYTE), 16-bit (RGBA HALF), and 32-bit (RGBA FLOAT) pixel formats
- **Camera Synchronization:** Automatic camera parameter synchronization between Blender and remote server
- **Bounding Box Visualization:** Load and visualize volumetric data bounding boxes
- **Command Script Integration:** Execute custom rendering commands via Blender text blocks
- **Frame Animation Support:** Multi-frame rendering with timestep support
- **FPS Monitoring:** Real-time display of both remote and local frame rates

## Requirements

- **Blender:** Version 4.5.0 or higher
- **Operating System:** Windows (code uses platform-specific DLL calls)
- **Python:** Included with Blender (Python 3.x)
- **Dependencies:**
  - Access to [braas_hpc_renderengine_dll](https://github.com/It4innovations/braas-hpc-renderengine) module (platform-specific library)

## Installation

### Step 1: Download

Download the add-on in zip format: https://github.com/It4innovations/braas-hpc-renderengine-addon/releases

### Step 2: Enable the Addon

1. Open Blender (version 4.5.0 or higher)
2. Go to `Edit > Preferences > Add-ons`
3. Click `Install...` button
4. Navigate to the `braas_hpc_renderengine.zip` file and install it
5. Check the box to enable the addon

### Step 5: Configure Addon Preferences

After enabling, you can configure addon preferences:

1. In the Preferences window with the addon enabled, expand the addon details
2. Configure:
   - **Pixel Size:** Choose between 8-bit, 16-bit, or 32-bit pixel formats

## How to Use

### Setting up the Render Engine

1. **Select Render Engine:**
   - Go to the **Render Properties** panel (camera icon in Properties panel)
   - In the **Render Engine** dropdown, select **"BRaaS-HPC"**

### Configuring Server Connection

In the **Render Properties** panel, you'll see the **Server** section:

1. **TCP Server Settings:**
   - **Server:** Enter the hostname or IP address of your HPC rendering server (default: `localhost`)
   - **Port:** Enter the TCP port number (default: `7000`)

2. **Resolution Display:**
   - **Width/Height:** Shows the current viewport resolution (read-only)

3. **Command Script:**
   - **Command Script:** Select a Blender text block containing custom rendering commands
   - These commands will be sent to the remote server to control rendering behavior

### Using the Viewport Renderer

1. Switch to **Viewport Shading** mode by pressing `Z` and selecting **Rendered** mode (or click the rightmost shading icon in the 3D viewport header)
2. The addon will automatically:
   - Connect to the configured server
   - Send camera and scene data
   - Receive and display rendered frames in real-time
   - Update as you navigate or modify the scene

### Loading Bounding Box

Once connected to the server:

1. In the **Render Properties** panel, click **"Load BBox"** button
2. This creates a bounding box object representing the volumetric data dimensions
3. The bounding box is automatically positioned based on data from the remote server

### Monitoring Performance

While rendering, the viewport displays:
- **Time:** Total rendering time
- **Samples:** Number of samples rendered
- **FPS (r):** Remote server frame rate
- **FPS:** Local display frame rate

### Animation Rendering

For multi-frame animations:

1. Set **Time Steps** in the server settings
2. The addon will automatically cycle through timesteps based on the current frame
3. Scrub the timeline to see different frames

## Architecture

### Key Components

1. **`__init__.py`**
   - Main addon entry point
   - Registers/unregisters all addon components

2. **`braas_hpc_renderengine_pref.py`**
   - Addon preferences management
   - Global settings (GPUJPEG, pixel format)

3. **`braas_hpc_renderengine_render.py`**
   - Core rendering engine implementation
   - TCP/IP communication with remote server
   - Camera synchronization
   - Viewport integration
   - Multi-threaded rendering loop

4. **`braas_hpc_renderengine_scene.py`**
   - Scene data management
   - Bounding box creation and visualization
   - Volumetric data range handling

### Rendering Pipeline

1. **Initialization:** Connect to remote server via TCP/IP
2. **Synchronization:** Send camera parameters and scene settings
3. **Command Execution:** Transmit custom rendering commands (if specified)
4. **Rendering:** Remote server processes scene and generates frames
5. **Data Transfer:** Receive rendered pixels via TCP/IP
6. **Display:** Update Blender viewport with received frames
7. **Iteration:** Continuously update on camera/scene changes

# License
This software is licensed under the terms of the [GNU General Public License](https://github.com/It4innovations/braas-hpc-renderengine-addon/blob/main/LICENSE).


# Acknowledgement
This work was supported by the Ministry of Education, Youth and Sports of the Czech Republic through the e-INFRA CZ (ID:90254).

This work was supported by the SPACE project. This project has received funding from the European High- Performance Computing Joint Undertaking (JU) under grant agreement No 101093441. This project has received funding from the Ministry of Education, Youth and Sports of the Czech Republic (ID: MC2304).