use clap::Parser;
use regex::Regex;
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};

/// Rust scraper for vendetunave.co — carros y camionetas section.
/// Outputs a JSON array of vehicle listings to stdout.
#[derive(Parser)]
#[command(name = "vendetunave-scraper", about = "Scraper for vendetunave.co vehicles")]
struct Args {
    /// Search query, e.g. "Toyota Corolla 2019"
    #[arg(short, long)]
    query: String,

    /// Maximum number of results to return (default: 20)
    #[arg(short, long, default_value_t = 20)]
    max_results: usize,
}

#[derive(Serialize, Deserialize, Debug)]
struct Listing {
    title: String,
    price: Option<String>,
    year: Option<u32>,
    mileage: Option<u32>,
    city: Option<String>,
    url: String,
    source: String,
}

fn main() {
    let args = Args::parse();

    match run(&args.query, args.max_results) {
        Ok(listings) => {
            println!("{}", serde_json::to_string(&listings).unwrap_or_else(|_| "[]".to_string()));
        }
        Err(e) => {
            eprintln!("Error: {e}");
            println!("[]");
        }
    }
}

fn run(query: &str, max_results: usize) -> Result<Vec<Listing>, Box<dyn std::error::Error>> {
    // vendetunave.co accepts the search term via the `search` query parameter on
    // the carros y camionetas category page.
    let encoded_query = url_encode(query);
    let url = format!(
        "https://www.vendetunave.co/vehiculos/carrosycamionetas?search={encoded_query}"
    );

    let client = reqwest::blocking::Client::builder()
        .user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
             AppleWebKit/537.36 (KHTML, like Gecko) \
             Chrome/120.0.0.0 Safari/537.36",
        )
        .timeout(std::time::Duration::from_secs(30))
        .build()?;

    let response = client
        .get(&url)
        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        .header("Accept-Language", "es-CO,es;q=0.9,en;q=0.8")
        .header("DNT", "1")
        .send()?;

    if !response.status().is_success() {
        eprintln!(
            "Warning: vendetunave.co returned HTTP {} for query: {}",
            response.status(),
            query
        );
        return Ok(vec![]);
    }

    let body = response.text()?;
    let listings = parse_listings(&body, max_results);
    Ok(listings)
}

/// Parse vehicle listings from the HTML page.
fn parse_listings(html: &str, max_results: usize) -> Vec<Listing> {
    let document = Html::parse_document(html);
    let mut listings: Vec<Listing> = Vec::new();

    // vendetunave.co renders each listing card as an <article> or a <div> with
    // a class that contains "card" or "vehicle".  We try a broad selector and
    // then narrow down inside each matched element.
    let card_selectors = [
        "article.vehiculo-card",
        "article.vehicle-card",
        "div.vehiculo-card",
        "div.vehicle-card",
        "div.card-vehicle",
        "div[class*='listing']",
        "article",
    ];

    let card_selector = card_selectors
        .iter()
        .find_map(|s| Selector::parse(s).ok().filter(|sel| document.select(sel).next().is_some()))
        .unwrap_or_else(|| Selector::parse("article").unwrap());

    for card in document.select(&card_selector).take(max_results) {
        let title = extract_text_by_selectors(
            &card,
            &["h2", "h3", "[class*='title']", "[class*='titulo']", "a"],
        );

        if title.is_empty() {
            continue;
        }

        let price_raw = extract_text_by_selectors(
            &card,
            &["[class*='price']", "[class*='precio']", "[data-price]"],
        );
        let price = if price_raw.is_empty() { None } else { Some(price_raw) };

        let card_text = card.text().collect::<String>();
        let year = extract_year(&card_text);
        let mileage = extract_mileage(&card_text);

        let city_raw = extract_text_by_selectors(
            &card,
            &["[class*='city']", "[class*='ciudad']", "[class*='location']", "[class*='ubicacion']"],
        );
        let city = if city_raw.is_empty() { None } else { Some(city_raw) };

        // Try to find the listing URL from any <a> element inside the card
        let url = extract_link(&card);

        listings.push(Listing {
            title,
            price,
            year,
            mileage,
            city,
            url,
            source: "VendeTuNave".to_string(),
        });
    }

    listings
}

