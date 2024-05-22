from datetime import datetime, timedelta
import pandas as pd
import os
import csv
import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph
import json
import validators
from dotenv import load_dotenv

class ScraperCache:
    def __init__(self):
        if 'cache' not in st.session_state:
            st.session_state.cache = {}

    def is_recently_scraped(self, url):
        if url in st.session_state.cache:
            last_scraped_time = datetime.strptime(st.session_state.cache[url], "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - last_scraped_time) < timedelta(days=1)
        return False

    def update_cache(self, url):
        st.session_state.cache[url] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DataHandler:
    @staticmethod
    def load_parsed_data(file_path="parsed_data.csv"):
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
        else:
            df = pd.DataFrame(columns=["Context"])
        return df

    @staticmethod
    def save_parsed_data(data, file_path="parsed_data.csv"):
        df = pd.DataFrame(data, columns=["Context"])
        df.to_csv(file_path, index=False)


class WebScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = ScraperCache()

    def scrape(self, prompt, url):
        # if self.cache.is_recently_scraped(url):
        #     st.warning("This page was scraped within the last 24 hours. Skipping scraping.")
        #     return

        scraper_config = {
            "llm": {
                "api_key": self.api_key,
                "model": "gpt-3.5-turbo",
                "temperature": 0,
            },
            "verbose": True,
            "headless": False
        }

        search_result = SmartScraperGraph(
            prompt=prompt,
            source=url,
            config=scraper_config
        )

        result = search_result.run()

        print("Result of scraping:", result)
        
        if 'context' not in result or not result['context']:
            raise ValueError("No context found in the result. Please check the URL and prompt.")

        output = json.dumps(result, indent=2)
        print("Prettified JSON output:", output)

        DataHandler.save_parsed_data(result['context'])
        self.cache.update_cache(url)


class ScraperApp:
    def __init__(self, api_key):
        self.scraper = WebScraper(api_key)
        self.init_session_variables()

    def init_session_variables(self):
        if 'scraping' not in st.session_state:
            st.session_state.scraping = False

    def display_data(self):
        df = DataHandler.load_parsed_data()
        st.dataframe(df)

    def run(self):
        st.title("Website Scraper")
        default_url = "https://ezsnapcovers.com/"
        default_prompt = "fetch content relevant to Frequently asked questions from the page"
        
        url = st.text_input("Enter website URL", value=default_url)
        prompt = st.text_area("What data do you want to scrape?", value=default_prompt)
        prompt += "All the data you fetch should be text context no url no images no nested data just raw text and text data should store in one column named 'context'."

        start_button = st.button("Start")
        # start_button = st.button("Start" if not st.session_state.scraping else "Continue")
        # pause_button = st.button("Pause")
        load_button = st.button("Check Data")

        if start_button:
            st.session_state.scraping = True
            try:
                self.scraper.scrape(prompt, url)
            except ValueError as e:
                st.error(f"Scraping failed: {e}")
            # if is_valid_domain(url):
            #     try:
            #         self.scraper.scrape(prompt, url)
            #     except ValueError as e:
            #         st.error(f"Scraping failed: {e}")
            # else:
            #     st.error("Invalid domain. Please enter a valid website URL.")

        # if pause_button:
        #     st.session_state.scraping = False

        if load_button:
            self.display_data()


def is_valid_domain(url):
    return validators.domain(url)


if __name__ == "__main__":
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    app = ScraperApp(openai_key)
    app.run()

