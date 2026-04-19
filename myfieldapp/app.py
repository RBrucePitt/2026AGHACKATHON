import os
import zipfile
import io
import geopandas as gpd
import uuid
from flask import Flask, render_template, request, send_file, jsonify
from shapely.geometry import shape

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulator')
def simulator():
    # Generate a unique reference for this specific "submission"
    submission_id = str(uuid.uuid4()).upper()
    return render_template('simulation.html', submission_id=submission_id)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # Get GeoJSON data from the frontend
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Convert to GeoDataFrame
        # Leaflet draw returns a FeatureCollection or a single Feature
        gdf = gpd.GeoDataFrame.from_features([data])
        
        # Set the coordinate system to WGS84 (Standard for GPS/USDA)
        gdf.set_crs(epsg=4326, inplace=True)

        # Create an in-memory zip file to hold the .shp components
        zip_buffer = io.BytesIO()
        
        # Temporary directory to save the shapefile components
        temp_folder = "temp_export"
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
            
        base_name = "field_boundary"
        shp_path = os.path.join(temp_folder, f"{base_name}.shp")
        
        # Export to Shapefile
        gdf.to_file(shp_path)

        # Zip the .shp, .shx, .dbf, and .prj files
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                file_path = os.path.join(temp_folder, f"{base_name}{ext}")
                zf.write(file_path, arcname=f"{base_name}{ext}")
                os.remove(file_path) # Clean up temp files

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='field_boundary_shp.zip'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
