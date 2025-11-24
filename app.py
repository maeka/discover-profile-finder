import base64
import requests
import streamlit as st

# ------------------------------
# Helper: Encode MID into Discover Profile hash
# ------------------------------
def encode_mid_to_discover_url(mid: str) -> str:
    # Original format comes as "kg:/m/xxxx" or "kg:/g/xxxx"
    if mid.startswith("kg:"):
        mid = mid[3:]  # Remove 'kg:' prefix (keep "/m/..." or "/g/...")
    mid_bytes = mid.encode("utf-8")
    prefix = bytes([0x0A, len(mid_bytes)])
    payload = prefix + mid_bytes
    encoded = base64.urlsafe_b64encode(payload).decode("utf-8")
    return f"https://profile.google.com/cp/{encoded}"


# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="Google Discover Profile Finder", page_icon="🔎")

st.title("🔎 Google Discover Profile Finder")
st.write(
    """
This tool uses the **Google Knowledge Graph Search API** to find entities and  
try to derive a possible **Google Discover Profile URL** from the entity MID.
"""
)

# Inputs
api_key = st.text_input("Google API Key", type="password", help="Your Google Knowledge Graph Search API key.")
entity_name = st.text_input("Entity name or brand", value="semrush")

limit = st.slider("Number of results to fetch", min_value=1, max_value=10, value=5, step=1)

if st.button("Search"):
    if not api_key:
        st.error("Please provide your Google API key.")
    elif not entity_name.strip():
        st.error("Please provide an entity name.")
    else:
        # ------------------------------
        # Step 2: Query Google Knowledge Graph API
        # ------------------------------
        kgsearch_url = "https://kgsearch.googleapis.com/v1/entities:search"
        params = {
            "query": entity_name,
            "limit": limit,
            "indent": True,
            "key": api_key,
        }

        with st.spinner("Querying Google Knowledge Graph API..."):
            try:
                response = requests.get(kgsearch_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Error while calling the API: {e}")
                st.stop()

        # ------------------------------
        # Step 3: Parse and display results
        # ------------------------------
        items = data.get("itemListElement", [])

        if not items:
            st.warning("❌ No results found for this entity.")
        else:
            st.success(f"Found {len(items)} result(s).")

            for idx, item in enumerate(items, start=1):
                result = item.get("result", {})
                name = result.get("name", "-")
                description = result.get("description", "-")
                mid = result.get("@id", "-")
                url = result.get("url", "(no site)")

                with st.expander(f"Result #{idx}: {name}", expanded=True if idx == 1 else False):
                    st.markdown(f"**Name:** {name}")
                    st.markdown(f"**Description:** {description}")
                    st.markdown(f"**MID:** `{mid}`")
                    st.markdown(f"**Website:** {url if url != '(no site)' else '—'}")

                    # Attempt Discover Profile encoding
                    discover_profile_url = None
                    if isinstance(mid, str) and (mid.startswith("kg:/m/") or mid.startswith("kg:/g/")):
                        try:
                            discover_profile_url = encode_mid_to_discover_url(mid)
                            st.markdown(
                                f"✅ **Possible Discover Profile URL:** "
                                f"[{discover_profile_url}]({discover_profile_url})"
                            )
                        except Exception as e:
                            st.warning(f"Could not encode MID to Discover URL: {e}")
                    else:
                        st.info("⚠️ MID does not match expected `/m/` or `/g/` format.")

                    # Optional: show raw result JSON
                    with st.expander("Show raw JSON result"):
                        st.json(result)

# Optional footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit and the Google Knowledge Graph Search API.")
