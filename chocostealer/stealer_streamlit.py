import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="🎪 Pukkelpop Ticket Monitor",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
URL_TEMPLATE = "https://tickets.pukkelpop.be/nl/meetup/demand/?type={day}&camping={camping}&price=all"

days = {
    "day1": "Friday",
    "day2": "Saturday", 
    "day3": "Sunday",
    "combi": "Combi"
}

campings = {
    "n": "No Camping",
    "a": "Camping Chill",
    "b": "Camping Relax"
}

def extract_price_value(price_text):
    """Extract numeric value from price text for sorting"""
    price_match = re.search(r'€?\s*(\d+(?:\.\d{2})?)', price_text)
    if price_match:
        return float(price_match.group(1))
    return float('inf')  # If no price found, put it at the end

def get_tickets_for_combination(day, camping):
    """Get available tickets for a specific day/camping combination"""
    try:
        url = URL_TEMPLATE.format(day=day, camping=camping)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        link_elements = soup.find_all('a', href=re.compile(r"^https://tickets\.pukkelpop\.be/nl/meetup/buy/"))
        
        if not link_elements:
            return {
                'day': days[day],
                'camping': campings[camping],
                'count': 0,
                'lowest_price': 'N/A',
                'url': url,
                'status': 'No tickets available'
            }
        
        # Extract all prices and find the lowest
        prices = []
        for link_element in link_elements:
            price_text = link_element.get_text(strip=True)
            prices.append(price_text)
        
        # Find lowest price
        lowest_price = min(prices, key=extract_price_value) if prices else 'N/A'
        
        return {
            'day': days[day],
            'camping': campings[camping],
            'count': len(link_elements),
            'lowest_price': lowest_price,
            'url': url,
            'status': f'{len(link_elements)} tickets available'
        }
        
    except requests.RequestException as e:
        return {
            'day': days[day],
            'camping': campings[camping],
            'count': 0,
            'lowest_price': 'N/A',
            'url': url,
            'status': f'Error: {str(e)}'
        }
    except Exception as e:
        return {
            'day': days[day],
            'camping': campings[camping],
            'count': 0,
            'lowest_price': 'N/A',
            'url': url,
            'status': f'Error: {str(e)}'
        }

@st.cache_data(ttl=60)  # Cache for 1 minute to avoid too frequent requests
def fetch_all_tickets():
    """Fetch ticket availability for all combinations"""
    all_tickets = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_combinations = len(days) * len(campings)
    current = 0
    
    for day in days.keys():
        for camping in campings.keys():
            current += 1
            progress = current / total_combinations
            progress_bar.progress(progress)
            status_text.text(f'Checking {days[day]} - {campings[camping]}...')
            
            ticket_info = get_tickets_for_combination(day, camping)
            all_tickets.append(ticket_info)
            
            # Small delay to be respectful to the server
            time.sleep(0.5)
    
    progress_bar.empty()
    status_text.empty()
    
    return all_tickets

def main():
    # Title and header
    st.title("🎪 Pukkelpop Ticket Monitor")
    st.markdown("Real-time ticket availability checker")
    
    # Last updated info
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"Last checked: {current_time}")
    
    # User selection filters (flat line)
    st.markdown("### 🎯 Select what you're interested in:")

    selected_days = {day_key: True for day_key in days}
    selected_campings = {camping_key: True for camping_key in campings}

    # Create checkboxes for days
    cols = st.columns(max(len(days), len(campings)) +1)
    cols[0].markdown("**Days:**")
    for i, (day_key, day_name) in enumerate(days.items()):
        selected_days[day_key] = cols[i+1].checkbox(day_name, value=(day_key != "day3"), key=f"day_{day_key}")
    
    # Create checkboxes for campings
    cols = st.columns(max(len(days), len(campings)) +1)
    cols[0].markdown("**Campings:**")
    for i, (camping_key, camping_name) in enumerate(campings.items()):
        selected_campings[camping_key] = cols[i+1].checkbox(camping_name, value=True, key=f"camping_{camping_key}")
    
    # Control buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("🔄 Refresh Now", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
    with col3:
        if st.button("Select All"):
            for day_key in days.keys():
                st.session_state[f"day_{day_key}"] = True
            for camping_key in campings.keys():
                st.session_state[f"camping_{camping_key}"] = True
            st.rerun()
    
    st.markdown("---")
    
    # Fetch ticket data only for selected combinations
    selected_combinations = []
    for day_key, day_selected in selected_days.items():
        for camping_key, camping_selected in selected_campings.items():
            if day_selected and camping_selected:
                selected_combinations.append((day_key, camping_key))
    
    if not selected_combinations:
        st.warning("⚠️ Please select at least one day and one camping option to monitor.")
        return
    
    with st.spinner("Checking ticket availability..."):
        tickets_data = []
        
        if selected_combinations:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_combinations = len(selected_combinations)
            current = 0
            
            for day_key, camping_key in selected_combinations:
                current += 1
                progress = current / total_combinations
                progress_bar.progress(progress)
                status_text.text(f'Checking {days[day_key]} - {campings[camping_key]}...')
                
                ticket_info = get_tickets_for_combination(day_key, camping_key)
                tickets_data.append(ticket_info)
                
                # Small delay to be respectful to the server
                time.sleep(0.5)
            
            progress_bar.empty()
            status_text.empty()
    
    # Create DataFrame for better display
    df = pd.DataFrame(tickets_data)
    
    # Separate available and unavailable tickets
    available_tickets = df[df['count'] > 0].copy()
    unavailable_tickets = df[df['count'] == 0].copy()
    
    # Display available tickets
    if not available_tickets.empty:
        st.success(f"🎉 {len(available_tickets)} ticket types currently available!")
        
        # Sort by count (descending) then by price
        available_tickets['price_numeric'] = available_tickets['lowest_price'].apply(
            lambda x: extract_price_value(x) if x != 'N/A' else float('inf')
        )
        available_tickets = available_tickets.sort_values(['count', 'price_numeric'], ascending=[False, True])
        
        # Display available tickets in a nice format
        for _, ticket in available_tickets.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 2])
                
                with col1:
                    st.markdown(f"**{ticket['day']}**")
                
                with col2:
                    st.markdown(f"**{ticket['camping']}**")
                
                with col3:
                    st.markdown(f"<span style='color: green; font-weight: bold;'>{ticket['count']} tickets</span>", 
                              unsafe_allow_html=True)
                
                with col4:
                    if ticket['lowest_price'] != 'N/A':
                        st.markdown(f"**From {ticket['lowest_price']}**")
                    else:
                        st.markdown("**Price: N/A**")
                
                with col5:
                    st.link_button("🎫 View Tickets", ticket['url'])
                
                st.markdown("---")
    
    else:
        st.warning("😔 No tickets currently available")
    
    # Show summary table
    st.markdown("## 📊 Complete Overview")
    
    # Prepare display DataFrame - remove status column
    display_df = df[['day', 'camping', 'count', 'lowest_price']].copy()
    display_df.columns = ['Day', 'Camping', 'Available', 'Lowest Price']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Add some helpful information
    st.markdown("---")
    st.markdown("### ℹ️ How to use")
    st.markdown("""
    - **Available tickets are highlighted in green** - click "View Tickets" to purchase
    - **Refresh the page** or click the refresh button to check for new tickets
    - **Enable auto-refresh** to automatically check every 30 seconds
    - Data is cached for 60 seconds to avoid overwhelming the server
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("*This tool monitors ticket availability on the official Pukkelpop website*")

if __name__ == "__main__":
    main()