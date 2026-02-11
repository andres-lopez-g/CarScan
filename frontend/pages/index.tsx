import React, { useState } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import styles from '../styles/Home.module.css';

// Dynamically import Map component (client-side only)
const MapView = dynamic(() => import('../components/MapView'), {
  ssr: false,
});

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/vehicles/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: searchQuery,
            max_distance_km: 50,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setListings(data.listings || []);
    } catch (err) {
      setError('Error searching vehicles. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>CarScan - Vehicle Listing Aggregator</title>
        <meta name="description" content="Find the best vehicle deals in Colombia" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to <span className={styles.brand}>CarScan</span>
        </h1>

        <p className={styles.description}>
          Find the best vehicle deals across Colombian marketplaces
        </p>

        <form onSubmit={handleSearch} className={styles.searchForm}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for vehicles (e.g., Toyota Corolla 2015)"
            className={styles.searchInput}
            required
          />
          <button 
            type="submit" 
            className={styles.searchButton}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {error && <p className={styles.error}>{error}</p>}

        {listings.length > 0 && (
          <div className={styles.results}>
            <h2>Found {listings.length} listings</h2>
            
            <div className={styles.mapContainer}>
              <MapView listings={listings} />
            </div>

            <div className={styles.listContainer}>
              {listings.map((listing: any) => (
                <div key={listing.id} className={styles.listingCard}>
                  <h3>{listing.title}</h3>
                  <p className={styles.price}>
                    ${listing.price.toLocaleString('es-CO')} COP
                  </p>
                  <div className={styles.details}>
                    {listing.year && <span>Year: {listing.year}</span>}
                    {listing.mileage && <span>Mileage: {listing.mileage.toLocaleString()} km</span>}
                    {listing.city && <span>City: {listing.city}</span>}
                    {listing.source && <span>Source: {listing.source}</span>}
                  </div>
                  {listing.distance_km && (
                    <p className={styles.distance}>
                      Distance: {listing.distance_km.toFixed(1)} km
                    </p>
                  )}
                  <a 
                    href={listing.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className={styles.viewButton}
                  >
                    View Original Listing
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className={styles.footer}>
        <p>CarScan © 2024 - Vehicle Listing Aggregator for Colombia</p>
      </footer>
    </div>
  );
}
