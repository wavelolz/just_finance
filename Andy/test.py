import streamlit as st

# Initialize the counter in session state if it does not exist
if 'button_click_count' not in st.session_state:
    st.session_state.button_click_count = 0

# Function to increment the counter
def increment_counter():
    st.session_state.button_click_count += 1

# Display the button and associate it with the increment function
if st.button('Click me!'):
    increment_counter()

# Display the current count
st.write(f"Button clicked {st.session_state.button_click_count} times.")
