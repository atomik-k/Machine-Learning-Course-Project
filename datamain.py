import pandas as pd
import folium
from sklearn.cluster import KMeans

bootstrap_css = "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css"
bootstrap_js = "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"
df = pd.read_csv('Homicides_Data.csv')

# Filter data for a specific crime code and remove rows with missing values
df = df[df['Crm Cd'] == 110]
df = df.dropna(subset=['Vict Age', 'LAT', 'LON'])


# Age groups
bins = [0, 30, 40, 50, 60, 120]
labels = ['0-29', '30-39', '40-49', '50-59', '60+']
df['age_group'] = pd.cut(df['Vict Age'], bins=bins, labels=labels, right=False)

# Function to perform K-means clustering for each age group
def cluster_by_age_group(df, age_groups, k):
    cluster_centers = {}
    cluster_points = {}
    for age_group in age_groups:
        age_group_data = df[df['age_group'] == age_group]
        kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42)
        clusters = kmeans.fit_predict(age_group_data[['LAT', 'LON']])
        cluster_centers[age_group] = kmeans.cluster_centers_
        cluster_points[age_group] = [age_group_data.iloc[clusters == i] for i in range(k)]
    return cluster_centers, cluster_points

# Number of clusters per age group
k = 3

# Cluster centers and points for each age group
cluster_centers, cluster_points = cluster_by_age_group(df, labels, k)

# Folium map
LA_map = folium.Map(location=[34.0522, -118.2437], zoom_start=10)

age_group_colors = {
    '0-29': 'red',
    '30-39': 'green',
    '40-49': 'blue',
    '50-59': 'black',
    '60+': 'brown'
}

# Loop through age groups and visualize cluster centers and incidents
for age_group, centers in cluster_centers.items():
    points = cluster_points[age_group]
    for center, color in zip(centers, [age_group_colors[age_group]]*len(centers)):
        folium.Marker(
            location=[center[0], center[1]],
            icon=folium.Icon(color=age_group_colors[age_group], prefix='fa',icon="flag"),
            popup=f"Cluster Center - Age Group: {age_group}",
            color=age_group_colors[age_group],
            tooltip="Click to view cluster",
            fill=True,
            fill_color=age_group_colors[age_group],
            opacity=1,
            className="leaflet-interactive"
        ).add_to(LA_map)
for age_group, centers in cluster_centers.items():
    points = cluster_points[age_group]
    for center, color in zip(centers, [age_group_colors[age_group]]*len(centers)):
        folium.CircleMarker(
            location=[center[0], center[1]],
            popup=f"Cluster Center - Age Group: {age_group}",
            color=age_group_colors[age_group],
            tooltip="Center of cluster",
            fill=True,
            fill_color=age_group_colors[age_group],
            opacity=1,
            className="leaflet-interactive"
        ).add_to(LA_map)
    for idx, point in enumerate(points):
        for _, row in point.iterrows():
            folium.CircleMarker(
                location=[row['LAT'], row['LON']],
                radius=3,
                color=age_group_colors[age_group],
                fill=True,
                fill_color=age_group_colors[age_group],
                opacity=0.6,
                tooltip=f"Age Group: {age_group}",
                className="leaflet-interactive"
            ).add_to(LA_map)

# JavaScript code for legend interaction
js_code = """
<script>
function toggleMarkers(cluster) {
    var markers = document.getElementsByClassName('leaflet-interactive');
    for (var i = 0; i < markers.length; i++) {
        if (markers[i].getAttribute('fill') === cluster) {
            markers[i].style.display = "initial";
        } else {
            markers[i].style.display = "none";
        }
    }
}
</script>
"""

# Onclick events to toggle markers
legend_html = f"""
<div style="position: fixed; 
             top: 10px; left: 0; width: 100%; height: auto; 
             z-index:9999; font-size:24px; text-align: center; color: #000000; background-color: #FFFFFF;
             " class="container-fluid">K-means Clustering of Homicides in LA by Age Group (June 2020 - November 2023)</div>
<div style="position: fixed; 
             bottom: 50px; left: 50px; width: 150px; height: auto; 
             border:2px solid grey; z-index:9999; font-size:14px; background-color: #FFFFFF; color: #000000;"
             class="container-fluid">&nbsp;Age groups (click to show datapoints): <br>
             &nbsp; <span onclick="toggleMarkers('red')" style="color: red;">0 - 29</span><br>
             &nbsp; <span onclick="toggleMarkers('green')" style="color: green;">30 - 39</span><br>
             &nbsp; <span onclick="toggleMarkers('blue')" style="color: blue;">40 - 49</span><br>
             &nbsp; <span onclick="toggleMarkers('black')" style="color: black;">50 - 59</span><br>
             &nbsp; <span onclick="toggleMarkers('brown')" style="color: brown;">60+</span><br>
</div>

"""

LA_map.get_root().html.add_child(folium.Element(f'<link href="{bootstrap_css}" rel="stylesheet">'))
LA_map.get_root().html.add_child(folium.Element(f'<script src="{bootstrap_js}"></script>'))

legend_html += js_code
LA_map.get_root().html.add_child(folium.Element(legend_html))

# Save the map to an HTML file
LA_map.save("cluster_map_with_legend_interactive.html")