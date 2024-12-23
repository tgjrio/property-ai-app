import streamlit as st
import requests
import logging
from PIL import Image, ImageOps
from io import BytesIO
import json

# Streamlit app layout setup
st.set_page_config(page_title="Property AI", layout="wide")

# Load available cities from JSON file
with open("availableCities.json", "r") as file:
    available_cities = json.load(file)

# Combine cities and states into a single list with "City, State" format
city_state_options = [
    f"{city['city']}, {city['state']}"
    for city in available_cities
    if city["city"] and city["state"]
]

# Sidebar dropdown for selecting a city-state pair
selected_city_state = st.sidebar.selectbox(
    "View available cities to query", options=sorted(city_state_options)
)

# Sidebar with chat input
st.sidebar.title("Property AI Chat")

# Spacer to push chat input to the bottom
st.sidebar.write("")  # Adds a small space

user_input = st.sidebar.chat_input("Ask something about properties...")

# Initialize session state for all required keys
if "last_user_input" not in st.session_state:
    st.session_state["last_user_input"] = ""
if "properties_fetched" not in st.session_state:
    st.session_state["properties_fetched"] = False
if "properties" not in st.session_state:
    st.session_state["properties"] = []
if "summary" not in st.session_state:
    st.session_state["summary"] = ""
if "zipcodes" not in st.session_state:
    st.session_state["zipcodes"] = []
if "hometypes" not in st.session_state:
    st.session_state["hometypes"] = []
if "price_range" not in st.session_state:
    st.session_state["price_range"] = (0, 2000000)
if "all_zipcodes_selected" not in st.session_state:
    st.session_state["all_zipcodes_selected"] = True

# Check if new input is detected
if user_input and user_input != st.session_state["last_user_input"]:
    # Reset relevant states
    st.session_state["properties"] = []
    st.session_state["summary"] = ""
    st.session_state["zipcodes"] = []
    st.session_state["hometypes"] = []
    st.session_state["price_range"] = (0, 2000000)
    st.session_state["properties_fetched"] = False

    # Update the last user input
    st.session_state["last_user_input"] = user_input

# Placeholder for filters and properties
filters_placeholder = st.container()
property_placeholder = st.container()
summary_placeholder = st.sidebar.container()

# Fetch data if user input exists and data hasn't been fetched
if user_input and not st.session_state["properties_fetched"]:
    st.sidebar.write(f"You asked: {user_input}")
    try:
        # Send request to the FastAPI endpoint
        response = requests.post("https://property-ai-service-288104261568.us-central1.run.app/process_request/", json={"user_input": user_input})
        response_data = response.json()

        # Handle response data
        if response_data.get("status") == "error":
            error_message = response_data.get("message", "An error occurred. Please try again.")
            st.sidebar.error(error_message)
        else:
            # Save response data to session state
            st.session_state["properties"] = response_data.get("properties", [])
            st.session_state["summary"] = response_data.get("summary", "No summary available.")

            # Extract zipcodes, home types, and price range
            properties = st.session_state["properties"]
            prices = [p['document'].get('price', 0) for p in properties if p['document'].get('price', 0) > 0]
            st.session_state["price_range"] = (min(prices), max(prices)) if prices else (0, 2000000)
            st.session_state["zipcodes"] = sorted({p['document'].get('zipcode', "Unknown Zipcode") for p in properties})
            st.session_state["hometypes"] = sorted({p['document'].get('hometype', "Unknown Type") for p in properties})
            st.session_state["properties_fetched"] = True
    except requests.exceptions.RequestException as e:
        st.sidebar.error("Error: Could not connect to the server.")
        st.sidebar.write(str(e))

# Retrieve data from session state
properties = st.session_state["properties"]
summary = st.session_state["summary"]
zipcodes = st.session_state["zipcodes"]
price_range_min, price_range_max = st.session_state["price_range"]
hometypes = st.session_state["hometypes"]


# Conditionally display filters if properties are available
if properties:
    with filters_placeholder:
        st.write("### Filters")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 2])  # Adjust column ratios as needed

        with col1:
            # Price range slider
            price_range = st.slider(
                "Price Range",
                min_value=price_range_min,
                max_value=price_range_max,
                value=(price_range_min, price_range_max),
                step=10000,
            )

        with col3:
            # Sort by Ascending or Descending
            sort_order = st.radio("Sort by Price", ["Ascending", "Descending"], index=0)

        with col4:
            # Home Type filter
            selected_hometypes = st.multiselect("Home Types", options=hometypes, default=hometypes)

        # Select All Checkbox and Multiselect for Zipcodes
        select_all = st.checkbox("Select All Zipcodes", value=st.session_state["all_zipcodes_selected"])
        if select_all:
            selected_zipcodes = zipcodes
            st.session_state["all_zipcodes_selected"] = True
        else:
            selected_zipcodes = st.multiselect("Select Zipcodes", options=zipcodes, default=zipcodes)
            st.session_state["all_zipcodes_selected"] = False

    # Filter and optionally sort properties based on filters
    filtered_properties = []
    for property_data in properties:
        document = property_data.get("document", {})
        price = document.get("price", 0)
        zipcode = document.get("zipcode", "Unknown Zipcode")
        hometype = document.get("hometype", "Unknown Type")

        # Check if property matches the selected filters
        if (
            price_range[0] <= price <= price_range[1]
            and (zipcode in selected_zipcodes)
            and (hometype in selected_hometypes)
        ):
            filtered_properties.append(property_data)

    # Sort properties by price
    reverse_sort = sort_order == "Descending"
    filtered_properties = sorted(filtered_properties, key=lambda x: x['document'].get('price', 0), reverse=reverse_sort)
