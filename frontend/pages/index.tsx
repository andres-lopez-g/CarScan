import React, { useState } from "react";
import Head from "next/head";
import dynamic from "next/dynamic";
import styles from "../styles/Home.module.css";
import {
  CarIcon,
  BuildingIcon,
  BoltIcon,
  SearchIcon,
  MapPinIcon,
  LayersIcon,
  CalendarIcon,
  RoadIcon,
  GlobeIcon,
  RulerIcon,
  ArrowRightIcon,
} from "../components/Icons";

// Dynamically import Map component (client-side only)
const MapView = dynamic(() => import("../components/MapView"), {
  ssr: false,
});

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState("vehicles");
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [nationwide, setNationwide] = useState(false);

  const runSearch = async (nationwide: boolean) => {
    setLoading(true);
    setError("");
    setListings([]);

    // When nationwide=false we do a "local" search (no city filter, but could
    // include user_lat/user_lon in the future). When nationwide=true we
    // explicitly omit city so the backend doesn't filter by location.
    const body: any = {
      query: searchQuery,
      search_type: searchType,
      max_distance_km: nationwide ? 5000 : 50,
    };

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/vehicles/search`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );

      if (!response.ok) throw new Error("Search failed");

      const data = await response.json();
      setListings(data.listings || []);
    } catch (err) {
      setError("Error al buscar. Por favor intenta de nuevo.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setNationwide(false);
    setHasSearched(true);
    await runSearch(false);
  };

  const handleNationwide = async () => {
    setNationwide(true);
    await runSearch(true);
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>CarScan — Encuentra los mejores vehículos en Colombia</title>
        <meta
          name="description"
          content="Busca y compara vehículos y propiedades en los principales marketplaces colombianos"
        />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </Head>

      {/* Navbar */}
      <nav className={styles.navbar}>
        <div className={styles.navLogo}>
          <span className={styles.navLogoIcon}>◈</span>
          Car<span className={styles.navLogoAccent}>Scan</span>
        </div>
        <div className={styles.navLinks}>
          <a href="#search" className={styles.navLink}>Buscar</a>
          <a href="#features" className={styles.navLink}>Características</a>
          <a
            href="https://github.com/andres-lopez-g/CarScan"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.navLink}
          >
            GitHub
          </a>
        </div>
      </nav>

      <main className={styles.main}>
        {/* Hero */}
        <section className={styles.heroSection} id="search">
          <span className={styles.badge}>
            <BoltIcon size={14} /> Búsqueda en tiempo real
          </span>

          <h1 className={styles.title}>
            {searchType === "vehicles" ? "Encuentra tu próximo" : "Encuentra tu próxima"}
            <br />
            <span className={styles.brand}>
              {searchType === "vehicles" ? "vehículo ideal" : "propiedad ideal"}
            </span>
          </h1>

          <p className={styles.description}>
            {searchType === "vehicles"
              ? "Busca y compara vehículos en los principales marketplaces de Colombia. Todo en un solo lugar."
              : "Explora bodegas, locales y propiedades comerciales en Colombia. Sin complicaciones."}
          </p>

          {/* Type toggle */}
          <div className={styles.searchTypeSelector}>
            <button
              type="button"
              className={`${styles.typeButton} ${searchType === "vehicles" ? styles.typeButtonActive : ""}`}
              onClick={() => setSearchType("vehicles")}
            >
              <CarIcon size={16} /> Vehículos
            </button>
            <button
              type="button"
              className={`${styles.typeButton} ${searchType === "properties" ? styles.typeButtonActive : ""}`}
              onClick={() => setSearchType("properties")}
            >
              <BuildingIcon size={16} /> Propiedades
            </button>
          </div>

          {/* Search form */}
          <form onSubmit={handleSearch} className={styles.searchForm}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                searchType === "vehicles"
                  ? "Buscar vehículos (ej: Toyota Corolla 2015)"
                  : "Buscar propiedades (ej: bodega Medellín)"
              }
              className={styles.searchInput}
              required
            />
            <button type="submit" className={styles.searchButton} disabled={loading}>
              {loading ? "Buscando..." : "Buscar"}
            </button>
          </form>
        </section>

        {/* Loading */}
        {loading && (
          <div className={styles.loadingContainer}>
            <div className={styles.spinner} />
            <p className={styles.loadingText}>
              {nationwide
                ? "Buscando en toda Colombia..."
                : "Buscando en todos los marketplaces..."}
            </p>
          </div>
        )}

        {/* Error */}
        {error && <p className={styles.error}>{error}</p>}

        {/* Results */}
        {listings.length > 0 && (
          <div className={styles.results}>
            <div className={styles.resultsHeader}>
              <h2>
                Resultados{" "}
                {nationwide && (
                  <span className={styles.nationwideBadge}>
                    <GlobeIcon size={13} /> Toda Colombia
                  </span>
                )}
              </h2>
              <span className={styles.resultsCount}>
                {listings.length} anuncios encontrados
              </span>
            </div>

            <div className={styles.mapContainer}>
              <MapView listings={listings} />
            </div>

            <div className={styles.listContainer}>
              {listings.map((listing: any) => (
                <div key={listing.id} className={styles.listingCard}>
                  <h3>{listing.title}</h3>
                  <p className={styles.price}>
                    ${listing.price.toLocaleString("es-CO")} COP
                  </p>
                  <div className={styles.details}>
                    {listing.year && (
                      <span className={styles.detailTag}>
                        <CalendarIcon size={13} /> {listing.year}
                      </span>
                    )}
                    {listing.mileage && (
                      <span className={styles.detailTag}>
                        <RoadIcon size={13} /> {listing.mileage.toLocaleString()} km
                      </span>
                    )}
                    {listing.city && (
                      <span className={styles.detailTag}>
                        <MapPinIcon size={13} /> {listing.city}
                      </span>
                    )}
                    {listing.source && (
                      <span className={styles.detailTag}>
                        <GlobeIcon size={13} /> {listing.source}
                      </span>
                    )}
                  </div>
                  {listing.distance_km && (
                    <p className={styles.distance}>
                      <RulerIcon size={14} /> {listing.distance_km.toFixed(1)} km de distancia
                    </p>
                  )}
                  <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.viewButton}
                  >
                    Ver anuncio <ArrowRightIcon size={14} />
                  </a>
                </div>
              ))}
            </div>

            {/* "Expand to all Colombia" — shown below results when NOT already nationwide */}
            {!nationwide && !loading && (
              <div className={styles.expandSection}>
                <p className={styles.expandHint}>
                  ¿No encontraste lo que buscabas? Amplía la búsqueda a todo el país.
                </p>
                <button
                  type="button"
                  className={styles.expandButton}
                  onClick={handleNationwide}
                  disabled={loading}
                >
                  <GlobeIcon size={16} />
                  Ver ofertas en toda Colombia
                </button>
              </div>
            )}
          </div>
        )}

        {/* Show expand button when 0 results after a search */}
        {listings.length === 0 && !loading && hasSearched && !nationwide && (
          <div className={styles.expandSection}>
            <p className={styles.expandHint}>
              No se encontraron resultados locales. ¿Buscamos en toda Colombia?
            </p>
            <button
              type="button"
              className={styles.expandButton}
              onClick={handleNationwide}
              disabled={loading}
            >
              <GlobeIcon size={16} />
              Buscar en toda Colombia
            </button>
          </div>
        )}

        {/* Features section — only shown before the first search */}
        {!hasSearched && !loading && (
          <section className={styles.featuresSection} id="features">
            <div className={styles.featureCard}>
              <span className={styles.featureIcon}>
                <SearchIcon size={22} />
              </span>
              <h3 className={styles.featureTitle}>Búsqueda unificada</h3>
              <p className={styles.featureDesc}>
                Compara precios de TuCarro, MercadoLibre, VendeTuNave y más en una sola búsqueda.
              </p>
            </div>
            <div className={styles.featureCard}>
              <span className={styles.featureIcon}>
                <MapPinIcon size={22} />
              </span>
              <h3 className={styles.featureTitle}>Mapa interactivo</h3>
              <p className={styles.featureDesc}>
                Visualiza los listados geolocalizados cerca de ti en un mapa interactivo en tiempo real.
              </p>
            </div>
            <div className={styles.featureCard}>
              <span className={styles.featureIcon}>
                <LayersIcon size={22} />
              </span>
              <h3 className={styles.featureTitle}>Resultados al instante</h3>
              <p className={styles.featureDesc}>
                Scraping en tiempo real de múltiples fuentes para que siempre tengas los datos más frescos.
              </p>
            </div>
          </section>
        )}
      </main>

      <footer className={styles.footer}>
        <p>
          <span className={styles.footerAccent}>CarScan</span> © 2024 —
          Agregador de listados para Colombia
        </p>
      </footer>
    </div>
  );
}
