import streamlit as st

# Initialize session state for button click status
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# App title
st.title("Button State Change Demo")

# Create the button with conditional text and behavior
if not st.session_state.button_clicked:
    # Button before being clicked
    if st.button("🔴 Click Me!", key="main_button", type="primary"):
        st.session_state.button_clicked = True
        st.rerun()  # Rerun to update the UI immediately
else:
    # Button after being clicked - show different appearance
    if st.button("✅ Clicked!", key="clicked_button", type="secondary"):
        # Optional: Reset the button state when clicked again
        st.session_state.button_clicked = False
        st.rerun()

# Display current status
if st.session_state.button_clicked:
    st.success("Button has been clicked! 🎉")
    st.info("Click the button again to reset it.")
else:
    st.info("Button is ready to be clicked.")

# Optional: Add a separate reset button
st.divider()
if st.button("Reset Button State", type="secondary"):
    st.session_state.button_clicked = False
    st.rerun()