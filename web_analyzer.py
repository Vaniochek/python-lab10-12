import csv
import json
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt


class WebScraper:
    # Клас для завантаження вебсторінок та вилучення структурованих даних.

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def fetch_page(self, page_num: int) -> BeautifulSoup | None:
        # Отримує HTML-код сторінки та повертає об'єкт BeautifulSoup.
        url = self.base_url.format(page_num)
        try:
            print(f"[INFO] Завантаження сторінки №{page_num}: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.ConnectionError:
            print(f"[ПОМИЛКА] Відсутнє підключення до мережі при запиті до {url}")
        except requests.exceptions.Timeout:
            print(f"[ПОМИЛКА] Перевищено час очікування відповіді від {url}")
        except requests.exceptions.HTTPError as err:
            print(f"[ПОМИЛКА HTTP] Сервер повернув помилку: {err}")
        except Exception as err:
            print(f"[НЕВІДОМА ПОМИЛКА] {err}")
        return None

    def parse_quotes(self, pages_count: int) -> list[dict]:
        # Виконує парсинг та очищення цитат із заданої кількості сторінок.
        collected_data = []

        for page in range(1, pages_count + 1):
            soup = self.fetch_page(page)
            if not soup:
                continue

            quote_blocks = soup.find_all("div", class_="quote")
            for block in quote_blocks:
                # Витягуємо та очищаємо текст від декоративних лапок
                raw_text = block.find("span", class_="text").get_text(strip=True)
                clean_text = raw_text.strip("“”\"")

                author = block.find("small", class_="author").get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in block.find_all("a", class_="tag")]

                collected_data.append({
                    "Page": page,
                    "Author": author,
                    "Quote": clean_text,
                    "Tags": ", ".join(tags),
                    "Tags_Count": len(tags)
                })

        return collected_data


class DataProcessor:
    # Клас для статистичного аналізу, візуалізації та збереження результатів.

    def __init__(self, data: list[dict], output_dir: str):
        self.data = data
        self.output_dir = output_dir

    def save_csv(self, filename: str = "parsed_quotes.csv") -> None:
        # Зберігає зібрані дані у формат CSV.
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=self.data[0].keys())
                writer.writeheader()
                writer.writerows(self.data)
            print(f"[УСПІХ] Дані збережено у CSV: {filepath}")
        except PermissionError:
            print(f"[ПОМИЛКА] Закрийте файл '{filename}', доступ заблоковано.")
        except Exception as err:
            print(f"[ПОМИЛКА CSV] {err}")

    def save_json(self, filename: str = "parsed_quotes.json") -> None:
        # Зберігає зібрані дані у формат JSON.
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, mode="w", encoding="utf-8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)
            print(f"[УСПІХ] Дані збережено у JSON: {filepath}")
        except Exception as err:
            print(f"[ПОМИЛКА JSON] {err}")

    def analyze_and_visualize(self, chart_filename: str = "top_authors.png") -> None:
        # Виконує статистичний аналіз через pandas та будує діаграму matplotlib.
        df = pd.DataFrame(self.data)

        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТИ АНАЛІЗУ ЗІБРАНИХ ДАНИХ (PANDAS)")
        print("=" * 60)
        print(f"Усього зібрано записів     : {len(df)}")
        print(f"Унікальних авторів         : {df['Author'].nunique()}")
        print(f"Середня кількість тегів    : {df['Tags_Count'].mean():.2f}")

        # Групування за авторами та визначення ТОП-5
        top_authors = df["Author"].value_counts().head(5)
        print("\n--- ТОП-5 авторів за кількістю цитат ---")
        print(top_authors.to_string())

        # Побудова та збереження стовпчастої діаграми
        chart_path = os.path.join(self.output_dir, chart_filename)
        plt.figure(figsize=(9, 5))
        bars = plt.bar(top_authors.index, top_authors.values, color="#2E86C1", edgecolor="black", width=0.55)

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontweight="bold"
            )

        plt.title("ТОП-5 авторів за кількістю цитат на сторінках", fontsize=13, fontweight="bold")
        plt.xlabel("Автор", fontsize=11)
        plt.ylabel("Кількість цитат", fontsize=11)
        plt.xticks(rotation=15)
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150)
        print(f"\n[УСПІХ] Діаграму збережено у графічний файл: {chart_path}")
        plt.show()


def get_pages_count() -> int:
    # Запитує у користувача кількість сторінок із перевіркою коректності вводу.
    while True:
        user_input = input("Введіть кількість сторінок для парсингу (від 1 до 5): ").strip()
        try:
            pages = int(user_input)
            if 1 <= pages <= 5:
                return pages
            print("[ПОПЕРЕДЖЕННЯ] Будь ласка, введіть число в межах від 1 до 5.")
        except ValueError:
            print("[ПОМИЛКА] Некоректне значення! Потрібно ввести ціле число.")


def main():
    print("=" * 60)
    print("  СИСТЕМА ЗБОРУ ТА АНАЛІЗУ ВЕБ-ДАНИХ (ВАРІАНТ 1)")
    print("=" * 60)

    pages_limit = get_pages_count()
    base_url = "https://quotes.toscrape.com/page/{}/"

    scraper = WebScraper(base_url)
    all_quotes = scraper.parse_quotes(pages_limit)

    if not all_quotes:
        print("[ПОМИЛКА] Не вдалося зібрати дані. Роботу програми завершено.")
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    processor = DataProcessor(all_quotes, current_dir)

    processor.analyze_and_visualize()
    processor.save_csv()
    processor.save_json()
    print("=" * 60)


if __name__ == "__main__":
    main()