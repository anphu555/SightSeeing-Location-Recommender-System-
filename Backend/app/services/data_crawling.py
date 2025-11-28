import asyncio
from playwright.async_api import async_playwright
import pandas as pd

# CONFIGURATION
BASE_URL = "https://csdl.vietnamtourism.gov.vn/dest/"
# DATA_TYPE = 2  # 2 likely maps to Accommodations/Hotels based on search results
START_PAGE = 1
MAX_PAGES = 2  # Set to a higher number to crawl more

async def scrape_tourism_data():
    async with async_playwright() as p:
        # Launch browser (headless=True is faster)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        all_data = []

        for current_page in range(START_PAGE, START_PAGE + MAX_PAGES):
            print(f"Crawling page {current_page}...")
            
            # Construct the URL with pagination
            # target_url = f"{BASE_URL}?datatype={DATA_TYPE}&page={current_page}"
            target_url = f"{BASE_URL}?item={current_page}"
            
            try:
                # Go to page and wait for the list to load
                await page.goto(target_url, timeout=60000)


                data_container_selector = "verticleilist listing-shot"
                await page.wait_for_selector(data_container_selector)

                
                # Wait for a specific element that contains data (adjust selector based on actual site)
                # This generic wait ensures content is loaded
                await page.wait_for_load_state("networkidle")

                # Extract listing items (You need to inspect the site to get the exact CSS class)
                # Assuming standard list items based on site structure
                listings = await page.locator('.listing-item, .item, .row').all() 
                
                if not listings:
                    print("No more listings found. Stopping.")
                    break

                for item in listings:
                    # Extract text from the item
                    text_content = await item.inner_text()
                    
                    # Simple parsing (refine this with specific selectors like .title, .address)
                    entry = {
                        "raw_text": text_content.replace("\n", " | ")
                        # "source_url": target_url
                    }
                    all_data.append(entry)
                    
            except Exception as e:
                print(f"Error on page {current_page}: {e}")

        await browser.close()
        
        # Save to Excel/CSV
        df = pd.DataFrame(all_data)
        df.to_csv("vietnam_tourism_data.csv", index=False)
        print(f"Done! Scraped {len(all_data)} items.")


async def crawl_title_info_wrapper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://csdl.vietnamtourism.gov.vn/dest/?item=1")


        # Where the title, address... is contained
        await page.wait_for_selector(".cslt-detail")

        # The title is on the first .cslt-detail css class
        items = page.locator(".cslt-detail").first

        # Count the number of items which page.locator gives out
        count = await items.count()     # == 1 because locate only the first item 

        # print(f"{count}")

        # Loop through all items
        for i in range(count):
            item = items.nth(i)
            
            try:
                # Extract title
                title_element = item.locator(".header h4")

                title_text = await title_element.inner_text()
                print(f"Title: {title_text.strip()}")


                # Extract other info
                other_info = item.locator("span")
                
                other_info_count = await other_info.count()

                for j in range(other_info_count):
                    other_info_iterator = other_info.nth(j)
                
                    address_element = await other_info_iterator.inner_text()
                    print(f"{address_element.strip()}")

                
            except Exception as e:
                print(f"Error on item {i+1}: {e}")


        await browser.close()

async def crawl_content_info_wrapper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://csdl.vietnamtourism.gov.vn/dest/?item=1")


        # load page in the specific class
        await page.wait_for_selector(".content-detail")

        # locate to all class name .content-detail
        items = page.locator(".content-detail")

        # Count the number of class named .content-detail
        count = await items.count()   

        # print(f"\n\n{count}\n\n")

        # Loop through all items
        for i in range(count):
            item = items.nth(i)
            
            if i == 0:  # first content-detail 
                try:
                    # Extract content

                    content_text = await item.inner_text()
                    print(f"{content_text.strip()}")

                except Exception as e:
                    print(f"Error on item {i+1}: {e}")

            else:
                try:
                    # Extract title
                    content = item.locator("p")

                    count_paragraph = await content.count()

                    # print(f"\n\n{count_paragraph}\n\n")

                    for j in range(count_paragraph):
                        paragraph = content.nth(j)

                        paragraph_text = await paragraph.inner_text()
                        print(f"{paragraph_text.strip()}\n")

                except Exception as e:
                    print(f"Error on item {i+1}: {e}")


        await browser.close()

