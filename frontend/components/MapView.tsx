import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapViewProps {
  listings: any[];
}

const MapView: React.FC<MapViewProps> = ({ listings }) => {
  // Default center (Medellín, Colombia)
  const defaultCenter: [number, number] = [6.2442, -75.5812];

  // Calculate center based on listings
  const getCenter = (): [number, number] => {
    const validListings = listings.filter((l) => l.latitude && l.longitude);
    if (validListings.length === 0) return defaultCenter;

    const avgLat =
      validListings.reduce((sum, l) => sum + l.latitude, 0) /
      validListings.length;
    const avgLon =
      validListings.reduce((sum, l) => sum + l.longitude, 0) /
      validListings.length;

    return [avgLat, avgLon];
  };

  const center = getCenter();

  return (
    <MapContainer
      center={center}
      zoom={12}
      style={{ height: "500px", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {listings
        .filter((listing) => listing.latitude && listing.longitude)
        .map((listing) => (
          <Marker
            key={listing.id}
            position={[listing.latitude, listing.longitude]}
          >
            <Popup>
              <div>
                <h3>{listing.title}</h3>
                <p>
                  <strong>Price:</strong> $
                  {listing.price.toLocaleString("es-CO")} COP
                </p>
                {listing.year && (
                  <p>
                    <strong>Year:</strong> {listing.year}
                  </p>
                )}
                {listing.mileage && (
                  <p>
                    <strong>Mileage:</strong> {listing.mileage.toLocaleString()}{" "}
                    km
                  </p>
                )}
                <a href={listing.url} target="_blank" rel="noopener noreferrer">
                  View Listing
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
};

export default MapView;
