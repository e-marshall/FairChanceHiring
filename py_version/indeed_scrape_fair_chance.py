from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import itertools
import pandas as pd
import numpy as np
import geopandas as gpd
from bs4 import BeautifulSoup

def indeed_scrape(loc: str, industry: str, fair_chance: bool) -> pd.DataFrame:
    """
    Scrapes job data from Indeed.com for a single state, sector, and either all jobs or only jobs listed as fair chance.

    Args:
        loc (str): The location (state) to search for jobs.
        industry (str): The industry/sector to search for jobs.
        fair_chance (bool): Whether to search for fair chance jobs only.

    Returns:
        pd.DataFrame: A DataFrame containing the job count and other metadata for the specified location and industry.
    """

    # Initialize a new Firefox webdriver instance
    driver = webdriver.Firefox()

    # Construct the URL for the job query, specifying location and sector
    url = f"https://www.indeed.com/jobs?q={industry}&l={loc}"

    # Add additional search criteria for fair chance jobs if specified
    if fair_chance:
        url += 'sc=0kf%3Aattr(Q5R8A)%3B&vjk=b0eb0c11d40f958b' #should make sure this isn't missing any jobs
        fair_chance_flag = 'Yes'
    else:
        fair_chance_flag = 'No'

    # Navigate to the constructed URL
    driver.get(url)

    # Wait for up to 20 seconds for the page to load
    wait = WebDriverWait(driver, 20)

    # Extract the job count element from the page
    job_count_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobsearch-JobCountAndSortPane-jobCount")))

    # Extract the text from the job count element and use regex to extract the number
    job_count_text = job_count_elem.text
    job_count = re.search(r'(\d+,?\d*)', job_count_text)

    # Look for a more precise count in the page source
    page_source = driver.page_source
    
    #the following lines handle job count
    match = re.search(r'"totalJobCount":(\d+)', page_source)
    if match:
        # Extract the precise job count from the page source
        num_jobs = match.group(1)
    else:
        # If no precise count is found, use the initial job count
        num_jobs = job_count.group(0).replace(',', '')

    # Create a dictionary to store the metadata
    d = {
        'state': loc, 
        'sector': industry,
        'job_count': num_jobs,
        'fair_chance_bool': fair_chance_flag
    }

    # Create a DataFrame from the metadata dictionary
    df = pd.DataFrame(d, index=[0])

    # Quit the webdriver instance
    driver.quit()

    # Return the DataFrame
    return df, full_job_info_df

def run_scrape():
    '''Runs indeed_scrape on permutations of industries, states, fair_chance. Returns combined dataframe of all counts
    '''
    industries = ["retail", "food service", "construction", "waste management", "home health"]
    states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
              "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
              "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
              "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
              "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
              "New Hampshire", "New Jersey", "New Mexico", "New York",
              "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
              "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
              "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
              "West Virginia", "Wisconsin", "Wyoming"]
    fair_chance = [True, False]
    df_ls = []
    
    permutations = list(itertools.product(industries, states, fair_chance))
    
    for permutation in permutations:
        try:
            df = indeed_scrape(permutation[1], permutation[0], permutation[2])[0]

            df_ls.append(df)
            
        except Exception as e:
            print(f"Error with permutation {permutation}: {e}")
    
    if df_ls:
        full_df = pd.concat(df_ls)
        
    else:
        full_df = pd.DataFrame()  # Return an empty DataFrame if no data was collected
    return full_df