else:
    filtered_properties = []

# Standardized dimensions
TARGET_WIDTH = 300
TARGET_HEIGHT = 200

def resize_image(image, width, height):
    """
    Resize the image while maintaining aspect ratio and filling the area.
    """
    return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)

query_message = st.session_state.get("query_message", "")

# Display query message (success or no results)
if query_message:
    st.markdown(f"### {query_message}")

# Display filtered properties
with property_placeholder:
    if properties:
        st.write("### Properties Available")
        if filtered_properties:
            cols = st.columns(3)  # Create 3 columns
            for i, property_data in enumerate(filtered_properties):
                col = cols[i % 3]  # Cycle through columns
                with col:
                    # Get document details with defaults
                    document = property_data.get("document", {})
                    img_src = document.get("imgSrc", None)
                    if not img_src:
                        img_src = "https://via.placeholder.com/150"
                    street_address = document.get("streetaddress", "Unknown Address")
                    city = document.get("city", "Unknown City")
                    state = document.get("state", "Unknown State")
                    zipcode = document.get("zipcode", "Unknown Zipcode")
                    price = document.get("price", "N/A")
                    bedrooms = document.get("bedrooms", "N/A")
                    bathrooms = document.get("bathrooms", "N/A")
                    home_type = document.get("hometype", "N/A")
                    url = document.get("url", "#")

                    # Render the property tile
                    st.markdown('<div class="property-tile">', unsafe_allow_html=True)

                    if img_src:
                        try:
                            response = requests.get(img_src, timeout=10)
                            response.raise_for_status()  # Verify the request was successful
                            image = Image.open(BytesIO(response.content))
                            resized_image = resize_image(image, TARGET_WIDTH, TARGET_HEIGHT)
                            st.image(resized_image, use_container_width=False)
                        except Exception as e:
                            st.warning("Could not load image.")
                            logging.error(f"Error fetching image: {e}")
                    else:
                        st.warning("Image URL not available.")

                    # Display property details
                    st.write(f"**{street_address}**")
                    st.write(f"{city}, {state} {zipcode}")
                    st.write(f"Price: ${price}")
                    st.write(f"Bedrooms: {bedrooms}, Bathrooms: {bathrooms}")
                    st.write(f"Type: {home_type}")
                    st.write(f"[View on Zillow]({url})")

                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("No properties match the selected filters.")
    else:
        st.markdown(
        """
        ## Welcome to **Property AI** 👋
        Thank you for checking out this prototype application! My goal is to help users understand how they can talk to their data and this 
        application is a great example of how you can use natural language to query Zillow data. Use this tool to explore real estate properties by providing specific queries. 
        
        Here's how to get started:

        ### What To Expect:
        🏠 **List of Properties**: You will get a list of properties that match the criteria of your search. This is Zillow data so you'll get a link to the property as well.
        📊 **Generated Insights**: A generated sumamry of all the properties that are in your list and some calculations like price average.


        ### How to Request:
        ✅ Write natural language queries and be specific and include details like:
          - **Location** (e.g., city, state, ZIP and/or county).
          - **Property Type** (e.g., single family, lot, multi-family etc).
          - **Status** (e.g., For sale or sold).
          - **Price** (e.g., *under/over or equal to $500,000*).
          - **Property Features** (e.g., bedrooms, bathrooms).

        ### Examples of Valid Queries:
        - *"Show me homes with 4 bedrooms in Los Angeles."*
        - *"What are the properties listed in Miami for $400,000?"*
        - *"Find properties with 2 bathrooms in Chicago under $300,000."*

        ### What This App Cannot Do:
        ❌  Compare properties or provide investor-specific analyses or answer non-real estate-related questions.

        ### Data Availability:
        - *Since this is a prototype, the data is limited to a small set of properties so you may not find all locations or prices if you search using a date.*
        - *The data is also static and does not update in real-time.*
        - *Images are fetched from the API I used and may not be available for all properties.*
        - *Data is automatically maxed out at 21 so you may not get all the results if you search for a large set of properties.*
        ---
        Start exploring by typing your request in the sidebar! 🚀
        """,
        unsafe_allow_html=True
    )

# Display property summary
with summary_placeholder:
    if summary:
        st.write("### Summary")
        st.markdown(summary, unsafe_allow_html=True)