/// Extract the inner text of the first element matching any of the given CSS selectors.
fn extract_text_by_selectors(
    element: &scraper::ElementRef,
    selectors: &[&str],
) -> String {
    for sel_str in selectors {
        if let Ok(sel) = Selector::parse(sel_str) {
            if let Some(found) = element.select(&sel).next() {
                let text = found.text().collect::<String>().trim().to_string();
                if !text.is_empty() {
                    return text;
                }
            }
        }
    }
    String::new()
}

/// Extract the href of the first <a> inside an element, making it absolute.
fn extract_link(element: &scraper::ElementRef) -> String {
    if let Ok(a_sel) = Selector::parse("a[href]") {
        if let Some(a) = element.select(&a_sel).next() {
            if let Some(href) = a.value().attr("href") {
                if href.starts_with("http") {
                    return href.to_string();
                }
                return format!("https://www.vendetunave.co{href}");
            }
        }
    }
    String::new()
}

/// Extract a four-digit year (1980–2030) from free text.
fn extract_year(text: &str) -> Option<u32> {
    let re = Regex::new(r"\b(19[89][0-9]|20[0-2][0-9]|2030)\b").ok()?;
    re.find(text)?.as_str().parse().ok()
}

/// Extract a mileage value (number followed by "km") from free text.
fn extract_mileage(text: &str) -> Option<u32> {
    let re = Regex::new(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*[Kk][Mm]").ok()?;
    let cap = re.captures(text)?;
    let raw = cap[1].replace(['.', ','], "");
    raw.parse().ok()
}

/// Percent-encode a query string for use in a URL.
fn url_encode(s: &str) -> String {
    s.chars()
        .flat_map(|c| match c {
            'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' => {
                vec![c]
            }
            ' ' => vec!['+'],
            other => {
                let mut buf = [0u8; 4];
                let bytes = other.encode_utf8(&mut buf);
                bytes
                    .bytes()
                    .flat_map(|b| {
                        let hi = char::from_digit((b >> 4) as u32, 16)
                            .unwrap_or('0')
                            .to_ascii_uppercase();
                        let lo = char::from_digit((b & 0x0f) as u32, 16)
                            .unwrap_or('0')
                            .to_ascii_uppercase();
                        vec!['%', hi, lo]
                    })
                    .collect()
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_year() {
        assert_eq!(extract_year("Toyota Corolla 2019 automático"), Some(2019));
        assert_eq!(extract_year("Modelo 1985"), Some(1985));
        assert_eq!(extract_year("Sin año"), None);
    }

    #[test]
    fn test_extract_mileage() {
        assert_eq!(extract_mileage("45.000 km recorridos"), Some(45000));
        assert_eq!(extract_mileage("120000km"), Some(120000));
        assert_eq!(extract_mileage("Sin km"), None);
    }

    #[test]
    fn test_url_encode() {
        assert_eq!(url_encode("Toyota Corolla"), "Toyota+Corolla");
        assert_eq!(url_encode("hello world"), "hello+world");
    }

    #[test]
    fn test_parse_listings_empty_html() {
        let listings = parse_listings("<html><body></body></html>", 20);
        assert!(listings.is_empty());
    }

    #[test]
    fn test_parse_listings_with_article() {
        let html = r#"
            <html><body>
                <article>
                    <h2>Toyota Corolla 2020</h2>
                    <span class="price">$45.000.000</span>
                    <span class="city">Medellín</span>
                    <a href="/vehiculos/toyota-corolla-2020">Ver más</a>
                    <p>35.000 km recorridos</p>
                </article>
            </body></html>
        "#;
        let listings = parse_listings(html, 20);
        assert_eq!(listings.len(), 1);
        assert_eq!(listings[0].title, "Toyota Corolla 2020");
        assert_eq!(listings[0].year, Some(2020));
        assert_eq!(listings[0].mileage, Some(35000));
        assert_eq!(listings[0].source, "VendeTuNave");
    }
}
