import os
import agentql
from playwright.sync_api import sync_playwright
from pyairtable import Api
from dotenv import load_dotenv

# load enviroment variables from env files
load_dotenv()

# get username and password from enviroment variables
EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')
os.environ['AGENTQL_API_KEY'] = os.getenv('AGENTQL_API_KEY')

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

def login():
    #page.wait_for_page_ready_state()
    browser.contexts[0].storage_state(path="idealist_login.json")

URL =  "https://www.idealist.org/jobs"

JOB_POSTS_QUERY = """
{
    job_posts[] {
        org_name
        job_title
        salary
        location
        contract_type(Contract full time)
        location_type(remote or onsite or hybrid)
        date_posted

    } 
}
"""

PAGINATION_QUERY = """
{
    pagination {
        next_page_btn
    }
}
"""

def push_to_airtable(job_posts_data):
    airtable = Api(AIRTABLE_API_KEY)
    table = airtable.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

    # push data to airtable
    for job in job_posts_data:
        table.create(job)

    print(f"{len(job_posts_data)} records pushed to airtable")

def main():
    with sync_playwright() as playwright, playwright.chromium.launch(headless=False) as browser:
        if not os.path.exists("idealist_login.json"):
            print("no login state found, loggin in...")
            login()

        context = browser.new_context(storage_state= "idealist_login.json")
        page = agentql.wrap(context.new_page())

        page.goto(URL)

        # use query_data() method to fetch the data from the page
        status = True

        while status:
            current_url = page.url
            
            job_posts_response = page.query_elements(JOB_POSTS_QUERY)
            job_posts = job_posts_response.job_posts
            job_posts_data = job_posts.to_data()

            print(f"Total number of job posts: {len(job_posts_data)}")
            print(job_posts_data)
            push_to_airtable(job_posts_data)

            # write job posts data to csv
            paginations = page.query_elements(PAGINATION_QUERY)
            next_page_btn = paginations.pagination.next_page_btn

            next_page_btn.click()

            # wait for page to settle
            page.wait_for_page_ready_state()

            if current_url == page.url:
                status = False
            

        page.close()

if __name__ == "__main__":
    main()