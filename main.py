import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Initialize Selenium WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Scrape reviews from a TripAdvisor hotel page
def scrape_tripadvisor_reviews(url, max_reviews=100):
    driver = init_driver()
    reviews_data = []
    reviews_per_page = 10
    max_pages = (max_reviews + reviews_per_page - 1) // reviews_per_page  # Ceiling division

    try:
        # Navigate to the URL
        driver.get(url)
        time.sleep(10)  # Wait for page to load

        # Accept cookies if present
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            time.sleep(5)
        except TimeoutException:
            print("No cookie popup found, proceeding...")

        # Loop through pages
        for page in range(max_pages):
            print(f"Scraping page {page + 1}...")
            time.sleep(3)  # Wait for page content to load

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_cards = soup.find_all("div", {"data-automation": "reviewCard"})

            # Extract reviews from the current page
            for review in review_cards:
                try:
                    # Click "Read more" if present
                    try:
                        more_button = driver.find_element(By.XPATH, ".//span[contains(@class, 'Ignyf _S Z')]")
                        driver.execute_script("arguments[0].click();", more_button)
                        time.sleep(1)
                    except NoSuchElementException:
                        pass

                    # Re-parse the page after clicking "Read more"
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    review_cards = soup.find_all("div", {"data-automation": "reviewCard"})

                    # Extract review details
                    title = review.find("a", class_="QewHA H4 _a").text.strip() if review.find("a", class_="QewHA H4 _a") else "N/A"
                    body = review.find("q", class_="QewHA H4 _a").span.text.strip() if review.find("q", class_="QewHA H4 _a") else "N/A"
                    rating = review.find("svg", class_="UctUV d H0")["aria-label"].split()[0] if review.find("svg", class_="UctUV d H0") else "N/A"
                    date = review.find("span", class_="_34Xs-BQm").text.strip() if review.find("span", class_="_34Xs-BQm") else "N/A"

                    reviews_data.append({
                        "title": title,
                        "body": body,
                        "rating": rating,
                        "date": date
                    })

                    # Stop if we have enough reviews
                    if len(reviews_data) >= max_reviews:
                        break
                except Exception as e:
                    print(f"Error extracting review: {e}")
                    continue

            # Stop if we have enough reviews
            if len(reviews_data) >= max_reviews:
                break

            # Navigate to the next page
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ui_button.nav.next.primary"))
                )
                driver.execute_script("arguments[0].click();", next_button)
            except TimeoutException:
                print("No more pages to scrape or next button not found.")
                break

    finally:
        driver.quit()

    return reviews_data[:max_reviews]

# Save reviews to a CSV file
def save_to_csv(reviews, filename="tripadvisor_reviews.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "body", "rating", "date"])
        writer.writeheader()
        for review in reviews:
            writer.writerow(review)

# Main execution
if __name__ == "__main__":
    # Example TripAdvisor hotel URL
    url = "https://www.tripadvisor.com/Attraction_Review-g317067-d472320-Reviews-Hell_s_Gate_National_Park-Naivasha_Rift_Valley_Province.html"
    reviews = scrape_tripadvisor_reviews(url, max_reviews=100)
    print(f"Scraped {len(reviews)} reviews.")
    save_to_csv(reviews)
    print(f"Reviews saved to tripadvisor_reviews.csv")