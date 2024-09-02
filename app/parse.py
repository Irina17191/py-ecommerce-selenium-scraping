import csv
from dataclasses import dataclass, fields, astuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementClickInterceptedException,
    NoSuchElementException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from app.urls import URLS_FIELDS


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None

def get_driver() -> WebDriver:
    return _driver

def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description")
        .text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span.ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def get_all_products(url: str = "", driver: WebDriver = None) -> list[Product]:
    if driver is None:
        driver = get_driver()  # Use the global driver if not provided
    if driver is None:
        raise RuntimeError("No WebDriver instance is available.")

    driver.get(url)

    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            more_button.click()
        except (NoSuchElementException, ElementClickInterceptedException):
            break

    products = BeautifulSoup(
        driver.page_source,
        "html.parser").select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def parse_urls(driver: WebDriver, urls: dict) -> dict:
    all_products = {}
    for url, filename in urls.items():
        all_products[filename] = get_all_products(url, driver)
    return all_products


def save_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        products_by_file = parse_urls(driver=new_driver, urls=URLS_FIELDS)

        for filename, products in products_by_file.items():
            save_to_csv(products, filename)


if __name__ == "__main__":
    main()