async def crawl_1place_info_wrapper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://csdl.vietnamtourism.gov.vn/dest/?item=1")

        await crawl_title_info(page)
        await crawl_content_info(page)

        await browser.close()


async def crawl_title_info(page, place_entry):
    # Where the title, address... is contained
    await page.wait_for_selector(".cslt-detail")

    # The title is on the first .cslt-detail css class
    items = page.locator(".cslt-detail").first

    # Count the number of items which page.locator gives out
    count = await items.count()     # == 1 because locate only the first item 

    # print(f"{count}")

    # Loop through all items
    for i in range(count):
        item = items.nth(i)
        
        try:
            # Extract title
            title_element = item.locator(".header h4")
            title_text = await title_element.inner_text()

            # Append to dict
            place_entry.update({"title": title_text})

            # print(f"{title_text.strip()}")

            # =======================================================
            # # Extract other info
            # other_info = item.locator("span")
            
            # other_info_count = await other_info.count()

            # for j in range(other_info_count):
            #     other_info_iterator = other_info.nth(j)
            #     info_text = await other_info_iterator.inner_text()

            #     ## Append to dict
            #     ## place_entry.update({f"span{j}": info_text})

            #     print(f"{info_text.strip()}")
            # =======================================================

        except Exception as e:
            print(f"Error on item {i}: {e}")

async def crawl_content_info(page, place_entry):

    # The full text to store descriptions, split by "|||"
    paragraph_content_fulltext = ""

    # load page in the specific class
    await page.wait_for_selector(".content-detail")

    # locate to all class name .content-detail
    items = page.locator(".content-detail")

    # Count the number of class named .content-detail
    count = await items.count()   

    # print(f"\n\n{count}\n\n")

    # Loop through all items
    for i in range(count):
        item = items.nth(i)
        
        if i == 0:  # first content-detail 
            try:
                # Extract content
                content_text = await item.inner_text()

                # Append to dict
                # place_entry.update({f"content{i}": content_text})
                paragraph_content_fulltext += content_text

                # print(f"{content_text.strip()}")

            except Exception as e:
                print(f"Error on item {i}: {e}")

        else:
            try:
                # Extract title
                content = item.locator("p")

                count_paragraph = await content.count()

                # print(f"\n\n{count_paragraph}\n\n")

                for j in range(count_paragraph):
                    paragraph = content.nth(j)

                    paragraph_text = await paragraph.inner_text()

                    # Append to dict
                    # place_entry.update({f"content{i}{j}": paragraph_text})
                    paragraph_content_fulltext += "|||" + paragraph_text


                    # print(f"{paragraph_text.strip()}\n")

            except Exception as e:
                print(f"Error on item {i}: {e}")

    # Append to dict
    place_entry.update({"description": paragraph_content_fulltext})

    

async def crawl_1place_info(page, place_entry):
    await crawl_title_info(page, place_entry)
    await crawl_content_info(page, place_entry)


async def crawl_all_places_info():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        all_place = []
        place_entry_i = 1

        for current_page in range(START_PAGE, START_PAGE + MAX_PAGES):
            print(f"Crawling page {current_page}...")
            
            # Construct the URL with pagination
            target_url = f"{BASE_URL}?item={current_page}"
            
            try:
                # Simple parsing (refine this with specific selectors like .title, .address)
                place_entry = {'id': place_entry_i}

                # Go to page and wait for the list to load
                await page.goto(target_url, timeout=60000)

                await crawl_1place_info(page, place_entry)

                all_place.append(place_entry)
                place_entry = {}
                place_entry_i += 1


            except Exception as e:
                print(f"Error on page {current_page}: {e}")

        await browser.close()

        
        print(all_place)
        
        # Save to Excel/CSV
        df = pd.DataFrame(all_place)
        df.to_csv("vietnam_tourism_data.csv", index=False)
        print(f"Done! Scraped {len(all_place)} items.")

        



# Run the script
if __name__ == "__main__":
    
    asyncio.run(crawl_all_places_info())
    # asyncio.run(crawl_1place_info_wrapper())

    # asyncio.run(crawl_content_info())
    # asyncio.run(crawl_content_info())
    # asyncio.run(crawl_title_info())
    # asyncio.run(crawl_title())                # ban nay ngon
    # asyncio.run(crawl_first_container_only())
    # asyncio.run(crawl_titles2())
    # asyncio.run(crawl_titles())

    # asyncio.run(crawl_specific_section())
    # asyncio.run(scrape_tourism_data())